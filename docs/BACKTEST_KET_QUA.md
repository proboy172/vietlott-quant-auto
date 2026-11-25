# Kết quả backtest thực tế (minh bạch)

- Ngày chạy: 2026-11-25
- Cửa sổ walk-forward: **300 kỳ gần nhất** (mỗi kỳ chỉ dùng dữ liệu trước đó).
- Mô phỏng: **1 vé đơn** do engine chọn, so sánh với vé ngẫu nhiên (hypergeometric).
- Lưu ý: mẫu vài trăm kỳ là nhỏ; sai lệch vài lần nằm trong nhiễu thống kê.

## 1. Kết quả trúng số

| Trò chơi | Số kỳ | Trúng >=2 số (AI) | Ngẫu nhiên | Trúng >=3 số (có giải) | Ngẫu nhiên |
|---|---:|---:|---:|---:|---:|
| Mega 6/45 | 300 | 51 | 52.59 | 6 | 7.15 |
| Power 6/55 | 300 | 38 | 36.89 | 7 | 4.0 |

Phân phối số lần trùng (0..6 số):

- **Mega 6/45**: {0: 125, 1: 124, 2: 45, 3: 6, 4: 0, 5: 0, 6: 0}
- **Power 6/55**: {0: 142, 1: 120, 2: 31, 3: 7, 4: 0, 5: 0, 6: 0}

## 2. Đối chiếu bộ lọc hình thái

| Trò chơi | Tổng kỳ lịch sử | Tỷ lệ kết quả thật nằm trong vùng lọc | Tổng trung bình thực tế | Trung vị lý thuyết |
|---|---:|---:|---:|---:|
| Mega 6/45 | 1395 | 77.71% | 138.27 | 138.0 |
| Power 6/55 | 1428 | 75.98% | 169.43 | 168.0 |

## 3. Kết luận

- Không có bằng chứng engine vượt vé ngẫu nhiên một cách có ý nghĩa. Mega 6/45 trúng >=3 số **6 kỳ** so với **7,15** kỳ mong đợi; Power 6/55 trúng **7 kỳ** so với **4,0** kỳ mong đợi (cao hơn nhẹ nhưng mẫu 300 kỳ quá nhỏ, nằm trong nhiễu thống kê). Cần mẫu lớn hơn nhiều và kiểm định ý nghĩa thống kê mới có thể khẳng định.
- `quant_score` là tổng trọng số tự đặt (Bayesian/Markov/Gap/pair/triplet...), **không phải xác suất**. Mỗi tổ hợp 6 số vẫn có xác suất đúng 1/C(45,6) hoặc 1/C(55,6).
- Bộ lọc hình thái có tác dụng thực tế duy nhất: tránh các bộ số đông người chọn, giảm khả năng **chia giải** nếu trúng — không tăng tỷ lệ trúng.
- Xem thêm: `docs/SECURITY_LICENSING.md` (nguyên tắc không cam kết trúng).
