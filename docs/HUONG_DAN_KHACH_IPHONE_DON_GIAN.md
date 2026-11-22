# Hướng dẫn nhanh cho khách iPhone (2-3 bước, ~5 phút, làm 1 lần)

Dành cho khách không rành công nghệ/người lớn tuổi. Hỗ trợ có thể **cài giúp 1 lần** (trực tiếp hoặc qua Zalo/video call) — sau đó máy tự chạy, khách gần như không cần làm gì thêm.

> **Thông tin gói (demo hiện tại)**
> - **Địa chỉ hệ thống (SERVER_URL):** `https://aivietlott.jbai.vn`
> - **Mã kích hoạt:** `VAF-F593-EB89-3453-EB4A`
> - **Số Vietlott SMS (SIM trên iPhone gửi tin):** `0906919053`
> - **Gói:** Mega 6/45 (`645`), AI gợi ý, 2 vé/ngày quay. Tin gửi tới **9969** từ đúng số `0906919053`.
>
> **Quan trọng:** 1 gói = 1 khách = 1 SĐT Vietlott SMS = 1 thiết bị. Không chia sẻ mã/phím tắt đã kích hoạt. Công cụ hỗ trợ gửi SMS, **không bán vé/mua hộ, không đảm bảo trúng**. Phí/vé (nếu Vietlott nhận) do Vietlott thu. Bạn luôn có quyền tạm dừng/bật lại.

## Khách cần chuẩn bị (trước khi cài)
- iPhone có **SIM 0906919053** đã đăng ký Vietlott SMS, có tài khoản/thẻ thanh toán mặc định và **đủ số dư/hạn mức**.
- iPhone có mạng (Internet), có app **Phím tắt (Shortcuts)**.
- Cần **link Phím tắt iCloud chính thức** do hỗ trợ gửi (kênh riêng). *Hiện link này do vận hành tạo/cấp; chưa có sẵn trong kho mã.*

---

## 3 bước (làm 1 lần) — nên có hỗ trợ thao tác cùng

### Bước 1 — Thêm Phím tắt (10 giây)
- Mở **link Phím tắt** do hỗ trợ gửi trên iPhone → chạm **Thêm phím tắt (Add Shortcut)**.
  - *Chỉ dùng link do hỗ trợ chính thức cung cấp. Nếu iOS hỏi, cho phép thêm.*

### Bước 2 — Bật lần đầu & cấp quyền (1 lần)
- Mở app **Phím tắt** → bấm chạy **“Vietlott Auto”** (hoặc tên phím tắt hỗ trợ cung cấp).
- Nếu được hỏi **mã kích hoạt**, nhập/dán: `VAF-F593-EB89-3453-EB4A` (hỗ trợ có thể dán giúp).
- Khi iPhone hiện câu hỏi xin quyền (truy cập mạng, lưu tệp, **gửi tin nhắn**), bấm **Cho phép/OK** cho các lần hỏi.
- Chờ thấy thông báo **kích hoạt/thành công** hoặc thông báo trạng thái.
  - *Đây là lúc gắn gói với đúng iPhone này. Mã bảo mật thiết bị được lưu riêng trên máy — không chia sẻ.*

### Bước 3 — Cho máy tự chạy hằng ngày (1 lần)
- Vào **Phím tắt → Tự động hóa (Automation) → + → Tạo tự động hóa cá nhân**.
- Chọn **Thời gian trong ngày**: đặt giờ **trước giờ chốt** (theo hỗ trợ hướng dẫn), lặp **Hằng ngày**.
- Hành động: **Chạy phím tắt** → chọn **“Vietlott Auto”**.
- Bật **Chạy ngay lập tức** (nếu có) → **Xong**.
  - *Hỗ trợ/người thân có thể làm giúp bước này.*

**Xong.** Sau đó máy tự chạy: ngày có lệnh sẽ gửi tin (ví dụ `645 K1 S ...`) tới **9969**; ngày nghỉ/không có lệnh sẽ không gửi (bình thường). Cần iPhone bật, có mạng, SIM `0906919053` hoạt động và đủ số dư/hạn mức.

> **Tạm dừng/bật lại:** vào **Phím tắt → Tự động hóa** → tắt hoặc bật lại tự động hóa bất cứ lúc nào (tắt = không gửi lệnh).

---

## Nếu gặp lỗi
| Thông báo | Cách xử lý |
|---|---|
| `another_device_active` (đã có thiết bị khác) | Liên hệ hỗ trợ **đổi máy** (150.000đ/lần, xác minh + mã GD, thu hồi máy cũ ngay, cooldown 30 ngày) rồi chạy lại. |
| `device_not_active` / `invalid_device_secret` | Liên hệ hỗ trợ (có thể cần kích hoạt lại sau khi xử lý). |
| License tạm ngưng/thu hồi/hết hiệu lực | Liên hệ hỗ trợ kiểm tra gói. |
| Không có mạng / lỗi kết nối | Kiểm tra Internet và địa chỉ `https://aivietlott.jbai.vn`. |
| Gửi 9969 nhưng Vietlott không nhận/phản hồi | Kiểm tra: đúng số `0906919053` đã đăng ký Vietlott SMS, tài khoản/thẻ mặc định, đủ số dư/hạn mức, trong giờ nhận. |

**Hỗ trợ Zalo:** https://zalo.me/0899963938

---

## Ghi chú cho vận hành (để khách chỉ cần 2-3 bước)
- **Chuẩn bị 1 lần:** tạo **một Phím tắt gộp** (template) trên iPhone với `SERVER_URL` điền sẵn `https://aivietlott.jbai.vn`, luồng: đọc/lưu `vietlott_device.json` → nếu chưa có secret thì hỏi `license_key` 1 lần và gọi `POST /api/activate` (lưu `device_id/device_secret/license_key`) → gọi `POST /api/today` → nếu `ACTIVE_BUY` thì gửi từng `sms_commands` tới `9969` (nghỉ/không có lệnh thì báo và dừng) → **chia sẻ link iCloud** cho khách (qua kênh riêng). Chi tiết kỹ thuật: `docs/CLIENT_INTEGRATION.md`.
- **Cài hộ:** hỗ trợ/người thân thực hiện 3 bước trên cùng khách (~5 phút). Với người lớn tuổi, đây là cách thực tế nhất (khách không tự thao tác kỹ thuật).
- **Lưu ý iOS:** iPhone vẫn bắt buộc hỏi quyền (mạng/tệp/gửi SMS) và cần tạo Tự động hóa 1 lần; tuỳ phiên bản iOS/cài đặt, chạy tự động gửi SMS có thể cần xác nhận — nên test trên máy khách. Kiểm tra máy 2 SIM gửi đúng số `0906919053`.
- Xem thêm hướng dẫn chi tiết & xử lý lỗi: `docs/HUONG_DAN_KHACH_IPHONE.md`, `docs/CLIENT_INTEGRATION.md`.