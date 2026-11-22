# Cách tạo Phím tắt “Vietlott Auto” CHUẨN — cầm tay chỉ việc (làm 1 lần)

Mục tiêu: tạo **đúng 1 phím tắt** trên iPhone, chạy được với API, rồi **chia sẻ 1 link iCloud** cho khách. Khách chỉ cần: mở link → Thêm phím tắt → chạy lần đầu **nhập mã của họ** → bấm Cho phép → bật Tự động hóa.

> **Thông tin cố định điền trong phím tắt**
> - `SERVER_URL` = `https://aivietlott.jbai.vn`
> - Mã demo để test = `VAF-F593-EB89-3453-EB4A` (khách dùng **mã riêng của họ**, phím tắt sẽ hỏi lúc chạy — **không điền sẵn mã vào phím tắt**)
> - Số nhận tin = `9969`; SĐT Vietlott SMS demo = `0906919053`
>
> **Nguyên tắc chống lỗi:** dùng GET `?license_key=...&device_id=...&device_secret=...` để lấy lệnh (không cần dựng JSON ở bước này). Kiểm tra lỗi bằng khóa `error` (có giá trị = lỗi) thay vì so sánh `ok` true/false — cách này không bao giờ nhầm trên iOS.

---

## 0) Những thao tác nền tảng phải biết trước (đọc kỹ 1 lần)

- **Thêm hành động:** ở cuối màn hình chạm **Thêm tác vụ** (Add Action) hoặc thanh tìm kiếm, gõ tên hành động (gõ tiếng Anh nếu không ra: `Text`, `Set Variable`, `Get File`, `Get Dictionary Value`, `If`, `Random UUID`, `Ask for Input`, `Get Contents of URL`, `Show Alert`, `Stop Shortcut`, `Dictionary`, `Save File`, `Count`, `Repeat with Each`, `Send Message`, `Wait`, `Show Notification`).
- **Chọn biến (quan trọng nhất):** sau khi một hành động tạo ra kết quả, **biến đó hiện ngay phía trên bàn phím** (hàng icon màu). Muốn dùng biến ở ô nào, hãy **chạm vào ô đó → chạm biến trên bàn phím → chọn tên biến**. Đừng gõ tay tên biến.
- **Đặt tên biến:** thêm hành động **Đặt biến (Set Variable)** → chạm tên mặc định → gõ tên (không dấu, viết liền, ví dụ `DEVICE_ID`) → OK.
- **Trong khối `Nếu (If)`:** các hành động nằm giữa `Nếu` và `Kết thúc Nếu (End If)` chỉ chạy khi đúng điều kiện. Để thêm hành động **vào trong** khối, hãy chạm dấu **+** ngay dòng `Nếu` (trước khi có `Kết thúc Nếu`). Kéo dài khối bằng cách chạm vùng trống cuối khối.
- **"Không có giá trị" / "Có giá trị":** trong `Nếu`, chạm vào điều kiện mặc định → chọn **has no value** (không có giá trị) hoặc **has any value** (có giá trị).

---

## 1) Bắt đầu

1. Mở app **Phím tắt (Shortcuts)** → tab **Phím tắt của tôi** → **+**.
2. Chạm tên phía trên → **Đổi tên** → `Vietlott Auto` → **Xong**.
3. Chạm **Thêm tác vụ**, làm lần lượt từ **Bước 1 → Bước 20** bên dưới. Mỗi xong 1 bước lại bấm `+` thêm bước kế tiếp.

---

## 2) Các hành động (làm đúng thứ tự)

### Nhóm A — Chuẩn bị & đọc thiết bị đã lưu

**B1. Văn bản (Text)**
- Nội dung: `https://aivietlott.jbai.vn`
- Thêm **Set Variable** → tên `SERVER_URL`.

**B2. Lấy tệp (Get File)**
- Chạm vào hành động để mở rộng:
  - Vị trí/Dịch vụ: **Phím tắt (Shortcuts)** *(nếu máy bạn chỉ hiện iCloud Drive → chọn iCloud Drive → thư mục Shortcuts)*
  - Tên/đường dẫn: `vietlott_device.json`
  - **Tắt** “Hiển thị bộ chọn tài liệu” (Show Document Picker)
  - **Tắt** “Báo lỗi nếu không tìm thấy” (Error If Not Found)
