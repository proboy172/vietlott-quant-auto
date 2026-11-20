# Hướng dẫn tích hợp client (iPhone Shortcuts & Android) — Thin client gắn thiết bị

Tài liệu này hướng dẫn tích hợp client để **chỉ thiết bị đã mua/kích hoạt** mới nhận được lệnh/cấu hình hằng ngày. Lệnh SMS **không** phát qua file/URL công khai và **không** nhúng thuật toán/engine vào client.

> Tuân thủ: công cụ hỗ trợ tự động gửi SMS tới **9969** từ **chính số Vietlott SMS của khách** (theo điều kiện Vietlott). Không bán vé, không mua hộ, không giữ tiền, **không đảm bảo trúng**. Khách luôn có quyền **tạm dừng/bật tắt** tự động bất cứ lúc nào.

## 1) Kiến trúc & nguyên tắc

- **1 license = 1 gói = 1 khách = 1 SĐT Vietlott SMS = 1 thiết bị đang hoạt động** (server thực thi).
- Client sinh `device_id` (UUID, lưu cục bộ trên máy) → gọi **activate** → nhận & lưu `device_secret` (một lần, chỉ trên máy đó). Mỗi lần chạy gọi **today** với `license_key + device_id + device_secret`.
- Server chỉ trả `plan.sms_commands`/cấu hình khi license **active** và đúng thiết bị đang bind. Chia sẻ Shortcut/app/`license_key` **không** cấp quyền nếu thiếu `device_secret` hợp lệ gắn đúng máy.
- **Đổi máy:** 150.000đ/lần, xác minh + mã giao dịch, **thu hồi máy cũ ngay**, cooldown tối thiểu **30 ngày** (admin thực hiện `rebind`). Sau rebind khách activate lại trên máy mới để nhận `device_secret` mới.
- Mọi request qua **HTTPS**. Không log/lộ `device_secret` hay lệnh ra nơi công khai.

## 2) Thông tin cần cấp cho khách (kênh riêng tư)

- `SERVER_URL` (HTTPS), `license_key` (riêng từng khách).
- Hướng dẫn cài đặt/kích hoạt lần đầu và cách **tạm dừng/bật tắt** tự động.
- Điều kiện Vietlott SMS: đúng SĐT đã đăng ký, tài khoản/thẻ thanh toán mặc định, đủ số dư/hạn mức, trong giờ nhận lệnh; bật quyền/tự động hóa cần thiết.

## 3) API (`server/license_server.py`)

Tất cả response JSON, `Cache-Control: no-store`.

### `POST /api/activate`
- Body: `{ "license_key": "...", "device_id": "<uuid>", "client_info": "ios-shortcut/1.0" }`
- `200 ok`: `{ "ok": true, "status": "activated"|"already_active", "device_secret": "..." }` → **lưu `device_secret` an toàn trên máy** (chỉ trả khi bind/bind lại; `already_active` có thể không trả lại secret).
- `403 another_device_active`: đã có máy khác active → hướng dẫn đổi máy (150.000đ/lần, xác minh).
- `403/404/400`: `license_not_found`, `license_status_*`, `missing_license_or_device_id`, v.v.

### `GET|POST /api/today`
- Query/body: `license_key`, `device_id`, `device_secret`
- `200 ok`:  
  `{ "ok": true, "plan": { "date": "YYYY-MM-DD", "status": "ACTIVE_BUY"|"REST_DAY", "sms_commands": ["645 K1 S 01 02 03 04 05 06", ...], "total_cost_vnd": 10000, "decision_summary": "...", "config_applied": {...} } }`
- `403`: `device_not_active` / `invalid_device_secret` / `license_status_*` / `another_device_active` / `missing_credentials` → dừng và thông báo phù hợp.
- `REST_DAY` hoặc `sms_commands` rỗng: không gửi SMS.

### `GET|POST /api/status`
- Kiểm tra `license_status`, `has_active_device`, `device_authorized`.

## 4) Luồng iPhone (Shortcuts / Phím tắt)

### 4.1 Kích hoạt (chạy 1 lần)
1. **Text** `SERVER_URL` = `https://<your-server>`
2. **Text** `LICENSE_KEY` = mã của khách
3. **Get File** (trong Shortcuts/iCloud, ví dụ `vietlott_device.json`; nếu chưa có thì bỏ qua lỗi) → đọc `device_id`, `device_secret`.
4. Nếu `device_id` trống: **Generate UUID** → gán `device_id`.
5. Nếu `device_secret` trống: **Get Contents of URL**
   - Method `POST`, URL `SERVER_URL + "/api/activate"`, Request Body = JSON
   - Body: `license_key`, `device_id`, `client_info` = `ios-shortcut/1.0`
   - Lấy `ok` và `device_secret`. Nếu `ok` != true → **Show Alert** (hiện `error`/`message`, đặc biệt `another_device_active`) và **Stop**.
   - **Save File** `vietlott_device.json` nội dung `{ "device_id": "...", "device_secret": "..." }` (lưu cục bộ trên máy khách).
