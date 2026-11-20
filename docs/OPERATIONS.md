# Vận hành: bảo mật, cấp phép & đổi máy (runbook)

Tài liệu này dành cho chủ sở hữu/vận hành. Mục tiêu: chạy dịch vụ **an toàn, 1 gói = 1 khách = 1 SĐT Vietlott SMS = 1 thiết bị active**, không phát lệnh công khai.

> Repo core nên **PRIVATE**. Landing (nếu public) phải tách/deploy riêng chỉ từ `landing/`. Không commit `server/licenses.db`, `.env`, secret, hay output `out/`.

## 1) Bảo mật & trạng thái hiện tại (đã thực hiện trong repo)

- [x] Ngừng phát lệnh/cấu hình hằng ngày ra file/URL công khai: output private `out/` (gitignored), `cloud_daily_runner`/`auto_agent_buy` không publish; workflow chỉ generate + upload artifact nội bộ (không commit/push lệnh). `public/today_sms.txt`, `public/today_report.json` đã bị gỡ khỏi HEAD và **xóa khỏi lịch sử git** (đã force-push).
- [x] Hardening `.gitignore` (ignore `out/`, file lệnh public, `server/*.db`, `.env*`, log…).
- [x] `server/license_server.py`: cấp phép **1 license → tối đa 1 thiết bị active**, `/api/today` chỉ trả plan cho thiết bị bind hợp lệ, sinh plan server-side (hỗ trợ per-khách qua `config_json`), **rebind 150.000đ/lần**, thu hồi máy cũ ngay, **cooldown 30 ngày**, audit `rebinds`/`access_logs`.
- [x] Tài liệu: `docs/SECURITY_LICENSING.md`, `docs/CLIENT_INTEGRATION.md`, `server/README.md`.

**Cần bạn đảm bảo ở hạ tầng/GitHub (ngoài mã):** repo core đặt **Private**; xử lý rủi ro cache/fork/clone cũ (không kiểm soát được bên ngoài); triển khai server sau HTTPS; quản lý secret/backup.

## 2) Triển khai server (production)

1. **Máy chủ/VPS** (Linux khuyến nghị), Python 3.10+ (chỉ thư viện chuẩn). Chạy từ thư mục gốc repo (để import `cloud_daily_runner`/engine):  
   - `python server/license_server.py init-db`
2. **Secret & cấu hình (env, không commit):**
   - `ADMIN_TOKEN` = chuỗi ngẫu nhiên đủ mạnh (bắt buộc cho admin API/CLI khi dùng API). Ví dụ PowerShell: `$env:ADMIN_TOKEN="..."` / Linux: `export ADMIN_TOKEN=...`
   - `LICENSE_DB_PATH` (tuỳ chọn, mặc định `server/licenses.db`), `LICENSE_SERVER_HOST`/`LICENSE_SERVER_PORT` (tuỳ chọn). Xem `server/.env.example`.
3. **HTTPS (bắt buộc khi public Internet):** đặt sau reverse proxy (Nginx/Caddy/Cloudflare Tunnel) terminate TLS, chỉ forward tới `127.0.0.1:8787`. **Không** public HTTP trần. Giới hạn rate-limit, chặn brute-force, bật log truy cập.
4. **Chạy dịch vụ:** `python server/license_server.py serve --host 127.0.0.1 --port 8787` (qua systemd/supervisor/container tuỳ hạ tầng). Kiểm tra `GET /healthz` và `show-policy`.
5. **Dữ liệu & backup:** `licenses.db` (và WAL/shm nếu có) là **private/tuyệt mật** — phân quyền chặt, **backup định kỳ**, mã hóa/giữ an toàn bản sao. Không đưa DB lên git/public.
6. **Giám sát:** theo dõi `access_logs` (qua DB) để phát hiện kích hoạt/gọi API bất thường, nhiều thất bại `another_device_active`/`invalid_device_secret` → tạm khóa/điều tra.

## 3) Cấp license & cá nhân hóa (1 gói/1 khách/1 SĐT/1 thiết bị)

```bash
# Tạo license
python server/license_server.py create-license --name "Khach A" --phone "09xxxxxxxx" --notes "don 999k, maGD ..."

# Cập nhật hồ sơ (SĐT Vietlott SMS thực tế, ghi chú/Zalo/mã GD...)
python server/license_server.py update-license VAF-... --phone "09xxxxxxxx" --notes "Zalo ..., maGD ..."

# Cá nhân hóa per-khách (config_json) — plan sinh server-side khi /api/today
# game: "645" (Mega 6/45), "655" (Power 6/55), "auto" (theo lịch ngày)
# mode: "dynamic" (AI), "1"/"2"/"3" (AI cố định số vé), "custom" (bộ số khách chọn)
python server/license_server.py set-config VAF-... --config '{"game":"645","mode":"dynamic","ticket_count":2}'

# Bộ số khách tự chọn (đúng các bộ này, tối đa theo ticket_count)
python server/license_server.py set-config VAF-... --config '{"game":"645","mode":"custom","custom_tickets":[[1,2,3,4,5,6],[7,8,9,10,11,12]]}'

# Quản lý
python server/license_server.py list
python server/license_server.py set-status VAF-... suspended|active|revoked|expired
```

