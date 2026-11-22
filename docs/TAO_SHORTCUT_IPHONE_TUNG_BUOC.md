# Tạo 1 Phím tắt “Vietlott Auto” trên iPhone (từng bước, làm 1 lần)

Hướng dẫn này dành cho **người vận hành/cài giúp** để tạo **một phím tắt gộp duy nhất** trên iPhone. Sau khi tạo xong, bạn **chia sẻ link iCloud** cho khách — khi đó khách chỉ cần **2–3 bước** (thêm phím tắt → chạy lần đầu cho phép & nhập mã → bật Tự động hóa), không phải tự tạo.

> **Bạn đang ở đâu?**: “B1 mở app Phím tắt trên iPhone rồi sao nữa” → bắt đầu từ **Mục A** bên dưới.
>
> **Lưu ý iPhone/Shortcuts:** tên nút/hành động có thể khác chút theo phiên bản iOS và ngôn ngữ (Tiếng Việt/English). Dùng ô **tìm kiếm** trong “Thêm tác vụ” để tìm đúng tên. Nếu kẹt ở bước nào, chụp màn hình và hỏi hỗ trợ.
>
> **Hệ thống đã sẵn sàng:** `SERVER_URL = https://aivietlott.jbai.vn` (đã chạy). License demo: `VAF-F593-EB89-3453-EB4A` (645, AI động, 2 vé, SĐT Vietlott SMS **0906919053**, chưa bind thiết bị). Cần iPhone có SIM 0906919053 (đã đăng ký Vietlott SMS, đủ số dư) để test gửi thật.

---

## A. Bước bắt đầu: mở và tạo phím tắt mới (B1)

1. Mở app **Phím tắt** (**Shortcuts**, biểu tượng 2 ô vuông màu hồng/xanh) trên iPhone.
2. Chạm tab **Phím tắt của tôi** (My Shortcuts) ở dưới.
3. Chạm dấu **+** ở góc trên bên phải để tạo phím tắt mới.
4. Chạm vào tên ở trên cùng (ví dụ “Phím tắt mới” / “New Shortcut”) → chọn **Đổi tên** (Rename) → đặt tên: **`Vietlott Auto`** → Xong/OK.
5. Ở giữa màn hình (hoặc phía dưới) chạm **Thêm tác vụ** (**Add Action**) để bắt đầu thêm các hành động theo **Mục B** (làm lần lượt từ trên xuống dưới).

---

## B. Thêm các hành động (theo đúng thứ tự)

Mỗi lần cần hành động mới: chạm **Thêm tác vụ** (hoặc ô tìm kiếm ở dưới) → gõ tên hành động → chọn nó. Các hành động xếp chồng từ trên xuống.

### B1. Đặt địa chỉ hệ thống (SERVER_URL)
1. Tìm và thêm hành động **Văn bản** (**Text**). Nhập đúng: `https://aivietlott.jbai.vn`
2. Tìm và thêm **Đặt biến** (**Set Variable**). Đặt tên biến là `SERVER_URL` (biến này lấy từ Văn bản phía trên).

### B2. Đọc tệp thiết bị đã lưu (nếu có)
3. Thêm **Lấy tệp** (**Get File**):
   - Vị trí: chọn **Phím tắt** (**Shortcuts** / iCloud Drive Shortcuts).
   - Đường dẫn/tệp: `vietlott_device.json`
   - **Tắt** “Hiển thị bộ chọn tài liệu” (Show Document Picker) nếu có.
   - **Tắt** “Báo lỗi nếu không tìm thấy” (**Error If Not Found**) — quan trọng (lần đầu chưa có tệp).
4. Thêm **Đặt biến** → đặt tên `FILE` (lấy từ kết quả Lấy tệp).

### B3. Lấy thông tin thiết bị từ tệp
5. Thêm **Lấy giá trị từ điển** (**Get Dictionary Value** / Get Value for Key): lấy giá trị của khóa (Key) `device_id` trong `FILE` → **Đặt biến** `DEVICE_ID`.
6. Thêm **Lấy giá trị từ điển**: khóa `device_secret` trong `FILE` → **Đặt biến** `DEVICE_SECRET`.
7. Thêm **Lấy giá trị từ điển**: khóa `license_key` trong `FILE` → **Đặt biến** `SAVED_KEY`.

