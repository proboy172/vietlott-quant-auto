# Hướng dẫn bắt đầu sử dụng trên iPhone (khách đã mua gói vĩnh viễn)

Tài liệu dành cho khách hàng dùng **iPhone (Phím tắt/Shortcuts)**. Công cụ hỗ trợ **tự động gửi SMS** đặt vé tới **9969** từ **chính số Vietlott SMS của bạn** theo lịch/cấu hình đã mua.

> **Lưu ý quan trọng**
> - Không bán vé, không mua hộ, không giữ tiền; **không đảm bảo trúng** (xổ số ngẫu nhiên). Phí SMS/vé (nếu gửi thành công) do Vietlott thu theo tài khoản Vietlott SMS của bạn.
> - **1 gói = 1 khách = 1 số Vietlott SMS = 1 thiết bị đang hoạt động**. Không chia sẻ/chuyển nhượng.
> - **Đổi máy:** 150.000đ/lần, cần xác minh + mã giao dịch; máy cũ bị thu hồi ngay, cooldown tối thiểu 30 ngày (theo chính sách hỗ trợ).
> - Bạn luôn có quyền **tạm dừng/bật tắt** tự động bất cứ lúc nào.

---

## 1) Sau khi mua, bạn sẽ nhận được gì?

Bên hỗ trợ sẽ gửi cho bạn (qua kênh riêng tư, ví dụ Zalo) các thông tin sau — **giữ kín, không chia sẻ**:

| Thông tin | Ý nghĩa |
|---|---|
| **SERVER_URL** | Địa chỉ hệ thống (dạng `https://...`) để iPhone lấy lệnh/cấu hình của riêng bạn |
| **Mã kích hoạt (license_key)** | Mã gói vĩnh viễn của bạn (ví dụ dạng `VAF-XXXX-...`) |
| **Link/hướng dẫn cài Shortcut** | Link iCloud Phím tắt (nếu có) hoặc hướng dẫn tạo 2 phím tắt: *Kích hoạt* và *Gửi vé hằng ngày* |
| **Cấu hình gói** | Loại vé (Mega 6/45 `645` hoặc Power 6/55 `655`), số lượng vé, AI gợi ý hay bộ số bạn chọn (đã được thiết lập phía hệ thống) |

> Hiện tại một số thông tin/link cài đặt có thể do nhân viên hỗ trợ gửi trực tiếp trong lúc triển khai. Nếu thiếu mục nào, hãy liên hệ Zalo/hỗ trợ để được cấp.

---

## 2) Chuẩn bị trước trên iPhone (bắt buộc)

1. **Đăng ký Vietlott SMS** cho **chính số điện thoại** đang dùng trên iPhone này.
2. **Tài khoản thanh toán Vietlott SMS**: đã thiết lập tài khoản/thẻ mặc định và **đủ số dư/hạn mức** theo số lượng vé.
3. **Đúng thời gian/điều kiện Vietlott**: gửi trong khung giờ Vietlott nhận lệnh (hệ thống chỉ cấp lệnh đúng ngày quay; ngày không quay sẽ không gửi). Tin nhắn phải gửi tới **9969** từ **đúng số Vietlott SMS đã đăng ký**.
4. **Thiết bị & quyền**:
   - iPhone có app **Phím tắt (Shortcuts)** (có sẵn trên iOS).
   - Có kết nối Internet (để lấy lệnh từ `SERVER_URL`).
   - Cho phép Phím tắt/Tự động hóa chạy khi được hỏi; cho phép **gửi tin nhắn (Messages/SMS)** tới `9969` khi chạy.
   - Khuyến nghị: tắt tối ưu pin quá mức cho Phím tắt nếu gây chặn chạy nền (tùy máy/iOS).
5. **1 iPhone duy nhất**: gói chỉ hoạt động trên **1 thiết bị đang kích hoạt** tại một thời điểm.

---

## 3) Bước 1 — Cài đặt Phím tắt

### Cách A (khuyến nghị): nhận link iCloud từ hỗ trợ
1. Mở link Phím tắt (iCloud) được hỗ trợ gửi trên iPhone.
2. Chạm **Thêm phím tắt / Get Shortcut** (có thể cần cuộn xuống và chọn *Thêm phím tắt không tin cậy* nếu iOS yêu cầu — chỉ thực hiện với link do hỗ trợ chính thức cung cấp).
3. Kiểm tra trong app **Phím tắt** đã có (thường gồm 2 phím tắt):
   - **Kích hoạt Vietlott (chạy 1 lần)** — gắn thiết bị này với mã của bạn.
   - **Gửi vé Vietlott hôm nay** — lấy lệnh & gửi SMS tới 9969.

