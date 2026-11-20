# Bảo mật, phân phối & cấp phép (quyết định chính thức)

Tài liệu này là quyết định kiến trúc/chính sách để bảo vệ mã nguồn, thuật toán và doanh thu. Áp dụng cho toàn bộ dự án `vietlott-quant-auto`.

## 1. Phân loại repo & công khai

**Nguyên tắc:** tách "bề mặt bán hàng" khỏi "lõi vận hành/cấp phép".

| Thành phần | Mức độ | Ghi chú |
|---|---|---|
| `landing/` (site tĩnh marketing) | **CÓ THỂ PUBLIC** | Chỉ HTML/CSS/JS/asset chính thức, `CONFIG` placeholder. Không chứa lệnh SMS, license, secret, mã engine, dữ liệu khách. Triển khai từ thư mục `landing/` (GitHub Pages/Netlify/Vercel/hosting tĩnh) — có thể dùng repo public riêng chỉ chứa nội dung `landing/`. |
| `quant_engine.py`, `backtest_optimizer.py`, `data_sync.py` | **PRIVATE (IP lõi)** | Thuật toán/AI tính toán & gợi ý bộ số tối ưu — không công khai. |
| `cloud_daily_runner.py`, `.github/workflows/*`, script vận hành | **PRIVATE** | Sinh lệnh/cấu hình; không phát hành đầu ra cho người chưa mua. |
| `auto_agent_buy.py`, `iphone_automation_server.py`, `pc_sms_sender.py`, `install_phonelink.py`, `BAT_PHONE_LINK.bat` | **PRIVATE** | Tự động gửi/hỗ trợ cài đặt — lộ ra làm lộ cách vận hành & dễ bị tái sử dụng trái phép. |
| `server/` (license/delivery) + DB license | **PRIVATE** | Logic cấp phép, gắn thiết bị, log, webhook thanh toán. Không commit DB/secret. |
| `data/*.jsonl` (lịch sử kết quả Vietlott công khai) | **CORE/PRIVATE repo** | Dữ liệu lấy từ nguồn công khai nhưng là đầu vào vận hành; không đưa vào repo/nhánh public của landing. |
| Output hằng ngày (`out/`, lệnh/cấu hình/plan) | **KHÔNG PUBLIC** | **BỎ** phát hành lệnh SMS hằng ngày ra file/repo/URL công khai. Đầu ra phục vụ khách trả phí chỉ đi qua kênh có xác thực (API gắn thiết bị). |
| License key, cấu hình per-user, SĐT, mã giao dịch, webhook/secret | **PRIVATE/TUYỆT MẬT** | Chỉ lưu server-side an toàn; không commit vào git. |

> `public/today_sms.txt` và `public/today_report.json` (dấu vết cũ) **không được** dùng để phân phối công khai và đã được loại bỏ khỏi HEAD/lịch sử repo. Phân phối hợp lệ chỉ qua `server/` (API có xác thực, gắn thiết bị).

## 2. Mô hình cấp phép & gắn thiết bị

**Chính sách:** `1 license = 1 gói = 1 khách = 1 số Vietlott SMS = 1 thiết bị đang hoạt động` tại một thời điểm.

- **Định danh:** mỗi license gắn với (a) thông tin khách/SĐT Vietlott SMS đã xác minh và (b) đúng **một** `device_id` đang active (do client sinh/lưu cục bộ, ví dụ UUID/khóa cài đặt).
- **Kích hoạt (activate):** client gửi `license_key` + `device_id` (+ thông tin thiết bị tối thiểu). Server cấp `device_secret`/token phiên **chỉ cho thiết bị đó** nếu license hợp lệ và chưa có thiết bị active (hoặc đang trong quy trình đổi máy hợp lệ).
- **Phân phối lệnh/cấu hình:** mỗi lần lấy lệnh, client gọi API với `license_key` + `device_id` + `device_secret`; server trả lệnh/cấu hình hằng ngày **chỉ khi** khớp thiết bị active của license đó. Không trả nội dung có giá trị nếu không xác thực.
- **Ràng buộc tự nhiên:** SMS đặt vé Vietlott phải gửi tới `9969` **từ chính số Vietlott SMS đã đăng ký** của khách. Công cụ chỉ sinh/gửi lệnh cho đúng cấu hình của license; dùng số/thiết bị không khớp sẽ không hoạt động theo thiết kế Vietlott.
- **Không chia sẻ:** chia sẻ file/app/shortcut không đồng nghĩa có quyền dùng vì thiếu `device_secret` hợp lệ gắn đúng máy; cài sang máy khác (device_id khác) sẽ bị từ chối khi đã có thiết bị active.

## 3. Chống phát tán & lạm dụng