- **Set Variable** → `FILE`.

**B3. Lấy giá trị từ điển (Get Dictionary Value)** — lần 1
- Key: `device_id` · Dictionary: chọn biến `FILE` → **Set Variable** `DEVICE_ID`.

**B4. Lấy giá trị từ điển** — lần 2
- Key: `device_secret` · Dictionary: `FILE` → **Set Variable** `DEVICE_SECRET`.

**B5. Lấy giá trị từ điển** — lần 3
- Key: `license_key` · Dictionary: `FILE` → **Set Variable** `SAVED_KEY`.

**B6. Nếu (If)** — lấy mã đã lưu (khi đã kích hoạt từ trước)
- Điều kiện: `SAVED_KEY` **has any value** (có giá trị).
- Trong khối: **Set Variable** `LICENSE_KEY` = `SAVED_KEY`.
- **Kết thúc Nếu**.

**B7. Nếu (If)** — tạo mã thiết bị nếu chưa có
- Điều kiện: `DEVICE_ID` **has no value**.
- Trong khối: **Random UUID** → **Set Variable** `DEVICE_ID`.
- **Kết thúc Nếu**.

### Nhóm B — Kích hoạt (chỉ chạy lần đầu)

**B8. Nếu (If)**: điều kiện `DEVICE_SECRET` **has no value**. Mọi hành động B8a–B8h đặt **bên trong khối này**.

**B8a. Nếu (If)**: `LICENSE_KEY` **has no value**
- Trong khối: **Ask for Input (Yêu cầu nhập)** → kiểu **Văn bản (Text)**, câu hỏi: `Nhập mã kích hoạt (license_key)` → **Set Variable** `LICENSE_KEY`.
- **Kết thúc Nếu**.

**B8b. Văn bản (Text)**: chạm vào ô chữ → chèn biến `SERVER_URL` (từ hàng biến trên bàn phím) → gõ tiếp `/api/activate` (thành `https://aivietlott.jbai.vn/api/activate`) → **Set Variable** `ACT_URL`.

**B8c. Lấy nội dung của URL (Get Contents of URL)**
- URL: biến `ACT_URL`
- Chạm **Hiển thị thêm / Show More**:
  - Phương thức: **POST**
  - Nội dung yêu cầu (Request Body): **JSON**
  - Chạm **Add new field** (Thêm trường) 3 lần, mỗi lần: ô tên = `license_key`, `device_id`, `client_info`; ô giá trị = lần lượt chọn biến `LICENSE_KEY`, biến `DEVICE_ID`, và gõ văn bản `ios-shortcut/1.0`.
    *(Nếu ô giá trị không cho chọn biến, hãy chạm vào ô → nhìn hàng biến ngay trên bàn phím → chọn tên biến.)*
- **Set Variable** → `ACT_RES`.

**B8d. Lấy giá trị từ điển** khóa `device_secret` từ `ACT_RES` → `NEW_SECRET`.

**B8e. Lấy giá trị từ điển** khóa `error` từ `ACT_RES` → `ERR`.

**B8f. Lấy giá trị từ điển** khóa `message` từ `ACT_RES` → `MSG`.

**B8g. Nếu (If)**: `ERR` **has any value** (có nghĩa là server báo lỗi)
- Trong khối: **Hiển thị cảnh báo (Show Alert)** → tiêu đề `Kích hoạt lỗi`, nội dung: chèn biến `ERR`, gõ ` - `, chèn biến `MSG`.
- Trong khối: **Dừng phím tắt (Stop Shortcut)**.
- **Kết thúc Nếu**.

**B8h. Lưu thiết bị**
- **Set Variable** `DEVICE_SECRET` = `NEW_SECRET`.
- **Từ điển (Dictionary)** → thêm 3 mục:
  - `license_key` = biến `LICENSE_KEY`
  - `device_id` = biến `DEVICE_ID`
  - `device_secret` = biến `DEVICE_SECRET`
  → **Set Variable** `SAVE_DICT`.
