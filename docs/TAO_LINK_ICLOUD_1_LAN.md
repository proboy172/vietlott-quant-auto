# Tạo 1 link iCloud dùng chung (1 lần) — khách chỉ cần điền mã

**Mục tiêu:** bạn tạo phím tắt **1 lần** trên iPhone → lấy **1 link iCloud** → gửi cho khách; khách mở link, thêm phím tắt, chạy và **nhập mã kích hoạt của họ** là xong (cộng với bấm “Cho phép” và bật Tự động hóa 1 lần do iOS bắt buộc).

> **Quan trọng:** *Link iCloud Shortcuts* chỉ tạo được **trong app Phím tắt trên iPhone/iPad** đã đăng nhập iCloud (bấm **Chia sẻ → Sao chép liên kết iCloud**). Không thể tạo link này từ máy tính/môi trường code hay từ repo — vì vậy cần bạn (hoặc người có iPhone) thực hiện “Bước 1” bên dưới **một lần** để sinh ra link.

- **SERVER_URL (điền sẵn trong phím tắt):** `https://aivietlott.jbai.vn`
- **Mã demo (ví dụ):** `VAF-F593-EB89-3453-EB4A` — mỗi khách dùng **mã riêng** của họ.
- **Gửi SMS tới:** `9969` (từ đúng SIM/SĐT Vietlott SMS của khách).

---

## Bước 1 — Bạn tạo phím tắt và lấy link iCloud (làm 1 lần trên iPhone)

### 1.1 Chuẩn bị
- iPhone đã đăng nhập Apple ID, có app **Phím tắt (Shortcuts)**. Khuyến nghị bật đồng bộ Phím tắt iCloud (*Cài đặt → [tên bạn] → iCloud → Phím tắt*, hoặc *Cài đặt → Phím tắt*).
- Cần test: iPhone có SIM/SĐT Vietlott SMS đã đăng ký, có mạng, đủ số dư (demo: `0906919053`).

### 1.2 Tạo phím tắt “Vietlott Auto” (gộp, hỏi mã lần đầu)
Mở **Phím tắt → Phím tắt của tôi → dấu +** → đặt tên **`Vietlott Auto`** → **Thêm tác vụ** lần lượt:

1. **Văn bản (Text):** `https://aivietlott.jbai.vn` → **Đặt biến (Set Variable)** `SERVER_URL`.
2. **Lấy tệp (Get File):** vị trí **Phím tắt** (Shortcuts), tệp `vietlott_device.json`, **tắt** “Hiển thị bộ chọn”, **tắt** “Báo lỗi nếu không tìm thấy (Error If Not Found)”.
3. Từ tệp đó, **Lấy giá trị từ điển (Get Dictionary Value)**: khóa `device_id`→`DEVICE_ID`, khóa `device_secret`→`DEVICE_SECRET`, khóa `license_key`→`LICENSE_KEY`.
4. **Nếu (If)** `DEVICE_ID` không có giá trị: **UUID ngẫu nhiên (Random UUID)** → `Đặt biến` `DEVICE_ID`. (Kết thúc Nếu)
5. **Nếu (If)** `DEVICE_SECRET` không có giá trị *(chưa kích hoạt → hỏi mã 1 lần)*:
   - **Yêu cầu nhập (Ask for Input)**: “Nhập mã kích hoạt (license_key)” (kiểu Văn bản) → `Đặt biến` `LICENSE_KEY`. *(**Không** điền sẵn mã của bạn để link dùng được cho mọi khách.)*
   - **Lấy nội dung của URL (Get Contents of URL)**: URL `https://aivietlott.jbai.vn/api/activate`, Method **POST**, Request Body **JSON** với: `license_key` = `LICENSE_KEY`, `device_id` = `DEVICE_ID`, `client_info` = `ios-shortcut/1.0` → `Đặt biến` `ACT_RES`.
   - Từ `ACT_RES` lấy `ok`→`OK`, `device_secret`→`NEW_SECRET`, `error`→`ERR`, `message`→`MSG`.
   - **Nếu** `OK` không đúng (thất bại): **Hiển thị cảnh báo (Show Alert)** `Kích hoạt lỗi: (ERR) (MSG)` → **Dừng phím tắt (Stop Shortcut)**. (Kết thúc Nếu)
   - `Đặt biến` `DEVICE_SECRET` = `NEW_SECRET`.
   - **Từ điển (Dictionary)** `{license_key: LICENSE_KEY, device_id: DEVICE_ID, device_secret: DEVICE_SECRET}` → **Lưu tệp (Save File)** tên `vietlott_device.json` vào **Phím tắt** (tắt “Hỏi nơi lưu”, **bật** “Ghi đè nếu tệp tồn tại”). (Kết thúc Nếu kích hoạt)
6. **Lấy nội dung của URL**: URL `https://aivietlott.jbai.vn/api/today`, Method **POST**, Request Body **JSON** với `license_key`=`LICENSE_KEY`, `device_id`=`DEVICE_ID`, `device_secret`=`DEVICE_SECRET` → `Đặt biến` `RES`.
7. Từ `RES` lấy `plan`→`PLAN`; từ `PLAN` lấy `status`→`STATUS`, `sms_commands`→`COMMANDS`.
8. **Nếu** `STATUS` là `REST_DAY`: **Hiển thị thông báo** `Hôm nay không có lệnh (ngày nghỉ)` → **Dừng phím tắt**. (Kết thúc Nếu)
9. **Lặp lại với mỗi (Repeat with Each)** trong `COMMANDS`: **Gửi tin nhắn (Send Message)** tới `9969`, nội dung = **Mục lặp lại (Repeat Item)**; *(khuyến nghị)* **Đợi (Wait)** 3 giây. (Kết thúc Lặp)
10. **Hiển thị thông báo**: “Hoàn tất (đã gửi lệnh nếu có)”. → Bấm **Xong** để lưu.

