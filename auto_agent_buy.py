import argparse
import json
from cloud_daily_runner import run_daily_cloud_pipeline
from pc_sms_sender import send_sms_via_usb_modem, send_sms_via_windows_phone_link


def execute_daily_auto_buy(
    method: str = "phone_link",
    com_port: str = "COM3",
    override_jackpot: float = None,
    dry_run: bool = False,
) -> dict:
    """
    Hàm điều phối trọn gói trên Máy tính Windows:
    1. Chạy mô hình xác suất định lượng (Mega 6/45 hoặc Power 6/55 tùy theo Thứ trong tuần).
    2. Tự động quyết định mua 1 vé đơn (khi Jackpot thấp) hoặc 3 vé Bao 9 rút gọn (khi Jackpot cao).
    3. Điều khiển trực tiếp Windows Phone Link (hoặc USB Modem) gửi SMS tới tổng đài 9969.
    """
    report = run_daily_cloud_pipeline(override_jackpot=override_jackpot)
    sms_commands = report.get("sms_commands", [])

    if not sms_commands:
        report["execution_status"] = "NO_DRAW_TODAY"
        return report

    if dry_run:
        report["execution_status"] = "DRY_RUN_READY"
        return report

    if method == "phone_link":
        send_res = send_sms_via_windows_phone_link("9969", sms_commands)
    elif method == "usb_modem":
        send_res = send_sms_via_usb_modem(com_port, 115200, "9969", sms_commands)
    else:
        raise ValueError(f"Unknown method: {method}")

    report["execution_status"] = "SMS_DISPATCHED_TO_9969"
    report["dispatch_results"] = send_res
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thực thi tự động tính xác suất & gửi SMS 9969 trên PC")
    parser.add_argument("--method", choices=["phone_link", "usb_modem"], default="phone_link")
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

