import json
import os
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
URLS = {
    "645": "https://raw.githubusercontent.com/vietvudanh/vietlott-data/main/data/power645.jsonl",
    "655": "https://raw.githubusercontent.com/vietvudanh/vietlott-data/main/data/power655.jsonl",
}


def sync_vietlott_data() -> dict:
    """Tải và đồng bộ dữ liệu lịch sử Mega 6/45 và Power 6/55 mới nhất từ vietvudanh/vietlott-data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}

    for game_code, url in URLS.items():
        file_path = DATA_DIR / f"power{game_code}.jsonl"
        req = urllib.request.Request(url, headers={"User-Agent": "VietlottQuantAuto/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8").strip()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

        lines = [line for line in content.splitlines() if line.strip()]
        last_record = json.loads(lines[-1]) if lines else {}
        summary[game_code] = {
            "total_draws": len(lines),
            "latest_id": last_record.get("id"),
            "latest_date": last_record.get("date"),
            "latest_result": last_record.get("result"),
            "path": str(file_path),
        }

    return summary


def load_draws(game_code: str) -> list[dict]:
    """Đọc danh sách các kỳ quay từ file jsonl cục bộ."""
    file_path = DATA_DIR / f"power{game_code}.jsonl"
    if not file_path.exists():
        sync_vietlott_data()

    draws = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            res = record.get("result", [])
            if game_code == "655" and len(res) >= 6:
                main_balls = sorted(int(x) for x in res[:6])
                bonus_ball = int(res[6]) if len(res) > 6 else None
            else:
                main_balls = sorted(int(x) for x in res[:6])
                bonus_ball = None
            draws.append({
                "id": record.get("id"),
                "date": record.get("date"),
                "main": main_balls,
                "bonus": bonus_ball,
            })
    return draws


if __name__ == "__main__":
    info = sync_vietlott_data()
    for code, meta in info.items():
        name = "Mega 6/45" if code == "645" else "Power 6/55"
        print(
            f"[{name}] Đã đồng bộ {meta['total_draws']} kỳ quay | "
            f"Kỳ mới nhất: #{meta['latest_id']} ({meta['latest_date']}) -> {meta['latest_result']}"
        )

