# Bảo mật, phân phối & cấp phép (quyết định chính thức)

Tài liệu này là quyết định kiến trúc/chính sách để bảo vệ mã nguồn, thuật toán và doanh thu. Áp dụng cho toàn bộ dự án `vietlott-quant-auto`.

## 1. Phân loại repo & công khai

**Nguyên tắc:** tách "bề mặt bán hàng" khỏi "lõi vận hành/cấp phép".

| Thành phần | Mức độ | Ghi chú |
|---|---|---|
| `landing/` (site tĩnh marketing) | **Có thể PUBLIC** | Chỉ HTML/CSS/JS/asset chính thức, `CONFIG` placeholder. Không chứa lệnh SMS, license, secret, mã engine, dữ liệu khách. Triển khai từ thư mục `landing/` (GitHub Pages/Netlify/Vercel/hosting tĩnh) — có thể dùng repo public riêng chỉ chứa nội dung `landing/`. |
| `quant_engine.py`, `backtest_optimizer.py`, `data_sync.py` | **PRIVATE (IP lõi)** | Thuật toán/AI tính toán & gợi ý bộ số tối ưu — không công khai. |
| `cloud_daily_runner.py`, `.github/workflows/*`, script vận hành | **PRIVATE** | Sinh lệnh/cấu hình; không phát hành đầu ra cho người chưa mua. |
| `auto_agent_buy.py`, `iphone_automation_server.py`, `pc_sms_sender.py`, `install_phonelink.py`, `BAT_PHONE_LINK.bat` | **PRIVATE** | Chi tiết triển khai/tự động hóa nội bộ. |
| `server/` (cấp phép & phân phối), DB/license, secret | **PRIVATE** | Gắn thiết bị, cấp lệnh theo quyền. Không commit `.env`, DB thật, khóa bí mật. |
| `data/*.jsonl` lịch sử quay số, `data/*.db` | **PRIVATE** (khuyến nghị) | Dữ liệu vận hành; DB vé/khách tuyệt đối không công khai. |
| `public/today_sms.txt`, `public/today_report.json` (lệnh/ngày) | **TUYỆT ĐỐI KHÔNG PUBLIC** | Lệnh SMS gửi 9969 là giá trị sử dụng trực tiếp. **Không** commit/push ra repo công khai, **không** phục vụ qua URL raw công khai. Chỉ phát qua API có xác thực, gắn đúng thiết bị/khách. |
| API key, webhook SePay, admin secret, signing key | **SECRET** | Lưu biến môi trường/secret manager (GitHub Secrets, `.env` không commit). |

**Quyết định cho repo hiện tại (`proboy172/vietlott-quant-auto`):** coi là **PRIVATE core repo**. Nếu cần public landing, chỉ export/push nội dung `landing/` sang repo/nhánh public chuyên dụng; tuyệt đối không đưa engine, server, lệnh, secret sang đó. (Việc đổi visibility GitHub thực hiện trên GitHub.)

## 2. Mô hình cấp phép & 1 gói = 1 thiết bị

- **1 license = 1 gói = 1 khách hàng = 1 số điện thoại Vietlott SMS = 1 thiết bị đang hoạt động** tại một thời điểm.
- Quyền sử dụng công cụ (AI gợi ý/cấu hình/lệnh/cập nhật) gắn với license và **thiết bị đã kích hoạt**. Không dùng chung, không chuyển nhượng, không cho mượn.
- Kích hoạt lần đầu: client (iPhone Shortcut/Android) sinh `device_id` (UUID/token cài đặt) lưu cục bộ, gửi kèm `license_key` tới server → server gắn (bind) nếu slot trống và trả `device_secret` (hoặc xác nhận). Các lần lấy lệnh sau phải gửi `license_key` + `device_secret` (và/hoặc `device_id` đúng hash) → server chỉ trả dữ liệu khi khớp thiết bị active.
- **Không** chạy thuật toán lõi hay phát feed lệnh chung ở client/file công khai. Client là "thin client" gọi API.

## 3. Chống phát tán / dùng chùa

