"""Backtest nhanh cho 1 vé đơn và ghi kết quả ra docs/BACKTEST_KET_QUA.md.

Chạy: python backtest_report.py --window 300
"""
import argparse
import datetime
import sys
from pathlib import Path

from backtest_optimizer import evaluate_historical_morphology, theoretical_single_ticket_probs
from data_sync import load_draws
from quant_engine import (
    GAME_CONFIGS,
    analyze_historical_stats,
    generate_1_ticket_optimal,
)

BASE_DIR = Path(__file__).resolve().parent
OUT_DOC = BASE_DIR / "docs" / "BACKTEST_KET_QUA.md"


def run_single_ticket_backtest(game_code: str, window: int) -> dict:
    draws = load_draws(game_code)
    start = max(0, len(draws) - window)
    hits = {m: 0 for m in range(7)}
    for idx in range(start, len(draws)):
        stats = analyze_historical_stats(
            game_code,
            draws_subset=draws[:idx],
            target_date=draws[idx].get("date"),
        )
        plan = generate_1_ticket_optimal(stats)
        predicted = set(plan["tickets"][0]["numbers"])
        actual = set(draws[idx]["main"])
        hits[len(predicted & actual)] += 1

    n = len(draws) - start
    theo = theoretical_single_ticket_probs(GAME_CONFIGS[game_code].max_ball)
    expected_ge2 = sum(theo[m] for m in range(2, 7)) * n
    expected_ge3 = sum(theo[m] for m in range(3, 7)) * n
    return {
        "game": GAME_CONFIGS[game_code].name,
        "window": n,
        "total_draws_available": len(draws),
        "hits": hits,
        "empirical_ge2": sum(hits[m] for m in range(2, 7)),
        "expected_ge2": round(expected_ge2, 2),
        "empirical_ge3": sum(hits[m] for m in range(3, 7)),
        "expected_ge3": round(expected_ge3, 2),
    }


def build_markdown(results: dict, morphologies: dict, window: int) -> str:
    lines = [
        "# Kết quả backtest thực tế (minh bạch)",
        "",
        f"- Ngày chạy: {datetime.date.today().isoformat()}",
        f"- Cửa sổ walk-forward: **{window} kỳ gần nhất** (mỗi kỳ chỉ dùng dữ liệu trước đó).",
        "- Mô phỏng: **1 vé đơn** do engine chọn, so sánh với vé ngẫu nhiên (hypergeometric).",
        "- Lưu ý: mẫu vài trăm kỳ là nhỏ; sai lệch vài lần nằm trong nhiễu thống kê.",
        "",
        "## 1. Kết quả trúng số",
        "",
        "| Trò chơi | Số kỳ | Trúng >=2 số (AI) | Ngẫu nhiên | Trúng >=3 số (có giải) | Ngẫu nhiên |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for code, r in results.items():
        lines.append(
            f"| {r['game']} | {r['window']} | {r['empirical_ge2']} | {r['expected_ge2']} "
            f"| {r['empirical_ge3']} | {r['expected_ge3']} |"
        )
    lines += [
        "",
        "Phân phối số lần trùng (0..6 số):",
        "",
    ]
    for code, r in results.items():
        lines.append(f"- **{r['game']}**: {r['hits']}")
    lines += [
        "",
        "## 2. Đối chiếu bộ lọc hình thái",
        "",
        "| Trò chơi | Tổng kỳ lịch sử | Tỷ lệ kết quả thật nằm trong vùng lọc | Tổng trung bình thực tế | Trung vị lý thuyết |",
        "|---|---:|---:|---:|---:|",
    ]
    for code, m in morphologies.items():
        lines.append(
            f"| {m.get('game', code)} | {m['total_draws']} | {m['relaxed_pass_rate_pct']}% "
            f"| {m['empirical_mean_sum']} | {m['theoretical_median_sum']} |"
        )
    lines += [
        "",
        "## 3. Kết luận",
        "",
        "- Không có bằng chứng engine vượt vé ngẫu nhiên một cách có ý nghĩa. Một trò có thể cao hơn "
        "nhẹ, trò kia thấp hơn kỳ vọng; với mẫu vài trăm kỳ cả hai đều nằm trong nhiễu thống kê. "
        "Cần mẫu lớn hơn và kiểm định ý nghĩa thống kê mới có thể khẳng định.",
        "- `quant_score` là tổng trọng số tự đặt (Bayesian/Markov/Gap/pair/triplet...), **không phải xác suất**. "
        "Mỗi tổ hợp 6 số vẫn có xác suất đúng 1/C(45,6) hoặc 1/C(55,6).",
        "- Bộ lọc hình thái có tác dụng thực tế duy nhất: tránh các bộ số đông người chọn, "
        "giảm khả năng **chia giải** nếu trúng — không tăng tỷ lệ trúng.",
        "- Xem thêm: `docs/SECURITY_LICENSING.md` (nguyên tắc không cam kết trúng).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=300)
    ap.add_argument("--out", default=str(OUT_DOC))
    args = ap.parse_args()

    results = {}
    morphologies = {}
    for code in ("645", "655"):
        results[code] = run_single_ticket_backtest(code, args.window)
        morphologies[code] = evaluate_historical_morphology(code)
        morphologies[code]["game"] = GAME_CONFIGS[code].name
        print(f"[{code}] xong {results[code]['window']} kỳ", flush=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_markdown(results, morphologies, args.window), encoding="utf-8")
    print(f"Da ghi {out_path}")


if __name__ == "__main__":
    main()
