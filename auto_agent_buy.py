import argparse
import json
import subprocess
import sys
from pathlib import Path

# --- repo root ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cloud_daily_runner import run_daily_cloud_pipeline
from pc_sms_sender import send_sms_via_usb_modem, send_sms_via_windows_phone_link

PUBLIC_DIR = BASE_DIR / "public"


def push_to_github_cloud() -> dict:
    """
    Day ngam file today_sms.txt moi nhat len GitHub Cloud de dong bo voi iPhone Shortcuts
    (khong bat cua so giao dien nao tren man hinh may tinh).
    Dung cho ca nhan (personal). SaaS dung server/license_server.py.
    """
    try:
        subprocess.run(["git", "add", "public/today_sms.txt", "public/today_report.json", "data/"], cwd=BASE_DIR, check=False, capture_output=True)
        diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=BASE_DIR)
        if diff_res.returncode != 0:
            subprocess.run(["git", "commit", "-m", "chore(auto): update daily Vietlott SMS ticket commands"], cwd=BASE_DIR, check=False, capture_output=True)
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=False, capture_output=True, text=True)
            return {"pushed": push_res.returncode == 0, "detail": (push_res.stdout or push_res.stderr or "").strip()}
        return {"pushed": True, "detail": "Already up to date on GitHub Cloud"}
    except Exception as exc:
        return {"pushed": False, "error": str(exc)}


def execute_daily_auto_buy(
    method: str = "cloud_push",
    com_port: str = "COM3",
    override_jackpot: float = None,
    dry_run: bool = False,
    out_dir: str | None = None,
) -> dict:
    """
    Orchestrator:
    1. Run quantitative engine and generate today's SMS commands.
    2. cloud_push (default, personal): write to public/ and push to GitHub Cloud for iPhone to fetch.
    3. local_file: write to out/ (private) only.
    4. phone_link/usb_modem: dispatch SMS locally from this PC.

    SaaS distribution to paying customers must go through server/license_server.py.
    """
    if method == "cloud_push":
        target_out = Path(out_dir) if out_dir else PUBLIC_DIR
    elif out_dir:
        target_out = Path(out_dir)
    else:
        target_out = BASE_DIR / "out" / "daily"

    report = run_daily_cloud_pipeline(override_jackpot=override_jackpot, out_dir=target_out, write_files=True)
    sms_commands = report.get("sms_commands", [])

    if not sms_commands:
        report["execution_status"] = "NO_DRAW_TODAY"
        return report

    if dry_run:
        report["execution_status"] = "DRY_RUN_READY"
        report["dispatch_results"] = {"written_to": str(target_out), "published": False}
        return report

    if method == "cloud_push":
        cloud_res = push_to_github_cloud()
        report["execution_status"] = "CLOUD_SYNCED_FOR_IPHONE"
        report["dispatch_results"] = {"written_to": str(target_out), **cloud_res}
    elif method == "local_file":
        report["execution_status"] = "WRITTEN_PRIVATE"
        report["dispatch_results"] = {"written_to": str(target_out), "published": False}
    elif method == "phone_link":
        send_res = send_sms_via_windows_phone_link("9969", sms_commands)
        report["execution_status"] = "SMS_DISPATCHED_TO_9969"
        report["dispatch_results"] = send_res
    elif method == "usb_modem":
        send_res = send_sms_via_usb_modem(com_port, 115200, "9969", sms_commands)
        report["execution_status"] = "SMS_DISPATCHED_TO_9969"
        report["dispatch_results"] = send_res
    else:
        raise ValueError(f"Unknown method: {method}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run engine and (optionally) publish daily commands for personal iPhone flow")
    parser.add_argument("--method", choices=["cloud_push", "local_file", "phone_link", "usb_modem"], default="cloud_push",
                        help="cloud_push (default, publish to GitHub) | local_file | phone_link | usb_modem")
    parser.add_argument("--com-port", default="COM3", help="COM port if using USB GSM Modem")
    parser.add_argument("--out-dir", default=None, help="Output directory override")
    parser.add_argument("--jackpot", type=float, default=None, help="Override jackpot (billion VND) for testing")
    parser.add_argument("--dry-run", action="store_true", help="Generate and write outputs only")
    args = parser.parse_args()

    out = execute_daily_auto_buy(
        method=args.method,
        com_port=args.com_port,
        override_jackpot=args.jackpot,
        dry_run=args.dry_run,
        out_dir=args.out_dir,
    )
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(out, ensure_ascii=False, indent=2))