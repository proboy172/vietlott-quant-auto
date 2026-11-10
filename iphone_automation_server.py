import datetime
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from data_sync import sync_vietlott_data
from quant_engine import (
    GAME_CONFIGS,
    analyze_historical_stats,
    generate_1_ticket_optimal,
    generate_3_tickets_abbreviated_wheel,
)

DB_PATH = Path(__file__).resolve().parent / "data" / "tickets_history.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS purchased_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_date TEXT NOT NULL,
                game_code TEXT NOT NULL,
                mode TEXT NOT NULL,
                sms_syntax TEXT NOT NULL,
                confirmation_sms TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def get_today_game_code(target_date: datetime.date = None) -> str | None:
    """
    Lịch quay thưởng chính thức của Vietlott:
    - Thứ 2 (weekday=0): Nghỉ (không quay Mega 6/45 và Power 6/55)
    - Thứ 3, Thứ 5, Thứ 7 (weekday in 1, 3, 5): Power 6/55 ('655')
    - Thứ 4, Thứ 6, Chủ Nhật (weekday in 2, 4, 6): Mega 6/45 ('645')
    """
    if target_date is None:
        target_date = datetime.date.today()
    wd = target_date.weekday()
    if wd in (1, 3, 5):
        return "655"
    if wd in (2, 4, 6):
        return "645"
    return None


def build_today_ticket_plan(jackpot_billion: float = 0.0, force_mode: str = None, force_game: str = None) -> dict:
    """
    Tự động đồng bộ dữ liệu mới nhất, kiểm tra lịch quay hôm nay,
    so sánh giá trị Jackpot với ngưỡng kích hoạt để xuất ra:
    - 1 vé đơn (khi Jackpot thấp)
    - Dàn 3 vé Bao 9 rút gọn (khi Jackpot vượt ngưỡng cao)
    """
    sync_vietlott_data()
    today = datetime.date.today()
    game_code = force_game or get_today_game_code(today)

    if game_code is None:
        return {
            "status": "REST_DAY",
            "date": str(today),
            "message": "Hôm nay là Thứ Hai (không có kỳ quay Mega 6/45 hoặc Power 6/55).",
            "sms_commands": [],
        }

    stats = analyze_historical_stats(game_code)
    cfg = GAME_CONFIGS[game_code]

    # Quyết định chế độ 1 vé hay 3 vé Bao rút gọn
    if force_mode == "wheel3":
        use_wheel3 = True
    elif force_mode == "single":
        use_wheel3 = False
    else:
        use_wheel3 = jackpot_billion >= cfg.jackpot_high_threshold_billion

    plan = generate_3_tickets_abbreviated_wheel(stats) if use_wheel3 else generate_1_ticket_optimal(stats)

    # Lưu lịch sử sinh vé vào SQLite
    init_db()
    now_iso = datetime.datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as conn:
        for sms_cmd in plan["sms_commands"]:
            conn.execute(
                """
                INSERT INTO purchased_tickets (draw_date, game_code, mode, sms_syntax, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(today), game_code, plan["mode"], sms_cmd, now_iso),
            )

    return {
        "status": "READY",
        "date": str(today),
        "game_code": game_code,
        "game_name": cfg.name,
        "jackpot_billion_input": jackpot_billion,
        "threshold_billion": cfg.jackpot_high_threshold_billion,
        "selected_mode": plan["mode"],
        "tickets": plan["tickets"],
        "sms_commands": plan["sms_commands"],
        "recipient": "9969",
    }


class iPhoneShortcutsHandler(BaseHTTPRequestHandler):
    """
    HTTP Endpoint phục vụ riêng cho ứng dụng Phím tắt (Apple Shortcuts) trên iPhone:
    - GET /today-sms?jackpot=45         -> Trả về JSON chứa danh sách sms_commands gửi 9969
    - GET /today-sms?format=text        -> Trả về từng dòng văn bản thuần (mỗi dòng 1 lệnh SMS)
    - GET /today-sms?mode=wheel3        -> Ép chạy chế độ dàn 3 vé Bao 9 rút gọn
    - POST /webhook-9969                -> Nhận tin nhắn xác nhận từ 9969 do iPhone chuyển tiếp về
    """

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/today-sms":
            self.send_response(404)
            self.end_headers()
            return

        qs = parse_qs(parsed.query)
        jackpot_val = float(qs.get("jackpot", ["0"])[0])
        force_mode = qs.get("mode", [None])[0]
        force_game = qs.get("game", [None])[0]
        fmt = qs.get("format", ["json"])[0]

        result = build_today_ticket_plan(
            jackpot_billion=jackpot_val,
            force_mode=force_mode,
            force_game=force_game,
        )

        if fmt == "text":
            body = "\n".join(result["sms_commands"]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/webhook-9969":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8")
            init_db()
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    """
                    UPDATE purchased_tickets
                    SET confirmation_sms = ?
                    WHERE id = (SELECT MAX(id) FROM purchased_tickets)
                    """,
                    (raw_body,),
                )
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "saved_reply": raw_body}).encode("utf-8"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vietlott Quantitative Auto-Buy Server for iPhone Shortcuts")
    parser.add_argument("--serve", action="store_true", help="Khởi chạy HTTP Server ở cổng 8686 cho iPhone Shortcuts")
    parser.add_argument("--port", type=int, default=8686, help="Cổng HTTP Server (mặc định: 8686)")
    parser.add_argument("--jackpot", type=float, default=0.0, help="Giá trị Jackpot hiện tại (tỷ VNĐ)")
    parser.add_argument("--mode", choices=["single", "wheel3"], default=None, help="Chế độ mua: single (1 vé) hoặc wheel3 (3 vé)")
    parser.add_argument("--game", choices=["645", "655"], default=None, help="Mã sản phẩm: 645 hoặc 655")
    args = parser.parse_args()

    if args.serve:
        print(f"[iPhone Shortcuts Server] Đang lắng nghe tại http://0.0.0.0:{args.port}/today-sms ...")
        server = HTTPServer(("0.0.0.0", args.port), iPhoneShortcutsHandler)
        server.serve_forever()
    else:
        plan = build_today_ticket_plan(jackpot_billion=args.jackpot, force_mode=args.mode, force_game=args.game)
        print(json.dumps(plan, ensure_ascii=False, indent=2))