### B4. Tạo mã thiết bị nếu chưa có
8. Thêm **Nếu** (**If**): điều kiện `DEVICE_ID` **không có giá trị** (has no value / is empty).
   - Bên trong khối Nếu: thêm **UUID** (**Random UUID** / Tạo UUID) → **Đặt biến** `DEVICE_ID`.
   - Kết thúc Nếu (**End If**).

### B5. Kích hoạt lần đầu (nếu chưa có mã bảo mật)
9. Thêm **Nếu** (**If**): điều kiện `DEVICE_SECRET` **không có giá trị** (has no value). (Trong khối Nếu này làm các bước 9a–9k):

   **9a. Hỏi mã kích hoạt (lần đầu)**
   - Thêm **Yêu cầu nhập** (**Ask for Input**): câu hỏi `Nhập mã kích hoạt (license_key):`, kiểu nhập **Văn bản** (Text). (Có thể điền sẵn gợi ý `VAF-F593-EB89-3453-EB4A` khi test; nếu làm bản chia sẻ cho khách thì để trống để khách nhập mã của họ.)
   - **Đặt biến** → `LICENSE_KEY`.

   **9b. Tạo nội dung gọi kích hoạt**
   - Thêm **Từ điển** (**Dictionary**), thêm 3 mục:
     - `license_key` → chọn biến `LICENSE_KEY`
     - `device_id` → chọn biến `DEVICE_ID`
     - `client_info` → nhập văn bản `ios-shortcut/1.0`
   - **Đặt biến** → `ACT_BODY`.

   **9c. Tạo URL kích hoạt**
   - Thêm **Văn bản** (**Text**) có nội dung: biến `SERVER_URL` nối với `/api/activate` (viết liền thành `https://aivietlott.jbai.vn/api/activate` bằng cách chọn biến SERVER_URL rồi gõ tiếp `/api/activate`).
   - **Đặt biến** → `ACT_URL`.

   **9d. Gọi API kích hoạt**
   - Thêm **Lấy nội dung của URL** (**Get Contents of URL**):
     - URL: `ACT_URL`
     - Chạm **Hiển thị thêm** (Show More) nếu có:
       - Phương thức (**Method**): **POST**
       - Nội dung yêu cầu (**Request Body**): **JSON**
       - Điền các trường JSON: `license_key` = `LICENSE_KEY`, `device_id` = `DEVICE_ID`, `client_info` = `ios-shortcut/1.0` (hoặc nếu có tuỳ chọn dùng từ điển/biến, chọn `ACT_BODY`).
   - **Đặt biến** → `ACT_RES`.

   **9e. Đọc kết quả kích hoạt**
   - Từ `ACT_RES` dùng **Lấy giá trị từ điển** lấy: `ok`→`OK`, `device_secret`→`NEW_SECRET`, `error`→`ERR`, `message`→`MSG` (mỗi cái một hành động + Đặt biến tương ứng, hoặc lần lượt).

   **9f. Nếu kích hoạt thất bại**
   - Thêm **Nếu**: `OK` **không phải** đúng/true (ví dụ điều kiện “is not” giá trị `1`/Yes/true — tuỳ iOS; kiểm tra sao cho khi thất bại sẽ vào nhánh này).
     - Thêm **Hiển thị cảnh báo** (**Show Alert**): tiêu đề `Kích hoạt thất bại`, nội dung ghép `Lỗi: ` + `ERR` + ` - ` + `MSG`.
       - Gợi ý cho người dùng: nếu `ERR` là `another_device_active` → liên hệ hỗ trợ đổi máy (150.000đ/lần). Nếu `license_status_*`/`license_not_found` → kiểm tra mã/gói. Lỗi mạng → kiểm tra Internet/`SERVER_URL`.
     - Thêm **Dừng phím tắt** (**Stop Shortcut**).
   - Kết thúc Nếu.

   **9g. Nếu không nhận được mã bảo mật**
   - Thêm **Nếu**: `NEW_SECRET` **không có giá trị**.
     - **Hiển thị cảnh báo**: `Không nhận được mã bảo mật. Liên hệ hỗ trợ.`
     - **Dừng phím tắt**.
   - Kết thúc Nếu.

   **9h. Lưu thông tin đã kích hoạt**
   - **Đặt biến** `DEVICE_SECRET` = `NEW_SECRET`.
   - **Đặt biến** `SAVED_KEY` = `LICENSE_KEY`.

   **9i. Ghi tệp thiết bị**
   - Thêm **Từ điển**: `device_id` = `DEVICE_ID`, `device_secret` = `DEVICE_SECRET`, `license_key` = `SAVED_KEY`. → **Đặt biến** `SAVE_DICT` (tuỳ chọn).
   - Thêm **Lưu tệp** (**Save File**): lưu `SAVE_DICT` (hoặc từ điển vừa tạo) với tên `vietlott_device.json`, vị trí **Phím tắt** (Shortcuts), **tắt** “Hỏi nơi lưu” (Ask Where to Save), **bật** “Ghi đè nếu tệp tồn tại” (Overwrite If File Exists).

   **9j. Thông báo thành công**
   - Thêm **Hiển thị thông báo** (**Show Notification** / hoặc Show Alert): `Kích hoạt thành công trên thiết bị này.`

   **9k.** Kết thúc khối **Nếu** (bước 9 — chưa có DEVICE_SECRET).

