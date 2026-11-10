import subprocess
import time
from typing import List


def send_sms_via_usb_modem(com_port: str, baudrate: int, phone_number: str, messages: List[str]) -> List[dict]:
    """
    PHƯƠNG ÁN USB MODEM:
    Gửi SMS trực tiếp từ Máy tính qua USB GSM/4G Modem (AT+CMGF=1, AT+CMGS="9969").
    """
    import serial

    results = []
    with serial.Serial(com_port, baudrate, timeout=10) as ser:
        ser.write(b"AT\r\n")
        time.sleep(0.5)
        ser.write(b"AT+CMGF=1\r\n")
        time.sleep(0.5)

        for msg in messages:
            cmd = f'AT+CMGS="{phone_number}"\r\n'.encode("ascii")
            ser.write(cmd)
            time.sleep(1.0)
            ser.write(msg.encode("ascii") + b"\x1a")
            time.sleep(4.0)
            resp = ser.read_all().decode("utf-8", errors="ignore")
            results.append({"message": msg, "status": "SENT_VIA_USB_MODEM", "modem_response": resp.strip()})

    return results


def send_sms_via_windows_phone_link(phone_number: str, messages: List[str]) -> List[dict]:
    """
    PHƯƠNG ÁN WINDOWS PHONE LINK (LIÊN KẾT ĐIỆN THOẠI VỚI IPHONE):
    1. Kích hoạt cửa sổ 'Liên kết điện thoại' (ms-phone:) lên tiền cảnh.
    2. Dùng phím tắt chuẩn của Phone Link:
       - Ctrl + N : Mở khung 'Tin nhắn mới' (con trỏ tự đặt ở ô người nhận 'Đến:')
       - Nhập '9969' + Enter : Chọn đầu số tổng đài Vietlott 9969
       - Tab : Chuyển con trỏ xuống ô nhập nội dung tin nhắn
       - Ctrl + V : Dán cú pháp vé (ví dụ: '655 K1 S 07 11 18 24 41 55')
       - Enter : Bấm gửi tin nhắn ngay lập tức!
    """
    results = []
    for msg in messages:
        ps_script = f"""
        Set-Clipboard -Value "{msg}"
        Start-Process "ms-phone:"
        Start-Sleep -Seconds 3
        $wshell = New-Object -ComObject wscript.shell
        $null = $wshell.AppActivate("Liên kết điện thoại")
        $null = $wshell.AppActivate("Phone Link")
        Start-Sleep -Milliseconds 800
        # Nhấn Ctrl+N để bấm nút 'Tin nhắn mới'
        $wshell.SendKeys("^n")
        Start-Sleep -Seconds 1
        # Gõ số tổng đài 9969 và nhấn Enter
        $wshell.SendKeys("{phone_number}")
        Start-Sleep -Milliseconds 600
        $wshell.SendKeys("~")
        Start-Sleep -Milliseconds 800
        # Nhấn Tab chuyển xuống ô nhập tin nhắn và dán nội dung vé
        $wshell.SendKeys("{{TAB}}")
        Start-Sleep -Milliseconds 500
        $wshell.SendKeys("^v")
        Start-Sleep -Milliseconds 600
        # Nhấn Enter để gửi tin nhắn tới 9969
        $wshell.SendKeys("~")
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)
        results.append({"recipient": phone_number, "message": msg, "status": "SENT_VIA_PHONE_LINK"})
        time.sleep(2.5)

    return results
