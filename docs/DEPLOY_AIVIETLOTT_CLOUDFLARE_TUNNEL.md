# Triển khai tiết kiệm (Phương án A): `aivietlott.jbai.vn` + Cloudflare Tunnel

Hướng dẫn này giúp bạn có **`SERVER_URL = https://aivietlott.jbai.vn`** cho API cấp phép/phân phối (`server/license_server.py`) mà **không cần thuê VPS**: chạy server trên **máy của bạn (luôn bật 24/7)** và publish ra Internet an toàn bằng **Cloudflare Tunnel** (HTTPS do Cloudflare cung cấp).

> **Phạm vi:** server API (Python, SQLite `server/licenses.db`, per-device). Landing tĩnh (`landing/`) nếu public thì deploy riêng (Cloudflare Pages/GitHub Pages/hosting tĩnh) — không thay thế API này.

## 0) Kết luận nhanh

- **Có tự chạy trên GitHub được không?** Không. GitHub Actions/Pages/Codespaces không phải dịch vụ chạy API Python + SQLite liên tục, public 24/7 cho iPhone gọi `/api/activate`, `/api/today`. Repo có workflow sinh dữ liệu nội bộ, nhưng **không host được license server**.
- **Chỉ cần subdomain?** Có: `aivietlott.jbai.vn` là đủ.
- **“Hosting” nào phù hợp?** Phải là nơi chạy được **Python process liên tục + lưu DB bền vững**. Phương án A dùng **máy của bạn** làm host + **Cloudflare Tunnel** làm kênh HTTPS (chi phí hạ tầng thêm ~0 ngoài tên miền/máy sẵn có). Hosting tĩnh/shared PHP không chạy được API này.
- **Cloudflare:** dùng tốt cho DNS/HTTPS/Tunnel/bảo vệ (rate-limit/WAF). Nên dùng.
- **Supabase:** không bắt buộc và **không thay trực tiếp** hiện trạng (đang dùng SQLite + logic Python trong repo). Chỉ cân nhắc nếu tự refactor lớn sang Postgres + nơi chạy API tương ứng.

## 1) Yêu cầu

- Tên miền `jbai.vn` đã quản lý DNS trên **Cloudflare** (khuyến nghị để dùng Tunnel dễ nhất). Subdomain dùng: `aivietlott.jbai.vn`.
- **Một máy chạy 24/7**, Internet ổn định (Windows PC của bạn là được), không sleep/hibernate làm mất mạng.
- **Python 3.10+** (repo đã chạy trên Windows). Repo đặt tại ví dụ `D:\Du An Code\vietlott-quant-auto`.
- Quyền cài **`cloudflared`** và tạo Tunnel trên tài khoản Cloudflare.
- (Tuỳ chọn nhưng khuyến nghị) Cloudflare bảo vệ endpoint (rate-limit/WAF) và kế hoạch **backup** `server/licenses.db`.

## 2) Chuẩn bị & chạy license server (local, `127.0.0.1`)

> Chạy từ thư mục gốc repo để import đúng `cloud_daily_runner`/engine.

```powershell
cd "D:\Du An Code\vietlott-quant-auto"

# 1) Khởi tạo DB (nếu chưa)
python server\license_server.py init-db

# 2) Đặt secret (KHÔNG commit). Có thể copy server\.env.example -> server\.env (private) hoặc set env:
$env:ADMIN_TOKEN = "<chuoi-ngau-nhien-manh>"
$env:LICENSE_SERVER_HOST = "127.0.0.1"
$env:LICENSE_SERVER_PORT = "8787"
# $env:LICENSE_DB_PATH = "D:\Du An Code\vietlott-quant-auto\server\licenses.db"  # tuỳ chọn

# 3) Chạy thử
python server\license_server.py serve --host 127.0.0.1 --port 8787
```

Kiểm tra (cửa sổ/terminal khác): mở `http://127.0.0.1:8787/healthz` phải trả `{"ok": true, ...}`. Tắt server thử sau khi OK.

- **DB:** mặc định `server\licenses.db` (gitignored) chứa license, thiết bị active, hash secret, rebind, access log — **private, backup định kỳ, phân quyền chặt**.
- **ADMIN_TOKEN:** bắt buộc cho admin API/CLI qua API; giữ bí mật.
- Script hỗ trợ (Windows): `server\deploy\run-license-server.ps1` (set env `ADMIN_TOKEN` trước khi chạy).