> **Ghi chú:** tên hành động có thể khác theo iOS/ngôn ngữ (Text, Get File, Get Dictionary Value, Set Variable, If, Random UUID, Ask for Input, Get Contents of URL, Show Alert, Stop Shortcut, Save File, Repeat with Each, Send Message, Wait). Cách này rút gọn tối đa (gần giống luồng cũ: lấy lệnh → lặp gửi), server đã trả sẵn `sms_commands` nên không cần tách văn bản.

### 1.3 Test nhanh (trước khi chia sẻ)
- Trên iPhone có SIM Vietlott SMS hợp lệ (demo `0906919053`), chạy phím tắt → nhập mã (demo `VAF-F593-EB89-3453-EB4A`) → bấm **Cho phép** mọi quyền iOS hỏi (mạng, tệp, **gửi SMS**).
- Kỳ vọng: lần đầu kích hoạt và lưu `vietlott_device.json`; ngày có lệnh sẽ gửi tin tới 9969, ngày nghỉ báo `REST_DAY`/không gửi. (1 license chỉ bind 1 thiết bị.)
- *Nếu lỡ nhập sai mã lần đầu:* xóa tệp `vietlott_device.json` trong thư mục Phím tắt (iCloud Drive/Shortcuts) hoặc xóa & thêm lại phím tắt rồi chạy lại.

### 1.4 Lấy link iCloud (chính là “link quăng”)
1. Trong **Phím tắt → Phím tắt của tôi**, **nhấn giữ** “Vietlott Auto” → **Chia sẻ (Share)**.
2. Chọn **Sao chép liên kết iCloud (Copy iCloud Link)** (xác nhận chia sẻ nếu được hỏi).
3. Dán và lưu lại link `https://www.icloud.com/shortcuts/...` — **đây là link dùng chung** để gửi cho bạn/khách.

> Nếu không thấy “Sao chép liên kết iCloud”: kiểm tra đã đăng nhập iCloud và bật đồng bộ Phím tắt, chia sẻ từ đúng phím tắt đó (tên tuỳ iOS).

---

## Bước 2 — Gửi khách: khách chỉ cần điền mã (2–3 bước, 1 lần)

Gửi khách (kênh riêng) **link iCloud** + **mã kích hoạt riêng của khách** + nhắc dùng iPhone có SIM/SĐT Vietlott SMS của họ. Khách làm:

1. **Mở link iCloud** (trên iPhone) → bấm **Thêm phím tắt (Add Shortcut)**.
2. Mở **Phím tắt** → chạy **“Vietlott Auto”** → khi được hỏi **nhập mã kích hoạt** (mã của khách) → bấm **Cho phép/OK** cho các quyền iOS hỏi (mạng, tệp, gửi SMS). *(Lần sau không cần nhập lại.)*
3. **Bật tự chạy:** **Phím tắt → Tự động hóa → + → Thời gian trong ngày** (giờ trước giờ chốt, lặp **Hằng ngày**) → **Chạy phím tắt “Vietlott Auto”** → bật **Chạy ngay lập tức** (nếu có) → Xong. *(Nên có người cài giúp bước này.)*

**Tạm dừng:** tắt Tự động hóa. **Lưu ý iOS:** bắt buộc cấp quyền và tạo Tự động hóa 1 lần; tuỳ phiên bản có thể hỏi xác nhận khi chạy tự động. Người già/không rành: hỗ trợ làm giúp 1 lần ~3–5 phút.

---

## Tin nhắn mẫu gửi khách (copy & thay [MÃ])

> Chào bạn, mình gửi link cài đặt (riêng tư, không chia sẻ):
> - Link Phím tắt: [LINK_ICLOUD]
> - Mã kích hoạt: [MÃ_KÍCH_HOẠT]
> - Số Vietlott SMS dùng trên iPhone: [SĐT_VIETLOTT_SMS]
>
> Cách dùng (1 lần): (1) Mở link → Thêm phím tắt. (2) Mở Phím tắt → chạy “Vietlott Auto” → nhập mã khi được hỏi → bấm Cho phép các quyền (mạng/tệp/gửi SMS). (3) Bật Tự động hóa hằng ngày (Phím tắt → Tự động hóa → Thời gian trong ngày → chạy “Vietlott Auto”). Cần hỗ trợ/cài giúp nhắn mình.

---

## Lưu ý & xử lý
- **Bảo mật:** không chia sẻ mã, không chia sẻ tệp `vietlott_device.json`/mã bảo mật thiết bị. Mỗi người nhập **mã riêng** của mình.
- **1 gói = 1 khách = 1 SĐT Vietlott SMS = 1 thiết bị.** Cùng 1 license không kích hoạt được máy thứ hai (`another_device_active`) → đổi máy: 150.000đ/lần, xác minh + mã GD, thu hồi máy cũ, cooldown 30 ngày (liên hệ hỗ trợ).
- **Vietlott:** phải đúng SĐT đã đăng ký Vietlott SMS, đủ số dư/hạn mức, trong giờ nhận lệnh; công cụ không bán vé/mua hộ, không đảm bảo trúng.
- **Nếu khách nhập sai mã/lỗi kích hoạt lần đầu:** xóa `vietlott_device.json` (thư mục Phím tắt) hoặc xóa phím tắt → thêm lại từ link → chạy và nhập đúng mã.
- Tham khảo kỹ thuật: `docs/CLIENT_INTEGRATION.md`, `docs/TAO_SHORTCUT_IPHONE_TUNG_BUOC.md`, `docs/HUONG_DAN_KHACH_IPHONE_DON_GIAN.md`.