# Design system — Vietlott Auto Flow Landing

Tài liệu này là **chuẩn thiết kế** và “design repo” nội bộ cho landing trong `landing/`. Mọi chỉnh sửa UI sau này phải bám theo để giữ giao diện nhất quán, rõ ràng và tuân thủ.

## 0. Nền tảng & “cấy” hướng dẫn thiết kế (research-backed)

- **Triển khai:** design system trong repo (CSS tokens + component + `sync_results.py`/`sync_winners.py`), **không cấy runtime/template bên ngoài** (Astro/Tailwind/React/Next) để giữ static thuần, không build, dễ deploy và sửa `CONFIG`.
- **Hướng dẫn đã cấy vào tư duy thiết kế (tham chiếu):**
  - **Chính:** [`anthropics/skills` → `frontend-design`](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) — thiết kế có chủ đích, gắn bối cảnh sản phẩm, tránh mặc định/template, lựa chọn palette/typography/layout có lập trường.
  - **Tham chiếu sâu/audit:** [`Zulelee/frontend-design`](https://github.com/Zulelee/frontend-design) (tài liệu + công cụ kiểm tra), [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable) (polish/critique), [`vercel-labs/agent-skills` → `web-design-guidelines`](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) (a11y/UX audit).
- **Bối cảnh & định vị (subject-grounded):** *Vietlott Auto Flow* là **công cụ tự động hóa gửi lệnh SMS Vietlott** (không bán vé, không mua hộ, không đảm bảo trúng). Giao diện phải gợi cảm giác **chuyên nghiệp, đáng tin cậy, “sang” kiểu vé số/jackpot (ruby & gold)** nhưng **minh bạch, bình tĩnh, dễ hiểu** — kể cả người lớn tuổi. Tự động hoàn toàn (Android/iPhone) và **quyền tạm dừng/bật tắt bất cứ lúc nào** là thông điệp trung tâm, phải dễ thấy.
- **Nguyên tắc áp dụng:** nhịp bố cục rõ, bề mặt (surface) có chiều sâu vừa phải, tương phản cao, mục tiêu chạm ≥44px, chữ đọc thoải mái, motion tinh tế và tôn trọng `prefers-reduced-motion`; không emoji, không ảnh bịa, không hứa hẹn trúng thưởng.

## 1. Mục tiêu trải nghiệm & chốt sale rõ ràng
- **Rõ ràng ngay từ đầu:** người xem phải hiểu trong vài giây: đây là **công cụ tự động gửi tin nhắn SMS tới 9969** (Vietlott SMS) từ chính điện thoại/tài khoản của khách — **không bán vé, không mua hộ, không giữ tiền, không đảm bảo trúng**. Tiền vé (nếu gửi thành công) do Vietlott trừ từ tài khoản thanh toán Vietlott SMS của khách.
- **Điểm mạnh nổi bật (phải thể hiện rõ, có căn cứ):** **AI tính toán & gợi ý bộ số theo thuật toán tối ưu** (cá nhân hóa, khách vẫn có thể tự chọn/đổi); **tự động hoàn toàn 24/7**, cài 1 lần không cần thao tác hằng ngày (Android quyền SMS, iPhone Shortcuts); **không bỏ lỡ kỳ quay, không quên, không sai cú pháp** — giúp tham gia đều đặn; **số lượng vé không giới hạn** (tùy số dư/hạn mức Vietlott SMS). Các lợi ích này giúp tăng khả năng tham gia/cơ hội theo lựa chọn của khách, **nhưng không được diễn giải thành cam kết trúng thưởng** (xổ số ngẫu nhiên).
- **FOMO minh bạch:** nhấn mạnh “mỗi kỳ quên là một cơ hội bị bỏ lỡ” (tham gia), countdown kỳ quay/jackpot công khai, **Giá Founder 999.000đ có thể tăng** — nhưng luôn kèm tuyên bố không bán vé/không đảm bảo trúng, không dùng kết quả/ảnh trúng thưởng làm thành tích công cụ.
- **Bố cục phễu dễ hiểu (clarity-first funnel):** giải thích “là gì / không là gì & điểm mạnh” → cách hoạt động + luồng tóm tắt → điều kiện cần có → lợi ích & quyền kiểm soát → giá rõ ràng → **bắt đầu** (ưu tiên dùng thử 0đ, sau đó mua) → cài đặt → (tham khảo) kết quả công khai → FAQ/điều khoản/hỗ trợ.
- **Dễ hiểu cho mọi lứa tuổi (kể cả người lớn):** chữ to, tương phản cao, nút/bấm tối thiểu ~44px, bước/câu ngắn, mobile-first, nút “Chữ to”.
- **Minh bạch & tuân thủ:** nhắc lại “không bán vé / không mua hộ / không đảm bảo trúng”, điều kiện Vietlott SMS, và quyền **tạm dừng/bật tắt tự động** bất cứ lúc nào để tránh gửi lệnh/mua vé ngoài ý muốn.

## 2. Bố cục (layout) — phễu ngắn, rõ (P0)

> **Nguyên tắc P0 (2026-11-22):** bán **sự yên tâm & dịch vụ cài hộ**, không bán sự phức tạp kỹ thuật. Tránh hứa "3 bước tự làm" trong khi iPhone Shortcuts thực tế khó — hãy nói rõ "chúng tôi cài hộ qua Zalo ~5 phút". Một CTA duy nhất (.js-zalo) xuyên suốt trang. Không public số tài khoản giả.

1. **Header** (sticky): logo, menu, nút "Chữ to", **1 CTA Zalo** (không aria-label trùng text).
2. **Hero**: tiêu đề ngắn + CTA "Nhắn Zalo — cài hộ 0đ" + dòng ghi chú cài hộ 1-1 + 4 bullet ngắn + dải minh bạch.
3. **Stats/FOMO**: jackpot công khai, countdown, giá Founder (1 CTA Zalo).
4. **Ticker** + dải nhắc kỳ quay (1 CTA Zalo).
5. **Sản phẩm là gì** (`#san-pham`): 3 thẻ "làm gì / không làm gì / tiền vé & kiểm soát".
6. **Cách hoạt động** (`#cach-hoat-dong`): 3 bước ngắn (cài hộ → tự gửi → tạm dừng) + luồng Bạn → Điện thoại → 9969.
7. **Điều kiện cần có** (`#dieu-kien`): 4 điều kiện Vietlott SMS.
8. **Bảng giá** (`#bang-gia`): 1 gói 999.000đ, dùng thử 7 ngày, giải thích "trọn đời" (CTA Zalo).
9. **Bắt đầu** (`#bat-dau`): dùng thử 0đ (ưu tiên) + form tối giản. **Khối thanh toán tự ẩn** khi `sepayQr`/bank còn placeholder.
10. **Cài đặt** (`#cai-dat`): tab iPhone/Android, nhấn mạnh được cài hộ & tạm dừng.
11. **Kết quả công khai** (`#ket-qua`): **thu gọn trong `<details class="disclosure">`** (mặc định đóng) — không chiếm ưu thế, không coi là thành tích công cụ.
12. **FAQ** (`#hoi-dap`): **6 câu**, `<details>`.
13. **Điều khoản** (`#dieu-khoan`): **thu gọn trong `<details>`**.
14. **Hỗ trợ + Footer + Mobile dock** (dock: 2 nút đều về Zalo).

**Đã bỏ:** section "Lợi ích & kiểm soát" (`#loi-ich`) trùng với clarity card; bỏ lặp disclaimer ở nhiều nơi (giữ 1 dải + footer).

Mục tiêu: mobile < ~14.000px (từ ~24.000px), desktop < ~11.000px (từ ~15.000px); Lighthouse A11y/Best/SEO = 1.0/1.0/1.0; không tràn ngang; không text < 12px.

- `.container` (max 1160px), `.section` / `.section--soft` / `.section--dark`, `.container--narrow` cho khối đọc tập trung.
- Mobile-first: 1 cột → 2/3 cột ở breakpoint lớn. **Không** để tràn ngang; phần tử trang trí (orb, ticker track) phải `overflow` được chứa và không tạo overflow trang (`scrollWidth <= clientWidth`).

## 3. Màu sắc (tokens trong `styles.css :root`)
| Nhóm | Giá trị tiêu biểu | Dùng cho |
|---|---|---|
| Ruby | `--ruby-950..600` (#260306 → #a51422) | Hero/footer/band, nhấn mạnh, CTA nền tối |
| Gold | `--gold-600..100` (#a97d17 → #fbf1d7) | CTA chính, viền, jackpot, shimmer |
| Nền sáng | `--cream/#fbf7ef`, `--paper/#f3ead9`, `--white` | Nền trang, section xen kẽ, thẻ |
| Chữ | `--ink/#171210`, `--ink-2/#3d342c`, `--muted/#6b5f52` | Nội dung |
| Trạng thái | `--green/#1f7a4d` | “Đang bật”, info |

Quy tắc: tối đa 2 màu nhấn (ruby + gold). Trên nền tối dùng trắng/gold nhạt; trên nền sáng dùng ink/muted.

## 4. Typography
- **Font duy nhất:** `Be Vietnam Pro` (Google Fonts, VN đầy đủ). Fallback: `"Segoe UI", Roboto, Arial, sans-serif`.
- Cỡ gốc: `17px` (mobile) → `18px` (≥680px). `html.big-text`: `20px` → `22px` (toggle A+, lưu `localStorage`).
- H1 `clamp(2.35rem,8.2vw,4.25rem)` weight 900; H2 `clamp(1.8rem,5vw,2.9rem)`; body ~1rem, `line-height: 1.65`.
- Không dùng font serif trang trí cho nội dung chính. UI nhỏ (badge/kicker/nhãn, ball, code) **tối thiểu 0.8rem ≈ 13px trên mobile** — từng đo thực tế; không để chữ < 12px (đặc biệt người lớn tuổi).

## 5. Thành phần (components)
- **Button:** pill, ≥44px (CTA lớn ≥56px), `.btn-gold` (chính), `.btn-outline-light`, `.btn-dark`, `.btn-light`, `.btn-ghost`. Hover/active rõ.
- **Card/panel:** nền trắng/kem, viền `--line`, bo góc `--radius/--radius-lg`, bóng mềm.
- **Clarity cards** (`.clarity-grid` / `.clarity-card`): 3 thẻ “làm gì / không làm gì / tiền vé & kết quả” để xóa nhầm lẫn bán vé ngay từ đầu.
- **Flow summary** (`.flow-note`): Bạn → Điện thoại → 9969 (Vietlott) để tóm tắt cơ chế một nhìn.
- **Steps** (`.steps` / `.step-card`) + **Conditions** (`.conditions`): 3 bước + 4 điều kiện Vietlott SMS, nhắc tạm dừng.
- **Start paths** (`.start-paths`): 2 lộ trình “Dùng thử 0đ (khuyên dùng)” vs “Mua gói” để chốt sale không gây áp lực, kèm form/QR/CK phía dưới.
- **Bóng số (ball):** tròn, gradient đỏ + viền vàng, số trắng; đặc biệt nền vàng. Dùng chung cho minh họa, kết quả, lịch sử. Kết quả chính: 1 hàng cố định (flex nowrap) — **không xuống 2 hàng** ở 360–1280px.
- **Result board + winners gallery:** dữ liệu công khai Vietlott, logo thật (`landing/assets/*.png`), ảnh chủ nhân Jackpot từ `winners.js`/`CONFIG.draws.images` (chỉ nguồn chính thức/có quyền, có ghi nguồn); **không bịa**, không coi là thành tích công cụ.
- **Tabs (iPhone/Android):** ARIA tablist/tabpanel, phím ← →.
- **Form:** label rõ, báo lỗi `aria-live`, nút copy, nội dung CK `AUTOFLOW <SĐT>`.
- **FAQ:** `<details>/<summary>` native (6 câu).
- **Disclosure** (`.disclosure`): khối thu gọn cho kết quả công khai & điều khoản; `<summary>` ≥44px, có dấu +/−. Mặc định đóng.
- **Deep-link Zalo:** `zaloUrl(text)` nối `?text=` vào `CONFIG.supportZalo`; 3 mẫu tin trong `CONFIG.zaloPrefill` (trial/ios/android). Khi khách đã điền form, `bindForm()` tạo tin cá nhân hóa (họ tên, SĐT, mã CK).

## 6. Icon & hình ảnh
- **Icon:** SVG sprite nội bộ trong `index.html` (`<symbol id="i-...">`), stroke nhất quán — **không dùng emoji** trong UI.
- **Logo/branding Vietlott:** file thật trong `landing/assets/` (`power655.png`, `mega645.png`, `vietlott-logo.png`) lấy từ trang chính thức; hiển thị kèm ghi nhận nguồn/kết quả công khai.
- **Ảnh người trúng/trao giải:** chỉ khi có file/URL chính thức hoặc được cấp quyền; nếu chưa có thì ẩn gallery.

## 7. Chuyển động (motion)
- Cho phép: shimmer jackpot, marquee ticker, float orb nhẹ, reveal-on-scroll, pulse dot.
- **Bắt buộc** `prefers-reduced-motion: reduce` (tắt animation/transition, reveal hiện ngay).

## 8. Truy cập & responsive
- Breakpoints chính: 480 / 680 / 860 / 980 / 1180 (+ thu gọn header 980–1179, ẩn brand text <380px).
- Kiểm tra 1280/1024/768/390/360: không tràn ngang, bóng số 1 hàng, header không chồng, footer/nav bấm được.
- `lang="vi"`, focus-visible, skip-link, dock mobile cố định.

## 9. Dữ liệu & nội dung động
- **`landing/draws.js`**: sinh bởi `landing/sync_results.py` — nguồn chính trang Vietlott + gộp lịch sử `data/power645.jsonl`, `data/power655.jsonl`. Chứa `latest`, `history`, `schedule`, `source`, `generatedAt`. Cập nhật:
  ```bash
  python landing/sync_results.py
  ```
- **`landing/winners.js`**: khoảnh khắc chủ nhân Jackpot chính thức (`window.VIETLOTT_WINNERS`, ảnh `media.vietlott.vn`, có nguồn). `sync_winners.py` best-effort; giữ file cũ nếu không parse được.
- **`CONFIG` trong `site.js`**: cấu hình/giá/link/SePay/bank/nội dung/FAQ + fallback kết quả. `applyRemoteDraws()` ưu tiên `window.VIETLOTT_DRAWS`. Hero/start/steps/benefits/price/FAQ render từ CONFIG.
- **Countdown:** tính kỳ quay tiếp theo theo lịch (645: T4,T6,CN; 655: T3,T5,T7) và `cutoffHour` (chốt lệnh SMS) — không giả định ngày cố định.
- **Không bịa** kết quả hay hình ảnh. Placeholder thanh toán/Zalo/link iOS/Android/contact hợp lệ khi chưa có thông tin thật.

## 10. Khi thêm/sửa giao diện/nội dung
1. Sửa token trong `:root` trước, không rải giá trị rời rạc. Dùng component/icon sprite có sẵn; thêm mới thì ghi vào file này.
2. Giữ **phễu rõ ràng**: giải thích công cụ là gì/không là gì → cách hoạt động + điều kiện → giá → bắt đầu (dùng thử 0đ ưu tiên) → cài đặt → tham khảo công khai → FAQ/điều khoản/hỗ trợ. Tránh đưa kết quả/ảnh trúng thưởng như bằng chứng của công cụ.
3. Kiểm tra: 360/390/768/1024/1280, nút “Chữ to”, `node --check landing/site.js landing/draws.js landing/winners.js`, không lỗi console, không emoji, không tràn ngang, form/copy/countdown/tab chạy.
   - Mỗi lần sửa CSS/JS phải **tăng `?v=` trong `index.html`** (hiện `v=20`; landing public tại `https://landing.jbai.vn/`) nếu không browser dùng file cache cũ. Khi đổi domain: cập nhật canonical/OG trong `index.html`, `sitemap.xml`, `robots.txt`.
   - Chạy Lighthouse: A11y/Best/SEO phải 1.0; kiểm tra `label-content-name-mismatch` (không đặt `aria-label` trùng/khác text hiển thị) và `color-contrast` (footer-note ≥4.5:1).
   - Kiểm tra placeholder: khối thanh toán phải ẩn khi chưa có SePay/bank thật; không public số TK giả.
   - **P1:** mọi nút `.js-zalo` phải có `?text=` (từ `CONFIG.zaloPrefill`), iOS/Android có tin nhắn riêng; `#install-media` phải `hidden` khi `CONFIG.demoVideoUrl` trống ( video MP4/WebM, ảnh, hoặc YouTube embed đều được).
4. Giữ tuyên bố minh bạch (không bán vé, không mua hộ, không đảm bảo trúng, tạm dừng bất cứ lúc nào) dễ thấy ở hero, clarity, điều kiện, bắt đầu, footer/disclaimer.