# Mẫu tin nhắn CSKH qua Zalo (thủ công/bán tự động)

Tài liệu này cung cấp **mẫu tin nhắn** để hỗ trợ khách qua Zalo khi chưa tích hợp Zalo OA/bot. Gửi qua **kênh riêng tư**, chỉ sau khi khách chủ động liên hệ/đồng ý nhận thông tin.

> **Bảo mật & tuân thủ**
> - `license_key`, `device_secret`, nội dung `sms_commands` là **bí mật từng khách** — không gửi hàng loạt, không đăng công khai, không nhờ người khác chuyển tiếp.
> - Chỉ xác nhận/cấp quyền sau khi **đối soát thanh toán** hợp lệ.
> - Công cụ **không bán vé/mua hộ/giữ tiền, không đảm bảo trúng**. Khách tự chịu điều kiện/phí Vietlott SMS.
> - **1 gói = 1 khách = 1 SĐT Vietlott SMS = 1 thiết bị đang hoạt động**. Đổi máy **150.000đ/lần** (xác minh + mã GD, thu hồi máy cũ ngay, cooldown tối thiểu 30 ngày).

---

## Thông tin kênh & bản ghi demo (ví dụ nội bộ)

- **Zalo hỗ trợ chính:** `0899963938` — link: `https://zalo.me/0899963938`
**Landing công khai:** `https://landing.jbai.vn/` · **API/server (không gửi cho khách dưới dạng link tải):** `https://aivietlott.jbai.vn`
- **Khách giả định (demo):** Zalo `0899963938` — license `VAF-F593-EB89-3453-EB4A` (active, 0 thiết bị, `645`/`dynamic`/2 vé), **SĐT Vietlott SMS đã đăng ký: `0906919053`**. DB license là dữ liệu private (`server/licenses.db`).
- **Link Zalo có tin nhắn sẵn (khách chỉ cần bấm Gửi):** `https://zalo.me/0899963938?text=Xin%20chao%2C%20toi%20muon%20duoc%20cai%20ho%20goi%20Vietlott%20Auto%20Flow.%20SDT%20Vietlott%20SMS%3A%20...`
- **Zalo hỗ trợ thêm:** `https://zalo.me/0906919053` (hiện trên landing dòng “Zalo hỗ trợ thêm”; cũng là SĐT Vietlott SMS).
- **Thông tin chuyển khoản gói 999.000đ:** Vietcombank · Chi nhánh PGD Phú Thọ, TP.HCM · STK `0721000544340` · Chủ TK `Nguyễn Nhật Trường` · Nội dung `AUTOFLOW <SĐT đăng ký Vietlott SMS>`. **Chỉ xác nhận/license sau khi đối soát mã GD.**

> Khi gửi khách thật: thay `[TEN_KHACH]`, `[SERVER_URL]`, `[LICENSE_KEY]`, `[GOI_CAU_HINH]`, `[LINK_PHIM_TAT]` bằng thông tin thực.

---

## 1) Sau thanh toán — bàn giao & hướng dẫn bắt đầu (iPhone)

**Gợi ý nội dung:**

> Chào [TEN_KHACH], bên mình đã xác nhận thanh toán gói **Vietlott Auto (trọn đời 999.000đ)** của bạn. Dưới đây là thông tin kích hoạt (riêng cho bạn, vui lòng không chia sẻ):
> 
> - **SERVER_URL:** [SERVER_URL] (dạng `https://...`)
> - **Mã kích hoạt (license_key):** [LICENSE_KEY]
> - **Cấu hình gói:** [GOI_CAU_HINH] (ví dụ Mega 6/45, AI gợi ý, 2 vé/ngày quay)
> - **Link Phím tắt (iPhone/iCloud):** [LINK_PHIM_TAT] *(nếu có; nếu chưa có, hỗ trợ sẽ hướng dẫn tạo/cài)*
> 
> **Cách bắt đầu nhanh (iPhone):**
> 1. Chuẩn bị: đã đăng ký **Vietlott SMS** bằng đúng số trên iPhone, có tài khoản thanh toán mặc định và đủ số dư/hạn mức; tin sẽ gửi tới **9969** từ đúng số Vietlott SMS của bạn.
> 2. Cài Phím tắt từ link (hoặc theo hướng dẫn) → chạy phím tắt **Kích hoạt** (1 lần), nhập/dán `SERVER_URL` + `LICENSE_KEY`, cấp quyền khi iOS hỏi.
> 3. Chạy thử **Gửi vé Vietlott hôm nay** và cấp quyền gửi SMS. Ngày không quay/không có lệnh là bình thường.
> 4. Bật **Tự động hóa (Automation)** trong Phím tắt (Time of Day → Run Shortcut “Gửi vé hôm nay”, Run Immediately nếu có) theo giờ khuyến nghị.
> 
> Bạn có thể **tạm dừng/bật lại** tự động bất cứ lúc nào bằng cách tắt/bật Tự động hóa. Nếu cần hỗ trợ, nhắn lại Zalo này. (Công cụ hỗ trợ gửi SMS, không bán vé/mua hộ và không đảm bảo trúng; phí/vé theo Vietlott SMS.)

