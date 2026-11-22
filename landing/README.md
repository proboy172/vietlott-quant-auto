# Landing page — Vietlott Auto Flow

Static site thuần HTML/CSS/JS. Không cần build tool, không dependency.

## Chạy thử locally
Mở trực tiếp `landing/index.html` trong trình duyệt, hoặc:

```powershell
cd landing
python -m http.server 8080
```

Truy cập `http://localhost:8080` (hard refresh `Ctrl+F5` nếu trình duyệt cache CSS/JS cũ).

## Deploy

**Hiện tại (đã triển khai, 2026-11-22):**
- Landing public: **https://landing.jbai.vn/** — phục vụ tĩnh từ máy chạy 24/7 qua cùng Cloudflare Tunnel `aivietlott`.
- Local static server: `python -m http.server 8090 --bind 127.0.0.1 --directory landing` → tunnel ingress `landing.jbai.vn → http://127.0.0.1:8090`.
- API cấp phép (riêng): **https://aivietlott.jbai.vn** → `http://127.0.0.1:8787` (xem `docs/DEPLOY_AIVIETLOTT_CLOUDFLARE_TUNNEL.md`).
- Khởi động tự động khi login: file `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VietlottAutoFlow.bat` (có guard tránh chạy trùng).

**Deploy chỗ khác (nếu cần):** copy thư mục `landing/` lên GitHub Pages / Netlify / Vercel / hosting tĩnh. Không commit core repo.
- Khi đổi domain: sửa `link[rel=canonical]`, `og:url`, `og:image` trong `index.html`, `sitemap.xml`, `robots.txt`.
- Mỗi lần sửa CSS/JS phải **tăng `?v=`** trong `index.html` (hiện `v=20`) để tránh cache cũ.

## Đồng bộ kết quả Vietlott (1:1 với trang chính thức)

Kết quả hiển thị trên landing lấy từ `landing/draws.js` (dữ liệu công khai Vietlott). Cập nhật:

```bash
python landing/sync_results.py
```

Script sẽ:
- đọc trang kết quả chính thức `vietlott.vn` (Mega 6/45, Power 6/55),
- gộp lịch sử gần nhất từ `data/power645.jsonl` và `data/power655.jsonl`,
- ghi đè `landing/draws.js` (latest + 6 kỳ lịch sử + jackpot + lịch quay).

Chạy lại mỗi ngày sau kỳ quay (hoặc thêm bước vào pipeline/GitHub Actions) để giữ kết quả đồng bộ. Không cần build; refresh trang là thấy dữ liệu mới.

> Lưu ý: trang Vietlott chặn nhúng iframe (`X-Frame-Options: SAMEORIGIN`), nên “1:1” được thực hiện bằng đồng bộ dữ liệu (scrape/copy có kiểm soát) vào `draws.js`, không phải nhúng trực tiếp.

## Ảnh chủ nhân Jackpot (chính thức Vietlott)

Nguồn công khai: <https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/chu-nhan-jackpot> (ảnh tại `media.vietlott.vn`).

- `landing/winners.js` (`window.VIETLOTT_WINNERS`) chứa danh sách khoảnh khắc trúng thưởng đã bóc từ trang trên. Landing tự hiển thị **6 ảnh chọn lọc** (3 Mega 6/45 + 3 Power 6/55) kèm tên/số tiền và ghi nguồn Vietlott khi không có `CONFIG.draws.images` tùy chỉnh.
- Muốn dùng đúng bộ ảnh tự chọn: điền `CONFIG.draws.images` và `CONFIG.draws.imageCaptions` trong `landing/site.js` (chỉ dùng ảnh do Vietlott công bố/có quyền, có ghi nguồn).
- Đồng bộ lại danh sách: `python landing/sync_winners.py` (script thử parse trực tiếp trang; nếu trang đổi cấu trúc và không bóc được mục nào, script sẽ giữ nguyên `winners.js` cũ). Có thể cập nhật thủ công `winners.js` từ dữ liệu trang chính thức.

## Chỉnh nội dung

