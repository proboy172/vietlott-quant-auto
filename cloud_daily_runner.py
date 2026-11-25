import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- repo root on path (safe when run from server/CI) ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_sync import sync_vietlott_data
from iphone_automation_server import get_today_game_code
from quant_engine import (
    GAME_CONFIGS,
    analyze_historical_stats,
    generate_1_ticket_optimal,
    generate_2_tickets_diversity_optimal,
    generate_3_tickets_abbreviated_wheel,
    generate_dynamic_quant_plan,
    ticket_key,
)

# Outputs are PRIVATE (per-day SMS commands have value). Never publish to a public repo/URL.
# Default: out/daily (gitignored). Override with VIETLOTT_OUT_DIR.
OUT_DIR = Path(os.environ.get("VIETLOTT_OUT_DIR", str(BASE_DIR / "out" / "daily")))

COST_PER_TICKET_VND = 10_000
RECENT_STATE_PATH = BASE_DIR / "data" / "last_published.json"
RECENT_WINDOW = 5  # loại các vé đã phát trong 5 ngày gần nhất


def _load_recent_ticket_keys(avoid_recent: bool) -> List[str]:
    """Đọc các tổ hợp đã phát gần đây để daily rotation không gửi lại vé cũ."""
    if not avoid_recent or not RECENT_STATE_PATH.exists():
        return []
    try:
        state = json.loads(RECENT_STATE_PATH.read_text(encoding="utf-8"))
        entries = state.get("recent", [])[-RECENT_WINDOW:]
        keys: List[str] = []
        for entry in entries:
            for sms in entry.get("sms_commands", []):
                parts = sms.split()
                if "S" in parts:
                    nums = parts[parts.index("S") + 1:]
                    if len(nums) == 6:
                        keys.append(ticket_key([int(x) for x in nums]))
        return keys
    except Exception:
        return []


def _save_recent_ticket(sms_commands: List[str], report_date: str, avoid_recent: bool) -> None:
    if not avoid_recent or not sms_commands:
        return
    try:
        state = {"recent": []}
        if RECENT_STATE_PATH.exists():
            state = json.loads(RECENT_STATE_PATH.read_text(encoding="utf-8"))
        recent = state.get("recent", [])
        recent = [e for e in recent if e.get("date") != report_date]
        recent.append({"date": report_date, "sms_commands": list(sms_commands)})
        state["recent"] = recent[-RECENT_WINDOW:]
        RECENT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        RECENT_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Lưu state thất bại không được làm hỏng bản phát hành
        pass


