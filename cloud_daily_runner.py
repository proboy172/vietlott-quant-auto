import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

# --- repo root on path (safe when run from server/CI) ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_sync import sync_vietlott_data
from iphone_automation_server import get_today_game_code
from quant_engine import (
    GAME_CONFIGS,
    analyze_3d_historical_stats,
    analyze_historical_stats,
    generate_1_ticket_optimal,
    generate_2_tickets_diversity_optimal,
    generate_3_tickets_abbreviated_wheel,
    generate_dynamic_quant_plan,
    generate_max3d_daily_plan,
    generate_max3dpro_daily_plan,
)

# Outputs are PRIVATE (per-day SMS commands have value). Never publish to a public repo/URL.
# Default: out/daily (gitignored). Override with VIETLOTT_OUT_DIR.
OUT_DIR = Path(os.environ.get("VIETLOTT_OUT_DIR", str(BASE_DIR / "out" / "daily")))


def fetch_live_jackpot_billion(game_code: str) -> float:
    """
    Lấy giá trị Jackpot hiện tại (tỷ VNĐ) từ nguồn công khai.
    Nếu không lấy được, trả về mức cơ sở (12 tỷ cho 6/45, 30 tỷ cho 6/55).
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


def run_daily_cloud_pipeline(force_date: datetime.date = None, override_jackpot: float = None,
                             out_dir: str | Path | None = None, write_files: bool = True) -> dict:
    """
    Chạy pipeline hằng ngày (private): đồng bộ dữ liệu, tính toán, sinh lệnh SMS.

    - Kết quả/lệnh SMS là tài sản vận hành: ghi ra thư mục PRIVATE (mặc định out/daily, gitignored)
      hoặc trả về in-memory để server cấp phép phân phối cho thiết bị đã kích hoạt.
    - KHÔNG commit/push lệnh ra repo/file công khai.
    """
    target_out = Path(out_dir) if out_dir else OUT_DIR
    if write_files:
        target_out.mkdir(parents=True, exist_ok=True)

    sync_vietlott_data()

    vn_tz = datetime.timezone(datetime.timedelta(hours=7))
    today = force_date or datetime.datetime.now(vn_tz).date()
    game_code = get_today_game_code(today)

    all_sms_commands = []
    tickets_summary = []
    total_cost_vnd = 0
    decision_notes = []

    if game_code is not None:
        cfg = GAME_CONFIGS[game_code]
        live_jp = override_jackpot if override_jackpot is not None else fetch_live_jackpot_billion(game_code)
        stats = analyze_historical_stats(game_code)

        plan_matrix = generate_dynamic_quant_plan(stats, live_jackpot_billion=live_jp)
        all_sms_commands.extend(plan_matrix.get("sms_commands", []))
        for tk in plan_matrix.get("tickets", []):
            tickets_summary.append({
                "game": cfg.name,
                "detail": tk,
            })
        cost_matrix = len(plan_matrix.get("sms_commands", [])) * 10000
        total_cost_vnd += cost_matrix
        decision_notes.append(f"[{cfg.name}] {plan_matrix.get('decision_reason', '')} (Chi phi: {cost_matrix:,}d)")
    else:
        cfg = None
        live_jp = 0.0

    report = {
        "date": str(today),
        "status": "ACTIVE_BUY" if all_sms_commands else "REST_DAY",
        "primary_matrix_game": cfg.name if cfg else "Nghi quay (Thu 2)",
        "detected_jackpot_billion": live_jp,
        "total_cost_vnd": total_cost_vnd,
        "decision_summary": " | ".join(decision_notes) if decision_notes else "Thu Hai khong co lich quay. Tu dong nghi de bao toan von.",
        "sms_commands": all_sms_commands,
        "tickets_detail": tickets_summary,
        "sensitive": True,
        "distribution": "licensed_device_api_only",
    }

    if write_files:
        sms_txt_path = target_out / "today_sms.txt"
        report_json_path = target_out / "today_report.json"
        sms_txt_path.write_text("\n".join(all_sms_commands), encoding="utf-8")
        report["output_sms_file"] = str(sms_txt_path)
        report["output_report_file"] = str(report_json_path)
        report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run daily pipeline (PRIVATE output; do not publish commands publicly)")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: out/daily or $VIETLOTT_OUT_DIR)")
    ap.add_argument("--no-write", action="store_true", help="Do not write files, just print JSON plan")
    ap.add_argument("--jackpot", type=float, default=None, help="Override jackpot (billion VND) for testing")
    args = ap.parse_args()
    result = run_daily_cloud_pipeline(override_jackpot=args.jackpot, out_dir=args.out_dir, write_files=not args.no_write)
    print(json.dumps(result, ensure_ascii=False, indent=2))
