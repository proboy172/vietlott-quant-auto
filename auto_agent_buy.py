import argparse
import json
import sys
from pathlib import Path

# --- repo root ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cloud_daily_runner import OUT_DIR, run_daily_cloud_pipeline
from pc_sms_sender import send_sms_via_usb_modem, send_sms_via_windows_phone_link


def push_to_github_cloud(*args, **kwargs) -> dict:
    """
    DISABLED (security/licensing): publishing daily SMS commands to a GitHub repo/file
    makes them accessible to anyone who can read the repo/raw URL, enabling unpaid use.
    Commands must be delivered only via the authenticated, per-device license server API.
    """
    return {
        "pushed": False,
        "disabled": True,
        "reason": "Public distribution of today_sms.txt is disabled. Use server/license_server.py (per-device API) instead.",
    }


def execute_daily_auto_buy(
    method: str = "local_file",
    com_port: str = "COM3",
    override_jackpot: float = None,
    dry_run: bool = False,
    out_dir: str | None = None,
) -> dict:
    """
    Orchestrator (private/internal):
    1. Run quantitative engine and generate today's SMS commands.
    2. NEVER publish commands to a public location. Default: write to private out/ (gitignored).
    3. Optional local dispatch (phone_link/usb_modem) for an authorized, owned device only.

    Production distribution to paying customers must go through server/license_server.py
    (1 license = 1 active device, device-bound API).
    """
    target_out = Path(out_dir) if out_dir else OUT_DIR
    report = run_daily_cloud_pipeline(override_jackpot=override_jackpot, out_dir=target_out, write_files=True)
    sms_commands = report.get("sms_commands", [])

    if not sms_commands:
        report["execution_status"] = "NO_DRAW_TODAY"
        return report

    if dry_run:
        report["execution_status"] = "DRY_RUN_READY"
        report["dispatch_results"] = {"written_to": str(target_out), "published": False}
        return report

    if method in ("cloud_push", "local_file"):
        # cloud_push kept as alias but never pushes; always local/private output only.
        report["execution_status"] = "WRITTEN_PRIVATE" if method == "local_file" else "CLOUD_PUSH_DISABLED_WRITTEN_PRIVATE"
        report["dispatch_results"] = {
            "written_to": str(target_out),
            "published": False,
            "note": "Use license server API for per-device delivery. Public push is disabled.",
        }
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
    parser = argparse.ArgumentParser(description="Run engine and output PRIVATE daily commands (no public publishing)")
    parser.add_argument("--method", choices=["local_file", "cloud_push", "phone_link", "usb_modem"], default="local_file",
                        help="local_file (default, private) | cloud_push (disabled alias) | phone_link | usb_modem")
    parser.add_argument("--com-port", default="COM3", help="COM port if using USB GSM Modem")
    parser.add_argument("--out-dir", default=None, help="Private output directory (default: out/daily)")
    parser.add_argument("--jackpot", type=float, default=None, help="Override jackpot (billion VND) for testing")
    parser.add_argument("--dry-run", action="store_true", help="Generate and write private outputs only")
    args = parser.parse_args()

    out = execute_daily_auto_buy(
        method=args.method,
        com_port=args.com_port,
        override_jackpot=args.jackpot,
        dry_run=args.dry_run,
        out_dir=args.out_dir,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