### B6. Đảm bảo có mã license để lấy lệnh
10. Thêm **Nếu**: `SAVED_KEY` **có giá trị** (has any value) → bên trong: **Đặt biến** `LICENSE_KEY` = `SAVED_KEY`. Kết thúc Nếu.  
    *(Nếu vừa kích hoạt ở B5 thì SAVED_KEY đã được đặt; nếu đã kích hoạt từ trước thì lấy từ tệp.)*

### B7. Lấy lệnh hôm nay
11. Thêm **Từ điển**: `license_key`=`LICENSE_KEY`, `device_id`=`DEVICE_ID`, `device_secret`=`DEVICE_SECRET`. (→ có thể Đặt biến `TODAY_BODY`)
12. Thêm **Văn bản**: `SERVER_URL` + `/api/today` → **Đặt biến** `TODAY_URL`.
13. Thêm **Lấy nội dung của URL**: URL `TODAY_URL`, Method **POST**, Request Body **JSON** với 3 trường trên → **Đặt biến** `TODAY_RES`.
14. Từ `TODAY_RES` lấy: `ok`→`OK2`, `error`→`ERR2`, `message`→`MSG2`, `plan`→`PLAN`.
15. **Nếu** `OK2` không đúng:
    - **Hiển thị cảnh báo**: `Lỗi lấy lệnh: ` + `ERR2` + ` - ` + `MSG2` (gợi ý: `another_device_active` → đổi máy; `device_not_active`/`invalid_device_secret` → kích hoạt lại/liên hệ hỗ trợ; `license_status_*` → kiểm tra gói; lỗi mạng → kiểm tra kết nối).
    - **Dừng phím tắt**.
    Kết thúc Nếu.

### B8. Xử lý kết quả và gửi SMS
16. Từ `PLAN` lấy: `status`→`STATUS`, `sms_commands`→`COMMANDS`.
17. **Nếu** `STATUS` **là** (is) `REST_DAY`:
    - **Hiển thị thông báo**: `Hôm nay không có lệnh (ngày nghỉ/không quay).`
    - **Dừng phím tắt**.
    Kết thúc Nếu.
18. Thêm **Đếm** (**Count**): đếm mục trong `COMMANDS` → **Đặt biến** `N`.
19. **Nếu** `N` **là** `0`:
    - **Hiển thị thông báo**: `Không có lệnh gửi.`
    - **Dừng phím tắt**.
    Kết thúc Nếu.
20. Thêm **Lặp lại với mỗi** (**Repeat with Each**) mục trong `COMMANDS`:
    - Thêm **Gửi tin nhắn** (**Send Message**): Người nhận `9969`, Nội dung = **Mục lặp lại** (Repeat Item).
    - (Khuyến nghị) Thêm **Đợi** (**Wait**) `3` giây.
    Kết thúc Lặp.