6. Thông báo “Kích hoạt thành công”.

### 4.2 Lấy lệnh & gửi SMS (chạy theo lịch)
1. Đọc `vietlott_device.json` → `device_id`, `device_secret`. Thiếu → yêu cầu chạy Kích hoạt.
2. **Get Contents of URL** `SERVER_URL + "/api/today"` (POST JSON: `license_key`, `device_id`, `device_secret`).
3. Nếu `ok` != true → thông báo lỗi/trạng thái và **Stop**. Nếu `plan.status` == `REST_DAY` hoặc `sms_commands` rỗng → kết thúc.
4. **Repeat with Each** trong `plan.sms_commands`:
   - **Send Message**: nội dung = item, người nhận = `9969` (gửi từ SIM/số Vietlott SMS của khách).
   - (Tuỳ chọn) chờ vài giây giữa các tin.
5. (Tuỳ chọn) ghi log cục bộ ngày/đã gửi (không gửi log nhạy cảm ra ngoài).

### 4.3 Tự động hóa & tạm dừng (iPhone)
- Tạo **Personal Automation** (thời gian/điều kiện phù hợp lịch quay) chạy shortcut lấy-lệnh-&-gửi; bật quyền/tự động hóa cần thiết. Tuỳ phiên bản iOS/cài đặt có thể yêu cầu xác nhận — cần hướng dẫn khách bật đúng.
- **Tạm dừng/bật tắt:** tắt Automation/Shortcut hoặc xoá lịch chạy bất cứ lúc nào. Khi tắt, không gửi lệnh mua vé.

## 5) Luồng Android (thin client / automation)

1. **Kích hoạt (1 lần):** sinh `device_id` (UUID) lưu an toàn (ví dụ EncryptedSharedPreferences/Keystore); `POST /api/activate` → lưu `device_secret` an toàn trên máy. Không hardcode, không chia sẻ.
2. **Lấy lệnh:** `POST/GET /api/today` với đủ 3 trường. Kiểm tra `ok` và `plan.status`.
3. **Gửi SMS:** với mỗi `plan.sms_commands` gửi tới `9969` từ đúng SĐT Vietlott SMS đã đăng ký (cần quyền `SEND_SMS`, tuân chính sách nền tảng nếu phát hành). Có thể dùng WorkManager/Alarm trong khung giờ phù hợp; tôn trọng tối ưu pin.
4. **Tạm dừng/bật tắt:** cung cấp nút/toggle tắt tự động hoặc hướng dẫn tắt quyền/lịch; khi tắt không gọi/gửi.
5. **Xử lý lỗi:** hiển thị rõ khi `another_device_active`, license tạm ngưng/hết hiệu lực, hoặc thiếu điều kiện Vietlott (số dư/hạn mức/giờ/sai số) — Vietlott nhận lệnh hay không phụ thuộc điều kiện tài khoản Vietlott SMS của khách.

## 6) Bảo mật phía client (bắt buộc)

- `device_secret` và `license_key` là bí mật từng khách: lưu cục bộ an toàn, **không** nhúng vào bản phát hành công khai, **không** commit, **không** gửi kèm lệnh ra kênh công khai.
- Không gọi/đọc lệnh từ file/URL công khai (repo raw, public storage…). Chỉ tin dữ liệu từ `SERVER_URL` (HTTPS).
- Không log nội dung `sms_commands`, `device_secret` ra dịch vụ bên thứ ba.

## 7) Đổi máy (rebind)

- Phí **150.000đ/lần**, cần xác minh + mã giao dịch. Admin thực hiện:  
  `python server/license_server.py rebind <LICENSE_KEY> --paid-ref "MA_GD" --reason "..."`
- Máy cũ bị **thu hồi/vô hiệu ngay**, áp **cooldown 30 ngày** (override có kiểm soát). Sau đó khách chạy lại **Kích hoạt** trên máy mới để nhận `device_secret` mới.

## 8) Kiểm tra nhanh (ops)

```bash
# tạo license & cấu hình per-khách
python server/license_server.py create-license --name "Khach A" --phone "09xxxxxxxx" --notes "..."
python server/license_server.py set-config VAF-XXXX-XXXX-XXXX-XXXX --config '{"game":"645","mode":"dynamic","ticket_count":2}'

# client: activate -> today (ví dụ curl)
curl -X POST https://HOST/api/activate -H "Content-Type: application/json" \
  -d '{"license_key":"VAF-...","device_id":"<uuid>","client_info":"test"}'
curl "https://HOST/api/today?license_key=VAF-...&device_id=<uuid>&device_secret=<secret>"
```

(Chạy server sau HTTPS/reverse proxy, đặt `ADMIN_TOKEN` mạnh; không dùng HTTP trần trên Internet.)