## 3) Cài `cloudflared` (Windows)

- Tải/cài theo hướng dẫn chính thức: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  - Ví dụ (nếu có winget): `winget install --id Cloudflare.cloudflared`
- Kiểm tra: `cloudflared --version`
- Đảm bảo `jbai.vn` đang được quản lý DNS bởi Cloudflare (nameserver Cloudflare).

## 4) Tạo Tunnel và trỏ DNS `aivietlott.jbai.vn`

Chạy trong PowerShell/cmd:

```powershell
# Đăng nhập (mở trình duyệt, chọn zone jbai.vn)
cloudflared tunnel login

# Tạo tunnel (tên gợi ý: aivietlott). Lưu lại Tunnel ID/UUID và file credentials JSON được tạo.
cloudflared tunnel create aivietlott

# Tạo bản ghi DNS cho subdomain (trỏ aivietlott.jbai.vn tới tunnel)
cloudflared tunnel route dns aivietlott aivietlott.jbai.vn
```

- File credentials thường nằm tại `%USERPROFILE%\.cloudflared\<TUNNEL-ID>.json`.
- `tunnel route dns` sẽ tạo/cập nhật bản ghi DNS tương ứng trên Cloudflare.

## 5) Cấu hình và chạy Tunnel

Tạo file cấu hình (ví dụ copy từ `server\deploy\cloudflared-config.aivietlott.yml.example` thành `%USERPROFILE%\.cloudflared\config.yml` hoặc một đường dẫn bạn chọn) và điền đúng `tunnel` (ID hoặc tên) và `credentials-file`:

```yaml
tunnel: <TUNNEL-UUID-hoặc-aivietlott>
credentials-file: C:\Users\<USER>\.cloudflared\<TUNNEL-UUID>.json

ingress:
  - hostname: aivietlott.jbai.vn
    service: http://127.0.0.1:8787
  - service: http_status:404
```

Chạy thử (trong khi license server đang chạy trên `127.0.0.1:8787`):

```powershell
cloudflared tunnel --config "%USERPROFILE%\.cloudflared\config.yml" run aivietlott
```

Mở trình duyệt: `https://aivietlott.jbai.vn/healthz` phải trả JSON `ok: true`. Khi đó:

- **`SERVER_URL = https://aivietlott.jbai.vn`**

> Không cần mở port 8787 (hay port nào khác) ra Internet/router; kết nối đi ra từ `cloudflared` tới Cloudflare.

## 6) Chạy như dịch vụ/24-7 (sau khi test OK)

Cần **cả hai** chạy ổn định và tự khởi động lại:

1. **License server (Python)**
   - Chạy nền qua **Task Scheduler** (At startup / At logon) hoặc công cụ như NSSM/WinSW để chạy:
     - Program: `python` (hoặc đường dẫn đầy đủ, vd `C:\Python314\python.exe`)
     - Args: `server\license_server.py serve --host 127.0.0.1 --port 8787`
     - Working dir: `D:\Du An Code\vietlott-quant-auto`
     - Env: `ADMIN_TOKEN` (và các biến cần thiết) — đặt an toàn, không hardcode vào repo.
   - Mẫu lệnh/tham khảo: `server\deploy\run-license-server.ps1`.
   - Đảm bảo máy không sleep/hibernate; tài khoản chạy có quyền đọc repo và ghi `server\licenses.db`.

2. **Cloudflared tunnel**
   - Cài chạy như service (Windows): `cloudflared service install` (tham khảo tài liệu Cloudflare cho cú pháp/config path tương ứng phiên bản), hoặc tạo Scheduled Task chạy `cloudflared tunnel --config ... run aivietlott` khi khởi động.
   - Kiểm tra sau reboot: cả service Python và tunnel đều lên, `https://aivietlott.jbai.vn/healthz` vẫn OK.

## 7) Cấu hình sau triển khai (vận hành)

- **Cấp/cấu hình license (admin, trên máy chủ):**
  - `python server\license_server.py create-license --name "..." --phone "<SĐT_Vietlott_SMS>" --notes "..."`
  - `python server\license_server.py update-license VAF-... --phone "..." --notes "..."`
  - `python server\license_server.py set-config VAF-... --config "{\"game\":\"645\",\"mode\":\"dynamic\",\"ticket_count\":2}"`
  - `python server\license_server.py list` (dùng `$env:PYTHONIOENCODING='utf-8'` nếu terminal Windows gặp lỗi hiển thị tiếng Việt).