## 2) Nhắc điều kiện Vietlott SMS (khi khách chưa nhận được phản hồi từ 9969)

> Bạn kiểm tra giúp mình các điều kiện Vietlott SMS: (1) đúng số điện thoại đã đăng ký Vietlott SMS, (2) đã thiết lập tài khoản/thẻ thanh toán mặc định, (3) đủ số dư/hạn mức theo số vé, (4) gửi trong khung giờ Vietlott nhận lệnh và đúng loại vé/cú pháp, (5) tin gửi tới **9969** từ đúng số Vietlott SMS. Nếu đã đủ điều kiện mà vẫn không nhận phản hồi, bạn chụp màn hình tin nhắn/ thông báo lỗi gửi mình để hỗ trợ kiểm tra.

## 3) Lỗi kích hoạt: đã có thiết bị khác (`another_device_active`)

> Thông báo này nghĩa là mã của bạn đang được gắn với **một thiết bị khác** (chính sách 1 gói = 1 thiết bị đang hoạt động). Để dùng trên iPhone hiện tại, bạn cần làm thủ tục **đổi máy**: phí **150.000đ/lần**, cần xác minh và cung cấp **mã giao dịch**; bên mình sẽ **thu hồi máy cũ ngay** và mở lại để bạn kích hoạt máy mới (áp dụng **cooldown tối thiểu 30 ngày** giữa 2 lần đổi). Bạn xác nhận muốn đổi máy và gửi mã giao dịch giúp mình nhé.

## 4) Hỗ trợ đổi máy (đã xác minh & thu phí)

*(Gửi sau khi đã thu phí + xác minh và admin đã thực hiện `rebind`)*

> Mình đã xác nhận và xử lý **đổi thiết bị** cho mã [LICENSE_KEY] (đã thu hồi thiết bị cũ). Bạn vui lòng mở iPhone mới → chạy lại phím tắt **Kích hoạt** với `SERVER_URL` và `LICENSE_KEY` để gắn máy mới, sau đó chạy thử “Gửi vé hôm nay” và bật lại Tự động hóa. Nếu gặp lỗi, nhắn mình kèm ảnh chụp thông báo.

## 5) Khách muốn tạm dừng / bật lại

> Bạn hoàn toàn chủ động: để **tạm dừng** tự động, vào **Phím tắt → Tự động hóa** và tắt/xóa tự động hóa chạy “Gửi vé Vietlott hôm nay”. Khi tạm dừng hệ thống sẽ không gửi lệnh mua vé. Để **bật lại**, bật lại tự động hóa đó.

## 6) Khách muốn đổi cấu hình (loại vé/số vé/bộ số)

> Mình ghi nhận yêu cầu đổi cấu hình của bạn (loại vé 645/655, số lượng vé, AI gợi ý hoặc bộ số tự chọn). Bên mình sẽ cập nhật phía hệ thống (cấu hình per-khách) và thông báo khi hoàn tất; các kỳ sau sẽ áp dụng theo cấu hình mới (tùy thời điểm/lịch quay).

## 7) Checklist vận hành (nội bộ, trước khi gửi khách)

- [ ] Đối soát thanh toán (ghi chú mã GD/ref).
- [ ] Tạo/kiểm tra license (`create-license`/`list`), trạng thái `active`.
- [ ] Cập nhật `phone_vietlott` (số Vietlott SMS thực tế) và `notes` (Zalo, mã GD) nếu có (`update-license`).
- [ ] Thiết lập cấu hình per-khách (`set-config`: game/mode/ticket_count/custom_tickets).
- [ ] Server đang chạy sau **HTTPS**, `SERVER_URL` đúng, `healthz` OK.
- [ ] Gửi khách `SERVER_URL` + `license_key` + link/hướng dẫn Shortcut (kênh riêng tư); nhắc điều kiện Vietlott & quyền tạm dừng.
- [ ] Xác nhận khách kích hoạt thành công (thiết bị active = 1) hoặc hỗ trợ xử lý lỗi.

*(Lưu ý: tự động hóa CSKH qua Zalo OA/ZNS/bot cần tích hợp riêng, chưa có trong repo.)*