### Cách B: chưa có link sẵn (do hỗ trợ/triển khai cấp sau)
- Liên hệ hỗ trợ để nhận link iCloud hoặc được hướng dẫn tạo thủ công. (Phần kỹ thuật tạo thủ công dành cho kỹ thuật/ops: xem `docs/CLIENT_INTEGRATION.md` mục 4.)

> Không cài/nhập mã từ nguồn không rõ. Không chia sẻ link/mã/phím tắt đã kích hoạt cho người khác.

---

## 4) Bước 2 — Kích hoạt thiết bị (chỉ chạy 1 lần trên iPhone này)

Mục tiêu: gắn gói của bạn với **chính iPhone này**. Sau bước này máy sẽ lưu khóa bảo mật riêng (`device_secret`) — **không chia sẻ**.

1. Mở app **Phím tắt** → chạy phím tắt **“Kích hoạt…”**.
2. Khi được hỏi, nhập/dán:
   - `SERVER_URL` (đúng như hỗ trợ cung cấp, bắt đầu bằng `https://`)
   - `LICENSE_KEY` (mã kích hoạt của bạn)
   *(Một số bản phím tắt có thể đã điền sẵn — chỉ cần xác nhận.)*
3. Nếu iOS hỏi quyền (truy cập mạng/URL, truy cập tệp trong Phím tắt/iCloud Drive…), chọn **Cho phép/OK**.
4. **Kết quả mong đợi:** thông báo kiểu **“Kích hoạt thành công”** (hoặc trạng thái tương đương). Từ đây iPhone này là thiết bị đang hoạt động của gói.

**Nếu gặp lỗi:**
- `another_device_active` / “đã có thiết bị khác đang hoạt động”: gói đang gắn với máy khác. Liên hệ hỗ trợ để **đổi máy** (phí 150.000đ/lần, xác minh + mã giao dịch; máy cũ bị thu hồi ngay, áp dụng cooldown theo chính sách) rồi chạy lại Kích hoạt trên iPhone mới.
- `license_not_found` / `license_status_*` (suspended/revoked/expired) / lỗi mạng: kiểm tra lại mã, kết nối, hoặc liên hệ hỗ trợ.
- **Không chạy lại kích hoạt lung tung** nếu không cần; nếu lỡ làm mất dữ liệu kích hoạt/phím tắt, liên hệ hỗ trợ để được hướng dẫn an toàn.

---

## 5) Bước 3 — Chạy thử lần đầu (kiểm tra gửi SMS)

1. Mở **Phím tắt** → chạy phím tắt **“Gửi vé Vietlott hôm nay”**.
2. Lần đầu iOS có thể hỏi quyền **Gửi tin nhắn** / truy cập mạng: chọn **Cho phép**.
3. Hệ thống sẽ kiểm tra và phản hồi:
   - **Có lệnh (ACTIVE_BUY):** phím tắt sẽ gửi từng tin nhắn (nội dung dạng `645 K1 S ...` hoặc `655 K1 S ...`) tới **9969** từ SIM/số Vietlott SMS của bạn. Bạn có thể thấy tin trong app **Tin nhắn** và (nếu đủ điều kiện Vietlott) nhận phản hồi từ 9969.
   - **Ngày nghỉ/không có lệnh (REST_DAY hoặc rỗng):** không gửi SMS — đây là bình thường (không phải ngày quay hoặc không có lệnh phát).
   - **Lỗi thiết bị/license:** phím tắt sẽ báo lỗi (ví dụ thiết bị không hợp lệ, chưa kích hoạt) — dừng và xử lý theo thông báo/liên hệ hỗ trợ.
4. **Kiểm tra điều kiện Vietlott:** đúng số đã đăng ký, đủ số dư/hạn mức, trong giờ nhận. Vietlott từ chối/không phản hồi thường do điều kiện tài khoản Vietlott SMS (không phải do phím tắt).

> Mỗi lệnh gửi đi (nếu Vietlott nhận) sẽ phát sinh phí theo Vietlott SMS/số lượng vé.

---

## 6) Bước 4 — Bật tự động hằng ngày (24/7 theo lịch)

Sau khi chạy thử OK, bạn có thể để iPhone tự gửi đúng lịch:

1. Mở app **Phím tắt** → tab **Tự động hóa (Automation)**.
2. Chạm **+** (hoặc *Tự động hóa mới*) → **Tạo Tự động hóa cá nhân**.
3. Chọn điều kiện **Thời gian trong ngày (Time of Day)**:
   - Chọn giờ chạy phù hợp **trước giờ chốt nhận lệnh** của kỳ quay (nên hỏi hỗ trợ khung giờ khuyến nghị cho `645`/`655`).
   - Lặp lại: **Hằng ngày** (hoặc theo ngày quay nếu bạn tự quản lý; chạy ngày nghỉ hệ thống sẽ trả không có lệnh).
4. Phần hành động: chọn **Chạy Phím tắt** → chọn **“Gửi vé Vietlott hôm nay”**.
5. Bật **Chạy ngay lập tức / Run Immediately** (nếu iOS có tùy chọn) và tắt yêu cầu hỏi trước khi chạy (nếu muốn tự động hoàn toàn). Tùy phiên bản iOS/cài đặt, máy vẫn có thể yêu cầu xác nhận trong một số trường hợp — hãy làm theo hướng dẫn hỗ trợ để bật đúng quyền.
6. Lưu tự động hóa.

**Khuyến nghị:** giữ iPhone có mạng và SIM Vietlott SMS hoạt động; đảm bảo số dư đủ cho các kỳ.

---

## 7) Tạm dừng / Bật lại (bạn luôn kiểm soát)

- **Tạm dừng tự động:** vào **Phím tắt → Tự động hóa** → tắt hoặc xóa tự động hóa “Gửi vé Vietlott hôm nay”.
- **Bật lại:** bật lại tự động hóa.
- Khi tạm dừng, hệ thống **không** gửi lệnh mua vé cho bạn.

---

## 8) Lỗi thường gặp & cách xử lý nhanh

| Tình huống | Nên làm gì |
|---|---|
| Báo “đã có thiết bị khác hoạt động” (`another_device_active`) | Liên hệ hỗ trợ đổi máy (150.000đ/lần, xác minh + mã GD). Sau khi được mở lại, chạy **Kích hoạt** trên iPhone này. |
| “Thiết bị không hợp lệ / secret sai” (`device_not_active`, `invalid_device_secret`) | Xóa dữ liệu kích hoạt/phím tắt cũ theo hướng dẫn hỗ trợ và **Kích hoạt lại** (hoặc liên hệ hỗ trợ nếu tài khoản bị thu hồi). |
| License bị tạm ngưng/hết hiệu lực | Liên hệ hỗ trợ kiểm tra trạng thái gói. |
| Đã gửi 9969 nhưng không nhận phản hồi / Vietlott từ chối | Kiểm tra: đúng SĐT đã đăng ký Vietlott SMS, tài khoản/thẻ mặc định, đủ số dư/hạn mức, trong giờ nhận, đúng loại vé/cú pháp (hệ thống cấp đúng cú pháp). |
| Không có mạng / `SERVER_URL` lỗi | Kiểm tra kết nối Internet và `SERVER_URL` đúng như được cấp (HTTPS). |
| Muốn đổi số lượng vé/loại vé/bộ số | Liên hệ hỗ trợ để cập nhật cấu hình per-khách phía hệ thống. |

---

## 9) Về hình ảnh / video hướng dẫn chi tiết

- Hiện **chưa có sẵn** bộ ảnh chụp màn hình iOS thực tế hoặc video hướng dẫn trong kho mã này. Các bước thao tác trên iPhone (tên nút/vị trí) có thể khác nhẹ tùy phiên bản iOS/ngôn ngữ máy.
- Nếu bạn cần, hãy yêu cầu hỗ trợ gửi: (1) **link iCloud Phím tắt** chính thức, (2) **video/ảnh chụp màn hình** thao tác mẫu (Thêm phím tắt → Kích hoạt → Cho phép quyền → Chạy thử → Tạo Tự động hóa) tương ứng với phiên bản iOS bạn đang dùng.
- Tham chiếu kỹ thuật/triển khai (cho vận hành): `docs/CLIENT_INTEGRATION.md`.

---

## Tóm tắt nhanh

1. Nhận `SERVER_URL` + `LICENSE_KEY` + link/hướng dẫn Shortcut từ hỗ trợ (kênh riêng).
2. Đảm bảo điều kiện Vietlott SMS (đúng số, đủ số dư, trong giờ).
3. Cài Shortcut → **Kích hoạt (1 lần)** trên iPhone này.
4. **Chạy thử** “Gửi vé hôm nay” và cấp quyền SMS.
5. Tạo **Tự động hóa** theo giờ để chạy hằng ngày.
6. Cần dừng thì **tắt Tự động hóa** bất cứ lúc nào.