- Cung cấp cho khách (kênh riêng tư): `SERVER_URL` (HTTPS) + `license_key` + hướng dẫn kích hoạt/tạm dừng (xem `docs/CLIENT_INTEGRATION.md`).
- Admin API (header `X-Admin-Token`): `/api/admin/create-license`, `/api/admin/update-license`, `/api/admin/set-config`, `/api/admin/set-status`, `/api/admin/rebind`, `/api/admin/licenses`.
- Chưa tích hợp Zalo OA/bot tự động; CSKH thủ công theo mẫu: [`docs/ZALO_CSKH_TEMPLATES.md`](../docs/ZALO_CSKH_TEMPLATES.md). Gửi `license_key`/hướng dẫn qua kênh riêng tư, chỉ sau khi đối soát thanh toán.

## 4) Kích hoạt thiết bị & phân phối (chặn dùng chùa)

- Client (Shortcut iPhone / Android thin client) **phải**: sinh+lưu `device_id` → `POST /api/activate` nhận+lưu `device_secret` (1 lần) → gọi `/api/today` với `license_key+device_id+device_secret` để lấy `sms_commands`, gửi tới **9969** từ **chính SĐT Vietlott SMS đã đăng ký** của khách. Không đọc file/URL công khai. Chi tiết: `docs/CLIENT_INTEGRATION.md`.
- Lỗi `another_device_active`: đã bind máy khác → đi theo quy trình **đổi máy** (mục 5), không tự cấp máy thứ hai.
- **Hệ quả khi repo private/chặn kênh công khai:** client/Shortcut cũ dựa trên raw file public sẽ ngừng nhận lệnh — cần cập nhật sang API per-device cho khách trả phí.

## 5) Đổi thiết bị (rebind) — 150.000đ/lần, kiểm soát

- **Phí:** 150.000đ **mỗi lần đổi**. Yêu cầu **xác minh** (SĐT Vietlott SMS/mã license/đơn, lý do) + **mã giao dịch/biên nhận** phí.
- **Thực hiện:** thu hồi/vô hiệu **máy cũ ngay**, mở slot cho máy mới, ghi nhận `rebinds` (paid_ref, lý do, thời điểm), áp **cooldown 30 ngày**:
```bash
python server/license_server.py rebind VAF-XXXX-XXXX-XXXX-XXXX \
  --paid-ref "MA_GD_SEPAY" --reason "doi may" --admin-note "da xac minh"
# (override cooldown chỉ khi thực sự cần, có kiểm soát: --force)
```
- Sau rebind khách chạy lại **activate** trên máy mới để nhận `device_secret` mới. Máy cũ không truy cập được nữa.
- **Chống lạm dụng:** từ chối/tạm khóa nếu đổi liên tục, dấu hiệu cho mượn/chuyển nhượng, hoặc không xác minh/không thu phí đúng.

## 6) Thanh toán & tự động hóa (bước tiếp theo, chưa tích hợp)

- Nối SePay/webhook (hoặc cổng bạn dùng) để: đối soát → `create-license`/`set-status active`/ghi nhận phí và (tuỳ chọn) kích hoạt tự động; ghi nhận `--paid-ref` khi rebind. Hiện hệ thống hỗ trợ **thủ công an toàn** qua CLI/API admin.
- Điền thông tin thật (Zalo, SePay QR/ngân hàng, contact, link cài đặt, domain) trong `landing/site.js` `CONFIG` khi sẵn sàng; deploy landing tách riêng nếu public.

## 7) Tuân thủ & điều kiện Vietlott SMS (nhắc khi hỗ trợ)

- Công cụ **không bán vé, không mua hộ, không giữ tiền, không đảm bảo trúng** (xổ số ngẫu nhiên). Tiền vé (nếu gửi thành công) do Vietlott trừ từ tài khoản Vietlott SMS của khách.
- Khách cần: đúng SĐT đã đăng ký Vietlott SMS, tài khoản/thẻ thanh toán mặc định, đủ số dư/hạn mức, trong giờ nhận lệnh, cú pháp đúng, bật quyền/tự động hóa; gửi tới **9969** từ đúng số khách. Thiếu điều kiện Vietlott có thể không nhận lệnh.
- Khách luôn có quyền **tạm dừng/bật tắt** tự động bất cứ lúc nào.
- 1 gói/1 khách/1 SĐT Vietlott SMS/1 thiết bị; **không chia sẻ/chuyển nhượng**. Đổi máy **150.000đ/lần**, xác minh, thu hồi máy cũ, cooldown/giới hạn — nêu rõ trên landing/điều khoản khi trao đổi với khách.
