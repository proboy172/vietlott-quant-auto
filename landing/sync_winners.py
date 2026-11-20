"""Đồng bộ ảnh/khoảnh khắc chủ nhân Jackpot từ trang chính thức Vietlott.

Nguồn: https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/chu-nhan-jackpot
Ảnh: https://media.vietlott.vn/... (do Vietlott công bố công khai)

Chạy:
    python landing/sync_winners.py

Kết quả: ghi landing/winners.js (window.VIETLOTT_WINNERS) để landing hiển thị
khoảnh khắc thật, có ghi nguồn. Chạy lại định kỳ để đồng bộ 1:1.
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
OUT_FILE = BASE_DIR / "winners.js"
URL = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/chu-nhan-jackpot"

PAT = re.compile(
    r'!\[]\((https://media\.vietlott\.vn/[^)]+)\)\s*\n\s*\n([^\n]+)\n\s*\n####\s*([^\n]+)\n\s*\n([^\n]+)\n\s*\n#####\s*([^\n]+)',
    re.M,
)


def fetch_markdown(url: str) -> str:
    # Trang trả nội dung đọc được qua fetch thông thường; parse HTML->text nhẹ bằng cách
    # bóc các khối ảnh/tên/giá trị trực tiếp từ HTML (ổn định hơn markdown render).
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_items(html: str) -> list[dict]:
    # Cấu trúc HTML lặp: <img src="..."> ... <div>Ông/Tên</div> ... <div>xx.xxx</div> VNĐ ... <div>Mega/Power</div>
    # Nhưng để bền, parse theo cặp media.vietlott.vn + khối text gần đó.
    items: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    # Bóc từng "card" xung quanh ảnh winner.avatar
    for m in re.finditer(
        r'<img[^>]+src="(https://media\.vietlott\.vn/[^"]*winner\.avatar[^"]*)"[^>]*>(.*?)</(?:div|li|section)>\s*</(?:div|li|section)>',
        html,
        re.S | re.I,
    ):
        url = m.group(1).strip()
        block = m.group(2)
        text = re.sub(r'<[^>]+>', '\n', block)
        lines = [re.sub(r'\s+', ' ', ln).strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        # kỳ vọng: tên, số tiền, VNĐ, game (thứ tự có thể lệch) -> tìm theo pattern
        name = next((ln for ln in lines if re.search(r'(Ông|Bà|Anh|Chị|Cô|Nguyễn|Phan|Trần)', ln, re.I)), '')
        amount = next((ln for ln in lines if re.search(r'^\d[\d\.]+$', ln)), '')
        game = next((ln for ln in lines if 'Mega 6/45' in ln or 'Power 6/55' in ln), '')
        if not (name and amount and game):
            continue
        key = (url, name, amount, game)
        if key in seen:
            continue
        seen.add(key)
        items.append({"url": url, "name": name, "amount": amount, "game": game})

    if items:
        return items

    # Fallback: quét toàn trang theo chuỗi liên tiếp (ít phụ thuộc cấu trúc thẻ)
    # Tìm tất cả URL ảnh winner rồi lấy các nhãn gần nhất phía sau trong plain text
    plain = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', html, flags=re.I)
    plain = re.sub(r'<[^>]+>', '\n', plain)
    plain = html  # giữ url trong thuộc tính
    # fallback 2: regex trên chuỗi gốc với text đã strip tag quanh
    for m in re.finditer(r'src="(https://media\.vietlott\.vn/[^"]*winner\.avatar[^"]*)"', html, re.I):
        url = m.group(1).strip()
        # lấy 600 ký tự sau ảnh
        tail = html[m.end(): m.end() + 1200]
        tail = re.sub(r'<[^>]+>', '\n', tail)
        lines = [re.sub(r'\s+', ' ', ln).strip() for ln in tail.splitlines()]
        lines = [ln for ln in lines if ln]
        name = next((ln for ln in lines if re.search(r'(Ông|Bà|Anh|Chị|Cô|Nguyễn|Phan|Trần)', ln, re.I) and len(ln) < 40), '')
        amount = next((ln for ln in lines if re.search(r'^\d[\d\.]{6,}$', ln)), '')
        game = next((ln for ln in lines if ln in ('Mega 6/45', 'Power 6/55')), '')
        if not (name and amount and game):
            continue
        key = (url, name, amount, game)
        if key in seen:
            continue
        seen.add(key)
        items.append({"url": url, "name": name, "amount": amount, "game": game})
    return items


def main() -> int:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    try:
        html = fetch_markdown(URL)
        items = parse_items(html)
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] Lỗi tải/parse {URL}: {exc}")
        return 1
    if not items:
        print("[ERROR] Không bóc được mục nào. Giữ nguyên winners.js cũ.")
        return 1

    payload = {
        "source": "vietlott.vn",
        "sourceUrl": URL,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(items),
        "items": items,
    }
    content = (
        "/* AUTO-GENERATED bởi landing/sync_winners.py — không sửa tay.\n"
        " * Nguồn: trang Chủ nhân Jackpot Vietlott (ảnh/khoảnh khắc công khai).\n"
        " */\n"
        "window.VIETLOTT_WINNERS = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n"
    )
    OUT_FILE.write_text(content, encoding="utf-8")
    print(f"[OK] {len(items)} khoảnh khắc -> {OUT_FILE}")
    for it in items[:3]:
        print(f"  - {it['game']} | {it['name']} | {it['amount']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
