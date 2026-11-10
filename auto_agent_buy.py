import argparse
import json
import subprocess
from pathlib import Path
from cloud_daily_runner import run_daily_cloud_pipeline
from pc_sms_sender import send_sms_via_usb_modem, send_sms_via_windows_phone_link

BASE_DIR = Path(__file__).resolve().parent


def push_to_github_cloud() -> dict:
    """
    Đẩy ngầm file today_sms.txt mới nhất lên GitHub Cloud để đồng bộ với iPhone Shortcuts
    (không bật bất kỳ cửa sổ giao diện nào trên màn hình máy tính).
    """
    try:
        subprocess.run(["git", "add", "public/today_sms.txt", "public/today_report.json", "data/"], cwd=BASE_DIR, check=False, capture_output=True)
        diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=BASE_DIR)
        if diff_res.returncode != 0:
            subprocess.run(["git", "commit", "-m", "chore(sync): update daily combinatorial state"], cwd=BASE_DIR, check=False, capture_output=True)
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=False, capture_output=True, text=True)
            return {"pushed": push_res.returncode == 0, "detail": push_res.stdout or push_res.stderr}
        return {"pushed": True, "detail": "Already up to date on GitHub Cloud"}
    except Exception as exc:
        return {"pushed": False, "error": str(exc)}


def execute_daily_auto_buy(
    method: str = "cloud_push",
    com_port: str = "COM3",
    override_jackpot: float = None,
    dry_run: bool = False,
) -> dict:
    """
    Hàm điều phối trọn gói:
    1. Chạy mô hình xác suất định lượng (Mega 6/45 hoặc Power 6/55 tùy theo Thứ trong tuần).
    2. Tự động quyết định mua 1 vé đơn (khi Jackpot thấp) hoặc 3 vé Bao 9 rút gọn (khi Jackpot cao).
    3. Mặc định (cloud_push): Cập nhật ngầm lên GitHub Cloud để iPhone tự lấy qua 4G/Wi-Fi và gửi 9969.
    """
    report = run_daily_cloud_pipeline(override_jackpot=override_jackpot)
    sms_commands = report.get("sms_commands", [])

    if not sms_commands:
        report["execution_status"] = "NO_DRAW_TODAY"
        return report

    if dry_run:
        report["execution_status"] = "DRY_RUN_READY"
        return report

    if method == "cloud_push":
        cloud_res = push_to_github_cloud()
        report["execution_status"] = "CLOUD_SYNCED_FOR_IPHONE"
        report["dispatch_results"] = cloud_res
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
    parser = argparse.ArgumentParser(description="Thực thi tự động tính xác suất & đồng bộ Cloud / gửi SMS 9969")
    parser.add_argument("--method", choices=["cloud_push", "phone_link", "usb_modem"], default="cloud_push")
    parser.add_argument("--com-port", default="COM3", help="Cổng COM nếu dùng USB GSM Modem")
    parser.add_argument("--jackpot", type=float, default=None, help="Ghi đè mức Jackpot (tỷ VNĐ) để test")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ tính số và xuất lệnh, chưa gửi SMS")
    args = parser.parse_args()

    out = execute_daily_auto_buy(
        method=args.method,
        com_port=args.com_port,
        override_jackpot=args.jackpot,
        dry_run=args.dry_run,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))