21. **Hiển thị thông báo**: `Đã gửi ` + `N` + ` tin tới 9969. Kiểm tra phản hồi và đủ số dư/điều kiện Vietlott SMS.`

Chạm **Xong (Done)** ở góc trên phải để lưu phím tắt.

---

## C. Chạy thử (quan trọng, trên iPhone có SIM Vietlott SMS)
1. Đảm bảo iPhone có SIM **0906919053** (đã đăng ký Vietlott SMS, đủ số dư), có mạng.
2. Chạy **Vietlott Auto** lần đầu: nhập mã `VAF-F593-EB89-3453-EB4A` (nếu được hỏi) → bấm **Cho phép/OK** cho mọi quyền iOS hỏi (mạng/URL, tệp, **gửi tin nhắn**).
3. Kỳ vọng: “Kích hoạt thành công”, sau đó hoặc gửi tin tới 9969 (nếu hôm nay `ACTIVE_BUY`) hoặc báo “Hôm nay không có lệnh (REST_DAY)” (bình thường nếu ngày không quay).
4. Kiểm tra hệ thống: license `VAF-F593-EB89-3453-EB4A` sẽ có `active_devices = 1` (sau kích hoạt). Không chia sẻ `vietlott_device.json`/mã bảo mật.
5. Nếu lỗi `another_device_active`: cần đổi máy (150.000đ/lần, xác minh, thu hồi máy cũ, cooldown 30 ngày) qua hỗ trợ.

## D. Chia sẻ link iCloud để khách chỉ làm 2–3 bước
1. Trong **Phím tắt**, nhấn giữ (hoặc mở chi tiết) **Vietlott Auto** → **Chia sẻ (Share)**.
2. Chọn chia sẻ qua **iCloud** / sao chép **Liên kết iCloud** (Copy iCloud Link). (Cần bật chia sẻ phím tắt iCloud trong cài đặt Phím tắt nếu iOS yêu cầu.)
3. Gửi link này cho khách qua kênh riêng (Zalo). Khách sẽ chỉ cần: (1) mở link → Thêm phím tắt, (2) chạy lần đầu → nhập mã + Cho phép, (3) tạo Tự động hóa hằng ngày.

> **Mẹo khi làm bản chia sẻ:** ở bước hỏi mã (9a) để trống/không gợi ý mã cụ thể để khách nhập mã của riêng họ. `SERVER_URL` đã điền sẵn trong phím tắt.

## E. Tự động hóa hằng ngày (làm 1 lần trên máy khách)
- **Phím tắt → Tự động hóa → + → Tạo tự động hóa cá nhân → Thời gian trong ngày** (giờ trước giờ chốt, lặp **Hằng ngày**) → **Chạy phím tắt “Vietlott Auto”** → bật **Chạy ngay lập tức** (nếu có) → Xong.
- Tạm dừng: tắt tự động hóa. Cần iPhone bật, có mạng, SIM Vietlott SMS đủ điều kiện/số dư.

## F. Nếu bị kẹt khi làm
- Tên hành động khác: thử tìm tiếng Anh (Text, If, Get Contents of URL, Dictionary, Set Variable, Get File, Save File, Repeat with Each, Send Message, Ask for Input, Show Alert, Stop Shortcut, Wait, Count, Random UUID).
- Kiểm tra: `Lấy tệp` đang trỏ `vietlott_device.json` trong **Phím tắt** và đã tắt “Báo lỗi nếu không tìm thấy”; `Gửi tin nhắn` tới `9969`; Request Body là **JSON** (POST).
- Phần điều kiện `ok` (true/false) có thể hiển thị khác (Có/Không, 1/0) tùy iOS — đặt điều kiện để nhánh lỗi kích hoạt khi `ok` không đúng.
- Chụp màn hình bước đang làm và gửi hỗ trợ để được chỉ cụ thể. Tham khảo spec: `docs/CLIENT_INTEGRATION.md`, `docs/HUONG_DAN_KHACH_IPHONE_DON_GIAN.md`.