- **Ngừng phát lệnh qua file công khai:** không dùng `today_sms.txt` trên GitHub raw/public. Phân phối qua `GET/POST /api/today` có xác thực.
- Lệnh/cấu hình trả về **chỉ cho thiết bị đã bind** của license hợp lệ, trạng thái active. Sai/thiếu/không khớp → từ chối.
- Chia sẻ Shortcut/app: vô nghĩa nếu không có `device_secret` hợp lệ gắn với máy đó (và máy đó phải là máy đang active). Copy sang máy khác → không khớp binding → từ chối.
- Chống chia sẻ cùng license: 1 slot thiết bị; theo dõi bất thường (nhiều device_id/IP/lỗi kích hoạt liên tục, tần suất rebind cao) → cảnh báo/khóa tạm, yêu cầu hỗ trợ.
- Ghi log truy cập/cấp phát (thời gian, license, device hash) để đối soát.
- Kèm chính sách: 1 gói/1 máy/1 SĐT, cấm chia sẻ; vi phạm có quyền tạm ngưng dịch vụ.

## 4. Đổi máy (rebind) — phí & hạn chế

**Chính sách (công bố rõ cho khách):**

- Mỗi gói gắn **1 thiết bị** tại một thời điểm.
- **Đổi thiết bị** (nâng cấp/mất máy/cài lại mất token): thu **phí 150.000đ mỗi lần đổi**. Hỗ trợ khi có nhu cầu hợp lệ.
- **Quy trình:** khách liên hệ hỗ trợ (Zalo), cung cấp thông tin đối soát (SĐT Vietlott SMS đã đăng ký, họ tên/mã đơn, mã giao dịch phí đổi 150.000đ, lý do) → xác minh → **thu hồi/vô hiệu thiết bị cũ ngay** → mở kích hoạt thiết bị mới (trong cửa sổ/cơ chế rebind) → khách kích hoạt trên máy mới.
- **Hạn chế lạm dụng (bắt buộc):**
  - **Cooldown tối thiểu 30 ngày** giữa 2 lần đổi thiết bị (trừ trường hợp đặc biệt được xác minh và duyệt thủ công).
  - Mỗi lần đổi phải có xác minh + ghi nhận phí/mã giao dịch (audit log). Tần suất bất thường (đổi liên tục, dấu hiệu cho mượn/chuyển nhượng) → từ chối hoặc tạm khóa chờ rà soát.
  - Thiết bị cũ bị thu hồi không sử dụng tiếp được.
- Triển khai kỹ thuật: bảng `licenses`, `device_bindings` (device_hash, active, activated_at, revoked_at), `rebinds` (fee_vnd, paid_ref, created_at, cooldown_until/notes); endpoint/CLI `rebind` kiểm tra cooldown & ghi log.

> Ghi chú vận hành: đây là chính sách mặc định bảo vệ doanh thu; admin có thể xử lý ngoại lệ có kiểm soát (ghi rõ lý do) nhưng không làm mất cơ chế ràng buộc.

## 5. Kiến trúc phân phối an toàn (mục tiêu)

1. **Repo/CI private** chạy engine + runner, không commit lệnh ra nơi công khai. (Artifact CI chỉ nội bộ nếu cần.)
2. **License/Delivery server (private)**: cấp license khi thanh toán, kích hoạt gắn máy, trả `today` theo license+device, rebind có phí.
3. **Client (Shortcut/Android)**: lưu `license_key` + `device_secret`/`device_id`, gọi API; hiển thị rõ cách tạm dừng tự động (quyền của khách) nhưng không cấp dữ liệu khi chưa được ủy quyền.
4. **Thanh toán (SePay/webhook)**: đối soát tự động → tạo/active license (tương lai). Hiện tại có thể cấp thủ công qua admin CLI, vẫn giữ ràng buộc thiết bị.

## 6. Hiện trạng & việc cần làm tiếp (kỹ thuật)

- Đã có scaffold `server/license_server.py` (SQLite, stdlib) cho activate/today/rebind/admin CLI và chính sách cooldown/phí — cần triển khai lên môi trường chạy thực (HTTPS, reverse proxy, backup DB), tích hợp thanh toán và cấu hình per-user đầy đủ.
- Cần chuyển Shortcut/Android sang gọi API thay vì đọc raw `today_sms.txt` công khai; cấu hình URL server khi triển khai.
- Landing phải luôn nêu rõ: 1 gói/1 máy/1 SĐT Vietlott SMS, đổi máy 150.000đ/lần + xác minh + cooldown/hạn chế, không chia sẻ; công cụ không bán vé/không đảm bảo trúng.
