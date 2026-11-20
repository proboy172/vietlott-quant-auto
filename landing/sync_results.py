"""Đồng bộ kết quả Vietlott mới nhất vào landing.

Nguồn chính: trang kết quả công khai của Vietlott (vietlott.vn).
Lịch sử bổ sung: các file data/power645.jsonl và data/power655.jsonl trong repo.

Chạy:
    python landing/sync_results.py

Kết quả: ghi đè landing/draws.js để landing hiển thị kết quả thật, không cần build.
Có thể chạy lại mỗi ngày (hoặc thêm vào pipeline/GitHub Actions) để đồng bộ 1:1.
"""

from __future__ import annotations

import io
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
DATA_DIR = REPO_DIR / "data"
OUT_FILE = BASE_DIR / "draws.js"

OFFICIAL_URLS = {
    "645": "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/645",
    "655": "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/655",
}
GAME_NAMES = {"645": "Mega 6/45", "655": "Power 6/55"}


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_official(html: str, game: str) -> dict | None:
    """Bóc kỳ, ngày, bộ số và jackpot từ trang kết quả chính thức."""
    draw = re.search(
        r"Kỳ quay thưởng\s*<b>#(\d+)</b>\s*ngày\s*<b>([^<]+)</b>",
        html,
        re.S,
    )
    if not draw:
        return None

    block = re.search(r'day_so_ket_qua_v2[^>]*>(.*?)</div>', html, re.S)
    if not block:
        return None
    numbers = re.findall(r'<span class="bong_tron[^"]*"[^>]*>(\d{1,2})</span>', block.group(1))
    if len(numbers) < 6:
        return None

    special = None
    if game == "655" and len(numbers) >= 7:
        special = int(numbers[6])

    jackpot = None
    money = re.search(
        r"Giá trị Jackpot(?:\s*1)?[^<]*</h5>.*?<h3>([\d.]+)</h3>",
        html,
        re.S,
    )
    if not money:
        money = re.search(r"Giá trị Jackpot[^<]*</h5>.*?<h3>([\d.]+)</h3>", html, re.S)
    if money:
        jackpot = int(money.group(1).replace(".", ""))

    date_text = draw.group(2).strip()
    try:
        sort_key = datetime.strptime(date_text, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        sort_key = date_text

    return {
        "game": game,
        "name": GAME_NAMES[game],
        "id": draw.group(1),
        "date": date_text,
        "numbers": [int(x) for x in numbers[:6]],
        "special": special,
        "jackpot": jackpot,
        "_sort": sort_key,
    }


def parse_history_file(game: str) -> list[dict]:
    path = DATA_DIR / f"power{game}.jsonl"
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        result = record.get("result") or []
        if not isinstance(result, list) or len(result) < 6:
            continue
        numbers = [int(x) for x in result[:6]]
        special = int(result[6]) if game == "655" and len(result) > 6 else None
        raw_date = str(record.get("date", ""))
        try:
            date_text = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            sort_key = raw_date
        except ValueError:
            date_text = raw_date
            sort_key = raw_date
        rows.append(
            {
                "game": game,
                "name": GAME_NAMES[game],
                "id": str(record.get("id", "")),
                "date": date_text,
                "numbers": numbers,
                "special": special,
                "_sort": sort_key,
            }
        )
    return rows


def format_jackpot(value: int | None) -> str | None:
    if not value:
        return None
    billion = value / 1_000_000_000
    text = f"{billion:.2f}".replace(".", ",")
    return f"{text} tỷ"


def main() -> int:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    official: list[dict] = []
    for game, url in OFFICIAL_URLS.items():
        try:
            page = fetch_html(url)
            parsed = parse_official(page, game)
            if parsed:
                official.append(parsed)
                print(f"[OK] {parsed['name']} kỳ #{parsed['id']} ngày {parsed['date']}: {parsed['numbers']}" + (f" | {parsed['special']}" if parsed["special"] is not None else ""))
            else:
                print(f"[WARN] Không bóc được kết quả {game} từ Vietlott")
        except Exception as exc:  # pragma: no cover - network dependent
            print(f"[WARN] Lỗi tải {url}: {exc}")

    if not official:
        print("[ERROR] Không có dữ liệu chính thức. Giữ nguyên draws.js cũ.")
        return 1

    history: list[dict] = []
    for game in OFFICIAL_URLS:
        history.extend(parse_history_file(game))

    # Gộp, ưu tiên dữ liệu chính thức, bỏ trùng theo (game, id).
    merged: dict[tuple[str, str], dict] = {}
    for item in history:
        merged[(item["game"], item["id"])] = item
    for item in official:
        merged[(item["game"], item["id"])] = item

    rows = list(merged.values())
    rows.sort(key=lambda r: (r.get("_sort") or "", r["id"]), reverse=True)

    latest = max(official, key=lambda r: r.get("_sort") or "")
    latest = dict(latest)
    latest["jackpotText"] = format_jackpot(latest.get("jackpot"))

    # Bảng kết quả chính là kết quả mới nhất; lịch sử lấy 6 kỳ gần nhất còn lại.
    recent = [
        {k: v for k, v in row.items() if not k.startswith("_")}
        for row in rows
        if not (row["game"] == latest["game"] and row["id"] == latest["id"])
    ][:6]

    payload = {
        "source": "vietlott.vn",
        "sourceUrl": "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/",
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latest": {k: v for k, v in latest.items() if not k.startswith("_")},
        "history": recent,
        "schedule": {
            "645": {"days": [0, 3, 5], "label": "Thứ 4 · Thứ 6 · Chủ nhật"},
            "655": {"days": [2, 4, 6], "label": "Thứ 3 · Thứ 5 · Thứ 7"},
        },
    }

    content = (
        "/* AUTO-GENERATED bởi landing/sync_results.py — không sửa tay.\n"
        " * Nguồn: vietlott.vn + data/power645.jsonl + data/power655.jsonl\n"
        " */\n"
        "window.VIETLOTT_DRAWS = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n"
    )
    OUT_FILE.write_text(content, encoding="utf-8")
    print(f"[OK] Đã ghi {OUT_FILE}")
    print(f"     Mới nhất: {latest['name']} #{latest['id']} · {latest['date']} · jackpot {latest['jackpotText']}")
    print(f"     Lịch sử: {len(recent)} kỳ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
