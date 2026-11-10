import datetime
import json
import re
import urllib.request
from pathlib import Path

from data_sync import sync_vietlott_data
from iphone_automation_server import get_today_game_code
from quant_engine import (
    GAME_CONFIGS,
    analyze_historical_stats,
    generate_1_ticket_optimal,
    generate_3_tickets_abbreviated_wheel,
)

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"


def fetch_live_jackpot_billion(game_code: str) -> float:
    """
    Tự động lấy giá trị Jackpot hiện tại (đơn vị: tỷ VNĐ) từ trang kết quả xổ số.
    Nếu không kết nối được (do mạng hoặc geo-block), trả về mức cơ sở (12 tỷ cho 6/45, 30 tỷ cho 6/55).
    """
    default_jp = 12.0 if game_code == "645" else 30.0
    urls = [
        "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/655"
        if game_code == "655"
        else "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/645",
        "https://atrungroi.com/xo-so-vietlott-power-6-55.html"
        if game_code == "655"
        else "https://atrungroi.com/xo-so-vietlott-mega-6-45.html",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            # Tìm chuỗi số tiền dạng xx.xxx.xxx.xxx (từ 10 tỷ đến 500 tỷ)
            matches = re.findall(r"(\d{1,3}(?:[.,]\d{3}){3})", html)
            candidates = []
            for m in matches:
                clean_num = int(re.sub(r"[.,]", "", m))
                if 10_000_000_000 <= clean_num <= 600_000_000_000:
                    candidates.append(clean_num / 1_000_000_000.0)
            if candidates:
                return round(max(candidates), 2)
        except Exception:
            continue
    return default_jp


def run_daily_cloud_pipeline(force_date: datetime.date = None, override_jackpot: float = None) -> dict:
    """
    Pipeline chạy hoàn toàn tự động mỗi ngày (trên GitHub Actions hoặc Task Scheduler):
    1. Đồng bộ kết quả quay thưởng mới nhất từ vietvudanh/vietlott-data
    2. Xác định hôm nay quay giải nào (Thứ 3,5,7 -> 655 | Thứ 4,6,CN -> 645 | Thứ 2 -> Nghỉ)
    3. Quét giá trị Jackpot thực tế hiện tại để tự quyết định:
       - Mua 1 vé đơn (10.000đ) khi Jackpot < ngưỡng
       - Mua dàn 3 vé Bao 9 rút gọn (30.000đ) khi Jackpot >= ngưỡng
    4. Xuất ra file tĩnh `public/today_sms.txt` để iPhone Shortcuts tự đọc và bắn SMS tới 9969!
    """
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    sync_vietlott_data()

    vn_tz = datetime.timezone(datetime.timedelta(hours=7))
    today = force_date or datetime.datetime.now(vn_tz).date()
    game_code = get_today_game_code(today)

    sms_txt_path = PUBLIC_DIR / "today_sms.txt"
    report_json_path = PUBLIC_DIR / "today_report.json"

    if game_code is None:
        # Thứ Hai không có kỳ quay Mega 6/45 hoặc Power 6/55 -> Ghi file rỗng để iPhone không gửi SMS
        sms_txt_path.write_text("", encoding="utf-8")
        report = {
            "date": str(today),
            "status": "REST_DAY",
            "message": "Thứ Hai không có lịch quay Mega 6/45 và Power 6/55. iPhone tự động nghỉ.",
            "sms_commands": [],
        }
        report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    cfg = GAME_CONFIGS[game_code]
    live_jp = override_jackpot if override_jackpot is not None else fetch_live_jackpot_billion(game_code)
    stats = analyze_historical_stats(game_code)

    is_high_jackpot = live_jp >= cfg.jackpot_high_threshold_billion
    plan = generate_3_tickets_abbreviated_wheel(stats) if is_high_jackpot else generate_1_ticket_optimal(stats)

    # Ghi danh sách lệnh SMS ra today_sms.txt (mỗi dòng 1 tin nhắn gửi 9969)
    sms_content = "\n".join(plan["sms_commands"])
    sms_txt_path.write_text(sms_content, encoding="utf-8")

    report = {
        "date": str(today),
        "status": "ACTIVE_BUY",
        "game_code": game_code,
        "game_name": cfg.name,
        "detected_jackpot_billion": live_jp,
        "high_jackpot_threshold_billion": cfg.jackpot_high_threshold_billion,
        "is_high_jackpot": is_high_jackpot,
        "selected_mode": plan["mode"],
        "total_cost_vnd": len(plan["sms_commands"]) * 10000,
        "sms_commands": plan["sms_commands"],
        "tickets_detail": plan["tickets"],
        "output_sms_file": str(sms_txt_path),
    }
    report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run_daily_cloud_pipeline()
    print(json.dumps(result, ensure_ascii=False, indent=2))