- **Kết quả/jackpot/lịch sử/lịch quay:** tự động từ `draws.js` (`window.VIETLOTT_DRAWS`). Ưu tiên chạy `sync_results.py`.
- **Cấu hình còn lại:** đầu `landing/site.js` trong `CONFIG`:
  - `brand`, `price`, `fomoPrice`, `cutoffHour`
  - `supportZalo`, `contact`, `shortcutUrl`, `androidUrl`
  - `sepayQr`: URL ảnh QR tĩnh từ SePay (để trống sẽ hiện placeholder)
  - `bank`: tên ngân hàng, số TK, chủ TK, nội dung CK gợi ý
  - `steps`, `benefits`, `priceList`, `faq`
  - `draws.images`: mảng URL ảnh **do Vietlott công bố hoặc có quyền dùng** (chỉ hiển thị khi có). Để trống thì ẩn gallery — **không dùng ảnh giả/người thắng không rõ nguồn**.
  - `draws.latest/history/schedule`: fallback khi chưa có `draws.js`

`site.js` sẽ tự ưu tiên dữ liệu từ `draws.js` nếu có.

## Chế độ gửi & kiểm soát (nội dung trên landing)
- **Số vé:** không giới hạn mỗi lần/kỳ — khách tự chọn bao nhiêu vé tùy ý, miễn tài khoản Vietlott SMS đủ số dư.
- **Tự động gửi hoàn toàn (không cần bấm):** khả dụng trên **Android** (khi khách chủ động cấp quyền gửi SMS/ứng dụng hỗ trợ) và trên **iPhone** qua **Phím tắt/Shortcuts** (theo kịch bản đã kiểm chứng). Tùy thiết bị, phiên bản và cài đặt, cần đảm bảo quyền/tự động hóa được bật.
- **Tạm dừng/Bật tắt:** khách phải luôn có cách tạm dừng hoặc tắt tự động ngay (tắt tự động hóa/Shortcut trên iPhone, tắt tự động trong ứng dụng/cài đặt trên Android, hoặc liên hệ hỗ trợ) để không phát sinh mua vé ngoài ý muốn. Nội dung landing nhấn mạnh quyền kiểm soát này.

## Chuẩn thiết kế (bắt buộc tuân theo)

Xem **`landing/DESIGN.md`** — đây là “design system” nội bộ (thay vì cấy repo thiết kế bên ngoài): bố cục mobile-first, tokens màu ruby/gold, font Be Vietnam Pro, icon SVG sprite (không emoji), component (bóng số 1 hàng không wrap), motion + `prefers-reduced-motion`, quy tắc người lớn tuổi, dữ liệu kết quả thật, tuyên bố minh bạch. Mọi thay đổi UI phải bám theo file này.

## Trạng thái hiện tại
- [x] Bố cục/nội dung landing theo phễu rõ ràng (clarity-first): làm rõ “công cụ tự gửi SMS 9969 là gì/không là gì”, luồng hoạt động, điều kiện Vietlott SMS, lợi ích & kiểm soát (tạm dừng bất cứ lúc nào), giá, lộ trình bắt đầu (dùng thử 0đ ưu tiên / mua gói), cài đặt, FAQ/điều khoản/hỗ trợ.
- [x] Kết quả thật đồng bộ từ Vietlott vào `draws.js` (Power 6/55 & Mega 6/45), logo game chính thức trong `landing/assets/`.
- [x] Khoảnh khắc chủ nhân Jackpot chính thức từ Vietlott (`landing/winners.js`, ảnh `media.vietlott.vn`, chọn lọc 3 Mega 6/45 + 3 Power 6/55, có ghi nguồn) — hiển thị như thông tin công khai tham khảo, không phải thành tích công cụ. Có thể override bằng `CONFIG.draws.images`/`imageCaptions`.
- [x] Form nhập tên + SĐT → tạo nội dung chuyển khoản `AUTOFLOW <SĐT>` + nút copy; nút mở Zalo; tab iPhone/Android; FAQ/lợi ích/quy trình/điều khoản; placeholder thanh toán.
- [ ] Chưa nối SePay webhook. Khi có SePay: cập nhật `CONFIG.sepayQr`, link xác thực/kích hoạt và nối webhook ở backend để tự động cấp quyền.

## Lưu ý nội dung
- Landing tuyệt đối không hứa trúng/lợi nhuận; luôn ghi rõ không bán vé, khách tự gửi 9969 từ SĐT/tài khoản của mình.
- “Trọn đời” = không phí định kỳ + cam kết vận hành/cập nhật 36 tháng; đã nêu trên trang.
- Thay placeholder ngân hàng/QR/Zalo bằng thông tin thật trước khi chạy quảng cáo.