- **Gửi khách (kênh riêng tư, vd Zalo):** `SERVER_URL = https://aivietlott.jbai.vn`, `license_key`, link Phím tắt iCloud chính thức và hướng dẫn:
  - `docs/HUONG_DAN_KHACH_IPHONE.md`, `docs/CLIENT_INTEGRATION.md`, mẫu tin: `docs/ZALO_CSKH_TEMPLATES.md`.
- **Đổi máy (rebind):** 150.000đ/lần, xác minh + mã GD, thu hồi máy cũ ngay, cooldown 30 ngày — `rebind` CLI/API (xem `docs/OPERATIONS.md`).
- **Bảo vệ & giám sát:** bật rate-limit/WAF trên Cloudflare cho `/api/*` nếu cần; theo dõi `access_logs` (DB); **backup thường xuyên** `server/licenses.db`.
- **Kiểm tra end-to-end:** tạo/cấu hình license → trên iPhone (SIM SĐT Vietlott SMS đúng) chạy Kích hoạt với `SERVER_URL` + `license_key` → gọi “Gửi vé hôm nay”/bật Tự động hóa; xác nhận `active_devices = 1` (`python server\license_server.py list`).

## 8) Lưu ý quan trọng

- **GitHub:** dùng để lưu code/workflow nội bộ; **không** dùng để host API này.
- **Supabase:** không thay thế trực tiếp kiến trúc SQLite + Python hiện tại; chỉ xem xét khi có kế hoạch refactor.
- **Bảo mật:** không commit `.env`, `licenses.db`, secret, hay nội dung lệnh SMS; chỉ gửi `license_key`/`SERVER_URL` qua kênh riêng tư. Không mở public port 8787.
- **Độ sẵn sàng:** nếu máy tắt/mất điện/mất mạng, API ngừng hoạt động (khách không kích hoạt/lấy lệnh được) — vì vậy cần máy ổn định và kế hoạch backup/khôi phục.
- **Tuân thủ:** công cụ hỗ trợ gửi SMS tới 9969 (từ đúng SĐT Vietlott SMS đã đăng ký), không bán vé/mua hộ, không đảm bảo trúng; khách có quyền tạm dừng/bật tắt.

## 9) Liên quan trong repo

- `docs/OPERATIONS.md` — runbook vận hành, bảo mật, đổi máy.
- `server/README.md`, `server/.env.example`, `server/deploy/*` (Caddy/Nginx/systemd mẫu, cloudflared config mẫu, script chạy Windows).
- `docs/CLIENT_INTEGRATION.md`, `docs/HUONG_DAN_KHACH_IPHONE.md`, `docs/ZALO_CSKH_TEMPLATES.md`.


## 10) Landing public cùng tunnel (đã triển khai)

Ngoài API `aivietlott.jbai.vn`, tunnel `aivietlott` còn phục vụ landing tĩnh:

1. Static server local (chỉ lắng nghe `127.0.0.1`):
   ```powershell
   python -m http.server 8090 --bind 127.0.0.1 --directory "D:\Du An Code\vietlott-quant-auto\landing"
   ```
2. DNS: `cloudflared tunnel route dns aivietlott landing.jbai.vn`
3. Thêm ingress vào `%USERPROFILE%\.cloudflared\config.yml` (trước rule `http_status:404`):
   ```yaml
     - hostname: aivietlott.jbai.vn
       service: http://127.0.0.1:8787
     - hostname: landing.jbai.vn
       service: http://127.0.0.1:8090
     - service: http_status:404
   ```
4. Restart tunnel task (`Stop-ScheduledTask`/`Start-ScheduledTask -TaskName VietlottCloudflaredTunnel`).
5. Kiểm tra: `https://landing.jbai.vn/` (HTML landing) và `https://aivietlott.jbai.vn/healthz` (`ok: true`).

**Khởi động tự động khi login (không cần admin):** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VietlottAutoFlow.bat` — kiểm tra cổng 8787/8090 và tiến trình cloudflared trước khi start (tránh trùng). Nếu Task Scheduler từ chối đăng ký (Access denied), dùng file Startup này.

**SEO/liên kết:** canonical + Open Graph trỏ `https://landing.jbai.vn/`; có `robots.txt`, `sitemap.xml`, `assets/favicon.svg`. Khi đổi domain phải sửa cả 4 nơi + tăng `?v=` trong `index.html`.