- **Lưu tệp (Save File)**: nội dung = `SAVE_DICT`, tên = `vietlott_device.json`, vị trí **Phím tắt**, **tắt** “Hỏi nơi lưu”, **bật** “Ghi đè nếu tệp tồn tại”.
- **Hiển thị thông báo (Show Notification)**: `Kích hoạt thành công. Mã bảo mật đã lưu trên máy này.`
- **Kết thúc Nếu** (kết thúc B8).

### Nhóm C — Lấy lệnh hôm nay & gửi SMS

**B9. Văn bản (Text)** — tạo URL lấy lệnh. Nội dung (chạm và chèn biến tại các vị trí `[...]`):
```
[SERVER_URL]/api/today?license_key=[LICENSE_KEY]&device_id=[DEVICE_ID]&device_secret=[DEVICE_SECRET]
```
→ **Set Variable** `TODAY_URL`.
*(Gõ tay các dấu `/api/today?license_key=` v.v.; chỉ chèn biến ở 4 chỗ ngoặc vuông. Không được có khoảng trắng trong URL.)*

**B10. Lấy nội dung của URL** — URL = `TODAY_URL`, **giữ nguyên phương thức GET** (mặc định) → **Set Variable** `RES`.

**B11. Lấy giá trị từ điển** khóa `error` từ `RES` → `ERR2`.

**B12. Nếu (If)**: `ERR2` **has any value**
- Trong khối: lấy khóa `message` từ `RES` → `MSG2`; **Hiển thị cảnh báo** “Lỗi lấy lệnh: ” + `ERR2` + ` - ` + `MSG2`; **Dừng phím tắt**.
- **Kết thúc Nếu**.

**B13. Lấy giá trị từ điển** khóa `plan` từ `RES` → `PLAN`.

**B14. Lấy giá trị từ điển** khóa `status` từ `PLAN` → `STATUS`.

**B15. Nếu (If)**: `STATUS` **is** `REST_DAY` *(nếu máy bạn không có “is”, chọn **contains**)*
- Trong khối: **Hiển thị thông báo** `Hôm nay không có lệnh (ngày nghỉ/không quay).` → **Dừng phím tắt**.
- **Kết thúc Nếu**.

**B16. Lấy giá trị từ điển** khóa `sms_commands` từ `PLAN` → `COMMANDS`.

**B17. Đếm (Count)**: đếm trong `COMMANDS` → **Set Variable** `N`.

**B18. Nếu (If)**: `N` **is** `0`
- Trong khối: **Hiển thị thông báo** `Không có lệnh gửi.` → **Dừng phím tắt**.
- **Kết thúc Nếu**.

**B19. Lặp lại với mỗi (Repeat with Each)**: chọn `COMMANDS`
- Trong khối: **Gửi tin nhắn (Send Message)** → Người nhận `9969`, Nội dung = biến **Mục lặp lại (Repeat Item)** (chạm ô nội dung → chọn biến *Repeat Item* trên bàn phím).
- (Khuyến nghị) thêm **Đợi (Wait)** `3` giây.
- **Kết thúc Lặp**.

**B20. Hiển thị thông báo**: chèn biến `N` giữa các chữ: `Đã gửi ` + `N` + ` tin tới 9969. Kiểm tra phản hồi và số dư Vietlott SMS.`

Bấm **Xong** để lưu.

---

## 3) Chạy thử lần đầu (bắt buộc trước khi chia sẻ)

1. iPhone phải có SIM/SĐT **0906919053** (đã đăng ký Vietlott SMS, đủ số dư), có Internet.
2. Mở **Vietlott Auto** → chạy. Lần đầu:
   - iOS hỏi quyền (mạng/URL, tệp Phím tắt, **gửi tin nhắn**) → bấm **Cho phép/OK** hết.
   - Khi được hỏi mã → nhập `VAF-F593-EB89-3453-EB4A`.
3. Kỳ vọng: “Kích hoạt thành công”, rồi:
   - Có lệnh → máy gửi tin tới **9969** (ví dụ `645 K1 S ...`).
   - Hoặc báo `Hôm nay không có lệnh (REST_DAY)` → bình thường nếu ngày không quay.
4. Kiểm tra phía server (trên máy chủ): `python server\license_server.py list` → license demo có `active_devices = 1`.