- **Không nhúng thuật toán trong client.** Client (Shortcut/Android) chỉ là "thin client": nhận lệnh/cấu hình đã cá nhân hóa từ server và thực thi gửi SMS; **không** chứa engine sinh số/lệnh, không chạy được nếu không gọi API hợp lệ.
- **Không phát lệnh công khai:** không commit/push lệnh hằng ngày ra repo; output hằng ngày ghi ra thư mục private/ignored (`out/`) hoặc chỉ tồn tại in-memory phía server.
- **Giới hạn:** tối đa 1 thiết bị active/license; rate-limit & log truy cập API (`access_logs`); phát hiện bất thường (nhiều device_id, tần suất/nguồn bất thường) để tạm khóa theo điều khoản.
- **Thu hồi:** có thể `revoke`/suspend license hoặc thu hồi thiết bị ngay (ngừng cấp lệnh) khi vi phạm/chia sẻ.
- **Tính cá nhân hóa:** `today` sinh plan **server-side** (`cloud_daily_runner.run_daily_cloud_pipeline(config=..., write_files=False)`) và **chỉ cấp cho thiết bị hợp lệ**. Hỗ trợ cá nhân hóa per-khách qua `licenses.config_json` (game/mode/số lượng/bộ số tùy chọn); có thể mở rộng thêm trường/logic theo nhu cầu vận hành.

## 4. Đổi thiết bị (rebind) — phí & kiểm soát

- **Phí:** hỗ trợ đổi/nâng cấp/mất điện thoại hoặc cài lại mất kích hoạt: **150.000đ/lần** (mỗi lần đổi), áp dụng cho mỗi lần yêu cầu chuyển thiết bị.
- **Quy trình:**
  1. Khách liên hệ hỗ trợ, cung cấp thông tin xác minh (SĐT Vietlott SMS, mã license/đơn, lý do).
  2. Xác minh hợp lệ và **thu phí 150.000đ** (ghi nhận mã giao dịch/biên nhận thanh toán).
  3. Hệ thống/nhân sự **thu hồi (revoke) thiết bị cũ ngay** → kích hoạt/bind thiết bị mới (chỉ 1 thiết bị active).
- **Hạn chế lạm dụng/mất doanh thu:**
  - **Cooldown:** tối thiểu **30 ngày** giữa 2 lần đổi máy hợp lệ (trừ trường hợp đặc biệt được duyệt thủ công, có ghi chú/log).
  - Mỗi lần đổi phải gắn với **mã giao dịch phí 150.000đ** và được ghi log (ai/when/thiết bị cũ→mới/lý do, `rebinds`).
  - Từ chối hoặc tạm khóa nếu có dấu hiệu cho mượn/chuyển nhượng/bán lại quyền sử dụng (đổi liên tục, nhiều người/thiết bị, hành vi bất thường).
  - Không tự phục vụ đổi máy tức thời không qua xác minh + phí.

## 5. Kiến trúc phân phối an toàn (mục tiêu & hiện trạng)

1. **Core private:** engine + runner + dữ liệu vận hành + license DB ở repo/server private. (**Đã áp dụng:** hardening, output private `out/`, không publish lệnh.)
2. **Delivery service (private):** API xác thực thiết bị → trả `plan/sms_commands` & cấu hình **chỉ** cho license+device hợp lệ (per-customer). (**Đã có scaffold:** `server/license_server.py`, DB `server/licenses.db` gitignored, per-customer `config_json`.)
3. **Client (mobile):** chỉ gọi API, lưu `device_id/secret` an toàn cục bộ, gửi SMS tới `9969` từ số Vietlott SMS của khách; tôn trọng quyền tạm dừng/bật-tắt. (**Hướng dẫn:** `docs/CLIENT_INTEGRATION.md`; cần triển khai Shortcut/app thực tế.)
4. **Thanh toán:** đối soát (SePay/webhook) → tạo/active license & ghi nhận phí đổi máy; mới cấp quyền sau khi xác minh. (**Chưa tích hợp tự động; hỗ trợ thủ công qua CLI/API admin.**)
5. **Ops:** HTTPS, secret trong env/secret manager, audit log, backup DB license, quy trình hỗ trợ/khiếu nại minh bạch. (**Cần triển khai hạ tầng production.**)

## 6. Phạm vi & tuân thủ

- Công cụ **không bán vé, không mua hộ, không giữ tiền, không đảm bảo trúng**; khách tự chịu phí SMS/vé theo Vietlott và điều kiện tài khoản Vietlott SMS (đúng SĐT đăng ký, tài khoản thanh toán, đủ số dư, trong giờ, đúng cú pháp/quyền).
- Khách luôn có quyền **tạm dừng/bật tắt** tự động bất cứ lúc nào.
- Điều khoản/landing phải phản ánh đúng chính sách: 1 gói/1 người/1 thiết bị, đổi máy 150.000đ/lần có xác minh & hạn chế, không chia sẻ/chuyển nhượng.
