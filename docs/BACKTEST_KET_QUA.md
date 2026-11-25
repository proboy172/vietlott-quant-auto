# Kết quả backtest thực tế (minh bạch)

- Ngày chạy: 2026-11-25
- Cửa sổ walk-forward: **500 kỳ gần nhất** (mỗi kỳ chỉ dùng dữ liệu trước đó).
- Mô phỏng: **1 vé đơn** do engine chọn, so sánh với vé ngẫu nhiên (hypergeometric).
- Lưu ý: mẫu vài trăm kỳ là nhỏ; sai lệch vài lần nằm trong nhiễu thống kê.

## 1. Kết quả trúng số

| Trò chơi | Số kỳ | Trúng >=2 số (AI) | Ngẫu nhiên | Trúng >=3 số (có giải) | Ngẫu nhiên | z | p-value |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mega 6/45 | 500 | 75 | 87.65 | 9 | 11.92 | -0.855 | 0.3924 |
| Power 6/55 | 500 | 56 | 61.48 | 9 | 6.66 | 0.911 | 0.3625 |

Phân phối số lần trùng (0..6 số):

- **Mega 6/45**: {0: 215, 1: 210, 2: 66, 3: 9, 4: 0, 5: 0, 6: 0}
- **Power 6/55**: {0: 242, 1: 202, 2: 47, 3: 9, 4: 0, 5: 0, 6: 0}

## 2. Đối chiếu bộ lọc hình thái

| Trò chơi | Tổng kỳ lịch sử | Tỷ lệ kết quả thật nằm trong vùng lọc | Tổng trung bình thực tế | Trung vị lý thuyết |
|---|---:|---:|---:|---:|
| Mega 6/45 | 1395 | 77.71% | 138.27 | 138.0 |
| Power 6/55 | 1428 | 75.98% | 169.43 | 168.0 |

## 3. Kết luận

- Kiểm định z hai phía (p-value trong bảng): nếu **p > 0,05** thì sai lệch so với ngẫu nhiên **không có ý nghĩa thống kê** — tức là không thể nói engine thắng vé random. Với mẫu vài trăm kỳ, hầu hết kết quả sẽ rơi vào trường hợp này.
- `quant_score` là tổng trọng số tự đặt (Bayesian/Markov/Gap/pair/triplet...), **không phải xác suất**. Mỗi tổ hợp 6 số vẫn có xác suất đúng 1/C(45,6) hoặc 1/C(55,6).
- Bộ lọc hình thái có tác dụng thực tế duy nhất: tránh các bộ số đông người chọn, giảm khả năng **chia giải** nếu trúng — không tăng tỷ lệ trúng.
- Xem thêm: `docs/SECURITY_LICENSING.md` (nguyên tắc không cam kết trúng).