> **Nếu lỡ nhập sai mã lần đầu:** xóa tệp `vietlott_device.json` trong Phím tắt (iCloud Drive → Shortcuts) hoặc xóa rồi thêm lại phím tắt từ link, rồi chạy lại với đúng mã. **Không** chia sẻ tệp này — nó chứa mã bảo mật thiết bị.

---

## 4) Lấy link iCloud (chính là “link quăng”)

**Điều kiện:** iPhone đã đăng nhập Apple ID, bật đồng bộ Phím tắt (*Cài đặt → [tên bạn] → iCloud → Phím tắt*, hoặc *Cài đặt → Phím tắt → Đồng bộ iCloud*).

1. **Phím tắt → Phím tắt của tôi** → **nhấn giữ** “Vietlott Auto” → **Chia sẻ (Share)**.
2. Chọn **Sao chép liên kết iCloud (Copy iCloud Link)** → xác nhận nếu được hỏi.
3. Link dạng `https://www.icloud.com/shortcuts/...` — **đây là link dùng chung**. Gửi link này cho mình để điền vào `CONFIG.shortcutUrl`, hoặc gửi khách.

> Không thấy “Sao chép liên kết iCloud”? Kiểm tra đăng nhập iCloud/đồng bộ Phím tắt, đang chia sẻ đúng phím tắt, thử đóng/mở lại app.

---

## 5) Khách dùng link (chỉ 2–3 bước, 1 lần)

1. Mở link iCloud trên iPhone → **Thêm phím tắt (Add Shortcut)**. *(Nếu iOS chặn “phím tắt không tin cậy”, vào Cài đặt → Phím tắt bật cho phép — chỉ với link do hỗ trợ chính thức gửi.)*
2. Mở **Phím tắt** → chạy **Vietlott Auto** → **nhập mã kích hoạt của khách** → bấm **Cho phép** các quyền iOS hỏi (mạng, tệp, gửi SMS). Lần sau không phải nhập lại.
3. **Phím tắt → Tự động hóa → + → Tạo tự động hóa cá nhân → Thời gian trong ngày** (giờ trước giờ chốt, lặp **Hằng ngày**) → **Chạy phím tắt “Vietlott Auto”** → bật **Chạy ngay lập tức** (nếu có) → **Xong**. Nên có người cài giúp bước này (~5 phút).

Tạm dừng: tắt Tự động hóa. 1 gói = 1 khách / 1 SĐT Vietlott SMS / 1 thiết bị; đổi máy 150.000đ/lần.

---

## 6) Xử lý lỗi khi dựng

| Triệu chứng | Cách sửa |
|---|---|
| B3–B5 không lấy được giá trị từ tệp | Thêm hành động **Lấy nội dung của tệp (Get Contents of File)** ngay sau B2, rồi lấy giá trị từ kết quả đó thay vì `FILE`. |
| B8c báo lỗi/403 | Kiểm tra URL đúng `/api/activate`, Method **POST**, Request Body **JSON**, đủ 3 trường; thử `curl` như trong `docs/CLIENT_INTEGRATION.md`. |
| `another_device_active` | License đang gắn máy khác → liên hệ hỗ trợ đổi máy (150.000đ/lần). |
| Lỗi `error` hiện ra | Đọc nội dung alert (`license_not_found`, `device_not_active`, `invalid_device_secret`, `license_status_*`) → đối chiếu `docs/HUONG_DAN_KHACH_IPHONE.md`. |
| B10 trả lỗi | Kiểm tra URL B9 **không có khoảng trắng**, đủ 3 tham số, `SERVER_URL` đúng `https://aivietlott.jbai.vn`. |
| B19 không gửi được tin | Vào Cài đặt → Tin nhắn/Phím tắt cho phép gửi SMS; kiểm tra máy 2 SIM gửi đúng số **0906919053**. |
| Chạy tự động vẫn hỏi xác nhận | Tuỳ iOS/cài đặt — test trên máy thật; hướng dẫn khách bật quyền Tự động hóa. |

Tham khảo kỹ thuật: `docs/CLIENT_INTEGRATION.md`, `docs/HUONG_DAN_KHACH_IPHONE_DON_GIAN.md`. Khi bạn gửi được **link iCloud**, mình sẽ điền `shortcutUrl` và soạn tin Zalo gửi khách.
