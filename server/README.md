# License & delivery server

Thư mục này chứa **dự án con (server)** để cấp phép và phân phối lệnh/cấu hình hằng ngày **theo từng thiết bị đã mua**. Mục tiêu: thực thi **1 gói = 1 tài khoản/1 SĐT Vietlott SMS = 1 thiết bị đang hoạt động**, chống phát tán và kiểm soát đổi máy.

## Chính sách (bắt buộc)

- **1 license ↔ tối đa 1 thiết bị active**. Chia sẻ license/shortcut không cấp quyền trên máy khác.
- **Đổi thiết bị (rebind): 150.000đ/lần** (mỗi lần đổi). Yêu cầu xác minh + ghi nhận mã giao dịch/biên nhận thanh toán phí.
- Khi rebind: **thu hồi/vô hiệu thiết bị cũ ngay**, mở slot để khách kích hoạt máy mới.
- **Cooldown tối thiểu 30 ngày** giữa 2 lần rebind (có thể override thủ công có kiểm soát, phải ghi log/lý do) để hạn chế lạm dụng/cho mượn.
- Dấu hiệu bất thường (đổi liên tục, nhiều lần kích hoạt sai, chia sẻ) → tạm khóa/điều tra theo điều khoản.
- **Không** phát lệnh qua file/URL công khai. Chỉ API có xác thực (`license_key` + `device_id` + `device_secret`).

Xem thêm: [`../docs/SECURITY_LICENSING.md`](../docs/SECURITY_LICENSING.md).

## Yêu cầu

- Python 3.10+ (chỉ dùng thư viện chuẩn: `sqlite3`, `http.server`, `hmac`, ...).
- Chạy trên máy chủ riêng/VPS, đặt sau **HTTPS** (reverse proxy: Nginx/Caddy/Cloudflare Tunnel...). Không public HTTP trần.
- DB `licenses.db` chứa dữ liệu khách/license → **giữ private, backup định kỳ, phân quyền truy cập**.

## Chạy nhanh (local/dev)

```bash
# từ thư mục gốc repo
python server/license_server.py init-db
set ADMIN_TOKEN=change-me-strong-secret        # Windows PowerShell: $env:ADMIN_TOKEN="..."
python server/license_server.py serve --host 127.0.0.1 --port 8787

# kiểm tra
curl http://127.0.0.1:8787/healthz
```

Mặc định DB: `server/licenses.db` (override bằng `--db` hoặc `LICENSE_DB_PATH`).

## Quản trị (CLI)

```bash
# Tạo license cho khách (1 gói)
python server/license_server.py create-license --name "Nguyen Van A" --phone "0912345678" --notes "don 999k ..."

# Liệt kê
python server/license_server.py list

# Tạm ngưng / kích hoạt / thu hồi
python server/license_server.py set-status VAF-XXXX-XXXX-XXXX-XXXX suspended
python server/license_server.py set-status VAF-XXXX-XXXX-XXXX-XXXX active

# Duyệt ĐỔI MÁY (thu 150.000đ/lần, thu hồi máy cũ, áp cooldown 30 ngày)
python server/license_server.py rebind VAF-XXXX-XXXX-XXXX-XXXX \
  --paid-ref "SEPAY_.../MA_GD" --reason "doi may moi" --admin-note "da xac minh"

# Xem chính sách
python server/license_server.py show-policy
```

## API (tóm tắt)

Tất cả response JSON, `Cache-Control: no-store`.

- `POST /api/activate` `{ "license_key": "...", "device_id": "<uuid-client>", "client_info": "ios-shortcut/1.0" }`
  - Bind thiết bị nếu license hợp lệ và **chưa có thiết bị active**. Trả `device_secret` **một lần** (client phải lưu an toàn trên máy). Nếu đã có thiết bị khác active → từ chối (yêu cầu rebind).
- `POST /api/today` hoặc `GET /api/today?license_key=...&device_id=...&device_secret=...`
  - Trả plan/lệnh SMS của ngày **chỉ khi** license active và thiết bị/secret khớp thiết bị đang bind.
- `POST /api/status` / `GET /api/status?...` — kiểm tra trạng thái license/thiết bị.
- Admin (header `X-Admin-Token: $ADMIN_TOKEN`): `POST /api/admin/create-license`, `POST /api/admin/set-status`, `POST /api/admin/rebind`, `GET /api/admin/licenses`.

## Tích hợp client (iPhone Shortcuts / Android)

- Khi kích hoạt lần đầu: sinh `device_id` (UUID) và lưu cục bộ; gọi `/api/activate`; lưu `device_secret` trả về (Keychain/Data Jar/lưu trữ an toàn của app). **Không chia sẻ** `device_secret`.
- Mỗi lần lấy lệnh: gọi `/api/today` với `license_key + device_id + device_secret`; gửi các SMS trong `plan.sms_commands` tới 9969 từ **chính SĐT Vietlott SMS của khách** (đúng điều kiện Vietlott). Tôn trọng quyền tạm dừng: nếu khách tắt tự động, client không gọi/gửi.
- Nếu server trả `another_device_active` → hướng dẫn liên hệ hỗ trợ để đổi máy (150.000đ/lần, xác minh).

## Lưu ý triển khai thực tế

- `today` hiện sinh plan theo logic chung (`cloud_daily_runner`) phía server và **chỉ cấp cho thiết bị hợp lệ** (đã chặn chia sẻ). Để cá nhân hóa sâu theo từng khách (bộ số/số lượng/cấu hình riêng) hãy mở rộng `licenses.config_json` và logic sinh plan.
- Kết nối thanh toán (SePay webhook) để tự tạo/active license và tự ghi nhận đối soát là bước tiếp theo; hiện hỗ trợ cấp thủ công an toàn qua CLI/API admin.
- Luôn triển khai sau HTTPS, giới hạn rate, giám sát log `access_logs`, và sao lưu DB.