def fetch_live_jackpot_billion(game_code: str) -> float:
    """
    Lay gia tri Jackpot hien tai (ty VND) tu nguon cong khai.
    Neu khong lay duoc, tra ve muc co so (12 ty cho 6/45, 30 ty cho 6/55).
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


def _normalize_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    c = dict(config or {})
    # accept common aliases
    game = str(c.get("game") or c.get("game_code") or "auto").strip().lower()
    if game in {"mega645", "mega", "mega 6/45", "6/45"}:
        game = "645"
    elif game in {"power655", "power", "power 6/55", "6/55"}:
        game = "655"
    elif game not in {"645", "655", "auto"}:
        game = "auto"
    mode = str(c.get("mode") or c.get("plan_mode") or "dynamic").strip().lower()
    aliases = {"ai_1": "1", "ai1": "1", "1_ticket": "1", "single": "1",
               "ai_2": "2", "ai2": "2", "2_tickets": "2", "diversity": "2",
               "ai_3": "3", "ai3": "3", "3_tickets": "3", "wheel": "3",
               "auto": "dynamic"}
    mode = aliases.get(mode, mode)
    if mode not in {"dynamic", "1", "2", "3", "custom"}:
        mode = "dynamic"
    ticket_count = c.get("ticket_count") or c.get("quantity") or c.get("tickets")
    try:
        ticket_count = int(ticket_count) if ticket_count is not None else None
    except Exception:
        ticket_count = None
    if ticket_count is not None:
        ticket_count = max(1, min(30, ticket_count))
    custom = c.get("custom_tickets") or c.get("numbers") or c.get("tickets_numbers") or []
    return {**c, "game": game, "mode": mode, "ticket_count": ticket_count, "custom_tickets": custom}


def _format_sms(game_code: str, numbers: List[int]) -> str:
    nums = sorted(int(n) for n in numbers)
    return f"{game_code} K1 S " + " ".join(f"{n:02d}" for n in nums)


def _parse_custom_tickets(custom: Any, cfg: Any, max_tickets: Optional[int] = None) -> List[Dict[str, Any]]:
    # Accept: [[1,2,3,4,5,6], ...] or ["01 02 03 04 05 06", ...] or {"tickets":[...]}
    if isinstance(custom, dict):
        custom = custom.get("tickets") or custom.get("custom_tickets") or []
    if isinstance(custom, str):
        # allow "01 02 03 04 05 06" or multiple separated by ; or newline
        parts = [p.strip() for p in re.split(r"[;\n]+", custom) if p.strip()]
        custom = parts if parts else [custom]
    if not isinstance(custom, list):
        return []
    tickets = []
    seen = set()
    for item in custom:
        nums: List[int] = []
        if isinstance(item, str):
            nums = [int(x) for x in re.findall(r"\d+", item)]
        elif isinstance(item, (list, tuple)):
            try:
                nums = [int(x) for x in item]
            except Exception:
                nums = []
        elif isinstance(item, dict) and "numbers" in item:
            try:
                nums = [int(x) for x in (item.get("numbers") or [])]
            except Exception:
                nums = []
        nums = sorted(n for n in nums if 1 <= n <= cfg.max_ball)
        # unique 6 numbers
        nums = sorted(set(nums))
        if len(nums) != 6:
            continue
        key = tuple(nums)
        if key in seen:
            continue
        seen.add(key)
        tickets.append({
            "numbers": nums,
            "formatted": " ".join(f"{n:02d}" for n in nums),
            "sms": _format_sms(cfg.code, nums),
            "source": "custom",
        })
        if max_tickets and len(tickets) >= max_tickets:
            break
    return tickets


def _generate_ai_plan(stats: dict, mode: str, ticket_count: Optional[int], live_jp: float) -> dict:
    if mode == "1":
        plan = generate_1_ticket_optimal(stats)
    elif mode == "2":
        plan = generate_2_tickets_diversity_optimal(stats)
    elif mode == "3":
        plan = generate_3_tickets_abbreviated_wheel(stats)
    else:
        # dynamic, optionally honoring desired ticket_count
        plan = generate_dynamic_quant_plan(stats, live_jackpot_billion=live_jp)
        if ticket_count in (1, 2, 3):
            desired = str(ticket_count)
            current_n = len(plan.get("sms_commands", []) or [])
            if desired != str(current_n if current_n in (1, 2, 3) else 0):
                if desired == "1":
                    plan = generate_1_ticket_optimal(stats)
                elif desired == "2":
                    plan = generate_2_tickets_diversity_optimal(stats)
                elif desired == "3":
                    plan = generate_3_tickets_abbreviated_wheel(stats)
    return plan


def run_daily_cloud_pipeline(force_date: datetime.date = None, override_jackpot: float = None,
                             out_dir: str | Path | None = None, write_files: bool = True,
                             config: Optional[Dict[str, Any]] = None,
                             sync_data: bool = True, avoid_recent: bool = False) -> dict:
    """
    Chay pipeline hang ngay (private): dong bo du lieu, tinh toan, sinh lenh SMS.

    - Ket qua/lenh SMS la tai san van hanh: ghi ra thu muc PRIVATE (mac dinh out/daily, gitignored)
      hoac tra ve in-memory de server cap phep phan phoi cho thiet bi da kich hoat.
    - KHONG commit/push lenh ra repo/file cong khai.
    - Ho tro cau hinh per-customer (config): chon game, so luong ve, bo so tuy chon hoac AI.
    """
    target_out = Path(out_dir) if out_dir else OUT_DIR
    if write_files:
        target_out.mkdir(parents=True, exist_ok=True)

    cfg_in = _normalize_config(config)
    if sync_data:
        sync_vietlott_data()

    vn_tz = datetime.timezone(datetime.timedelta(hours=7))
    now_vn = datetime.datetime.now(vn_tz)
    today = force_date or now_vn.date()
    # Stale guard: không bao giờ phát hành lệnh mang ngày khác ngày hiện tại.
    if write_files and str(today) != now_vn.date().isoformat():
        raise ValueError(
            f"STALE OUTPUT: ngày phát hành {today} != hôm nay {now_vn.date()}. "
            "Từ chối ghi đè today_sms.txt/today_report.json."
        )
    schedule_game = get_today_game_code(today)
    exclude_keys = _load_recent_ticket_keys(avoid_recent)
    latest_draw_date = None

    chosen_game = cfg_in.get("game", "auto")
    if chosen_game == "auto":
        game_code = schedule_game
    else:
        game_code = chosen_game

    all_sms_commands: List[str] = []
    tickets_summary: List[Dict[str, Any]] = []
    total_cost_vnd = 0
    decision_notes: List[str] = []
    live_jp = 0.0

    if game_code is None:
        game_cfg = None
        decision_notes.append("Hom nay khong co lich quay (nghi).")
    elif schedule_game is not None and game_code != schedule_game:
        game_cfg = GAME_CONFIGS.get(game_code)
        decision_notes.append(
            f"Hom nay la lich quay {GAME_CONFIGS[schedule_game].name} ({schedule_game}), "
            f"khong phai {game_cfg.name if game_cfg else game_code}. Khong gui lenh de tranh sai ky hieu."
        )
        game_code = None
    else:
        game_cfg = GAME_CONFIGS.get(game_code)
        live_jp = override_jackpot if override_jackpot is not None else fetch_live_jackpot_billion(game_code)
        if cfg_in.get("jackpot_override_billion") is not None:
            try:
                live_jp = float(cfg_in["jackpot_override_billion"])
            except Exception:
                pass
        stats = analyze_historical_stats(
            game_code,
            target_date=str(today),
            exclude_ticket_keys=exclude_keys,
        )
        latest_draw_date = (stats.get("latest_draw") or {}).get("date")
        mode = cfg_in.get("mode", "dynamic")
        ticket_count = cfg_in.get("ticket_count")

        # 1) Custom/fixed tickets (per-customer selected numbers) take priority when provided
        custom_tickets = _parse_custom_tickets(cfg_in.get("custom_tickets"), game_cfg, max_tickets=ticket_count)
        if mode == "custom" or custom_tickets:
            if custom_tickets:
                all_sms_commands = [t["sms"] for t in custom_tickets]
                for i, t in enumerate(custom_tickets, 1):
                    tickets_summary.append({"game": game_cfg.name, "detail": {**t, "ticket_index": i}})
                decision_notes.append(
                    f"[{game_cfg.name}] Su dung bo so tuy chon cua khach ({len(custom_tickets)} ve)."
                )
            else:
                decision_notes.append(
                    f"[{game_cfg.name}] Che do bo so tuy chon nhung khong co bo so hop le (can 6 so, 01-{game_cfg.max_ball:02d})."
                )
        else:
            # 2) AI/engine-generated plan (dynamic or fixed 1/2/3), personalized per license by server-side generation
            plan_matrix = _generate_ai_plan(stats, mode=mode, ticket_count=ticket_count, live_jp=live_jp)
            cmds = list(plan_matrix.get("sms_commands", []) or [])
            details = list(plan_matrix.get("tickets", []) or [])
            if ticket_count and ticket_count > 0 and len(cmds) > ticket_count:
                cmds = cmds[:ticket_count]
                details = details[:ticket_count]
            all_sms_commands.extend(cmds)
            for tk in details:
                tickets_summary.append({"game": game_cfg.name, "detail": tk})
            reason = plan_matrix.get("decision_reason") or plan_matrix.get("mode") or "AI toi uu"
            decision_notes.append(f"[{game_cfg.name}] {reason} (Chi phi: {len(cmds) * COST_PER_TICKET_VND:,}d)")

        total_cost_vnd = len(all_sms_commands) * COST_PER_TICKET_VND

    report = {
        "date": str(today),
        "status": "ACTIVE_BUY" if all_sms_commands else "REST_DAY",
        "primary_matrix_game": (game_cfg.name if game_cfg else ("Nghi quay (Thu 2)" if schedule_game is None else None)) or "Nghi/khong gui",
        "detected_jackpot_billion": live_jp,
        "total_cost_vnd": total_cost_vnd,
        "decision_summary": " | ".join(decision_notes) if decision_notes else "Khong co lenh.",
        "sms_commands": all_sms_commands,
        "tickets_detail": tickets_summary,
        "sensitive": True,
        "distribution": "licensed_device_api_only",
        "generated_at": now_vn.isoformat(timespec="seconds"),
        "rotation_date": str(today),
        "latest_draw_date": latest_draw_date,
        "avoided_recent_tickets": bool(avoid_recent),
        "config_applied": {k: v for k, v in cfg_in.items() if k in ("game", "mode", "ticket_count")},
    }

    if write_files:
        sms_txt_path = target_out / "today_sms.txt"
        report_json_path = target_out / "today_report.json"
        sms_txt_path.write_text("\n".join(all_sms_commands), encoding="utf-8")
        date_txt_path = target_out / "today_date.txt"
        date_txt_path.write_text(str(today), encoding="utf-8")
        report["output_sms_file"] = str(sms_txt_path)
        report["output_report_file"] = str(report_json_path)
        report["output_date_file"] = str(date_txt_path)
        report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        _save_recent_ticket(all_sms_commands, str(today), avoid_recent)

    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run daily pipeline (PRIVATE output; do not publish commands publicly)")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: out/daily or $VIETLOTT_OUT_DIR)")
    ap.add_argument("--no-write", action="store_true", help="Do not write files, just print JSON plan")
    ap.add_argument("--jackpot", type=float, default=None, help="Override jackpot (billion VND) for testing")
    ap.add_argument("--config", default=None, help="JSON config (per-customer): game/mode/ticket_count/custom_tickets")
    ap.add_argument("--config-file", default=None, help="Path to JSON config file")
    ap.add_argument("--force-date", default=None, help="YYYY-MM-DD (chỉ để test rotation; không dùng khi publish)")
    ap.add_argument("--no-sync", action="store_true", help="Không tải lại dữ liệu lịch sử (dùng khi test offline)")
    ap.add_argument("--avoid-recent", action="store_true", help="Không gửi lại vé đã phát trong 5 ngày gần nhất")
    args = ap.parse_args()
    cfg = None
    if args.config_file:
        try:
            cfg = json.loads(Path(args.config_file).read_text(encoding="utf-8"))
        except Exception:
            cfg = None
    if args.config:
        try:
            cfg = json.loads(args.config)
        except Exception:
            cfg = cfg
    forced = datetime.date.fromisoformat(args.force_date) if args.force_date else None
    result = run_daily_cloud_pipeline(
        force_date=forced,
        override_jackpot=args.jackpot,
        out_dir=args.out_dir,
        write_files=not args.no_write,
        config=cfg,
        sync_data=not args.no_sync,
        avoid_recent=args.avoid_recent,
    )
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(result, ensure_ascii=False, indent=2))
