import math
from data_sync import load_draws
from quant_engine import (
    GAME_CONFIGS,
    analyze_historical_stats,
    check_morphology_filter,
    generate_1_ticket_optimal,
    generate_3_tickets_abbreviated_wheel,
)


def theoretical_single_ticket_probs(max_ball: int) -> dict:
    """Tính xác suất lý thuyết (Hypergeometric Distribution) khi mua ngẫu nhiên 1 vé (k=6)."""
    total_combos = math.comb(max_ball, 6)
    probs = {}
    for m in range(7):
        ways = math.comb(6, m) * math.comb(max_ball - 6, 6 - m)
        probs[m] = ways / total_combos
    return probs


def evaluate_historical_morphology(game_code: str) -> dict:
    """
    Kiểm chứng thực nghiệm: Trong toàn bộ lịch sử quay số thật của Vietlott (hơn 1.400 kỳ),
    có bao nhiêu % kết quả thực tế nằm trong vùng Bộ lọc Hình thái của hệ thống?
    """
    draws = load_draws(game_code)
    cfg = GAME_CONFIGS[game_code]
    strict_pass = 0
    relaxed_pass = 0
    sums = []

    for d in draws:
        balls = d["main"]
        sums.append(sum(balls))
        p_strict, _ = check_morphology_filter(balls, cfg, strict=True)
        p_relax, _ = check_morphology_filter(balls, cfg, strict=False)
        if p_strict:
            strict_pass += 1
        if p_relax:
            relaxed_pass += 1

    return {
        "total_draws": len(draws),
        "strict_pass_rate_pct": round(strict_pass * 100.0 / len(draws), 2),
        "relaxed_pass_rate_pct": round(relaxed_pass * 100.0 / len(draws), 2),
        "empirical_mean_sum": round(sum(sums) / len(sums), 2),
        "theoretical_median_sum": cfg.sum_median,
    }


def run_walk_forward_backtest(game_code: str, test_window: int = 200) -> dict:
    """
    Chạy Walk-Forward Backtest (Không nhìn trước tương lai) trên `test_window` kỳ quay gần nhất:
    Tại mỗi kỳ t, chỉ dùng dữ liệu từ kỳ 0 đến t-1 để dự đoán cho kỳ t.
    Đo lường:
    1. Tỷ lệ trúng >= 2 số, >= 3 số (Giải Ba), >= 4 số (Giải Nhì) của Chế độ 1 Vé và Dàn 3 Vé Bao Rút Gọn.
    2. So sánh Hệ số Nâng Xác Suất (Probability Lift Factor) so với mua vé ngẫu nhiên (Quick Pick).
    """
    draws = load_draws(game_code)
    cfg = GAME_CONFIGS[game_code]
    n_total = len(draws)
    start_idx = n_total - test_window

    single_matches = {i: 0 for i in range(7)}
    wheel3_max_matches = {i: 0 for i in range(7)}
    seed9_hits = {i: 0 for i in range(7)}

    for idx in range(start_idx, n_total):
        history_slice = draws[:idx]
        actual_win = set(draws[idx]["main"])

        stats = analyze_historical_stats(game_code, draws_subset=history_slice)
        plan_1 = generate_1_ticket_optimal(stats)
        plan_3 = generate_3_tickets_abbreviated_wheel(stats)

        # Kiểm tra 1 vé đơn
        t1_set = set(plan_1["tickets"][0]["numbers"])
        m1 = len(actual_win.intersection(t1_set))
        single_matches[m1] += 1

        # Kiểm tra dàn 9 số hạt giống và 3 vé Bao rút gọn
        s9_set = set(plan_3["seed_pool_9"])
        s9_hit = len(actual_win.intersection(s9_set))
        seed9_hits[s9_hit] += 1

        best_m3 = max(len(actual_win.intersection(tk["numbers"])) for tk in plan_3["tickets"])
        wheel3_max_matches[best_m3] += 1

    theo = theoretical_single_ticket_probs(cfg.max_ball)
    theo_ge2_1tk = sum(theo[m] for m in range(2, 7)) * test_window
    theo_ge3_1tk = sum(theo[m] for m in range(3, 7)) * test_window

    # Với 3 vé ngẫu nhiên độc lập: P(ít nhất 1 vé >= k) = 1 - (1 - p)^3
    p_ge2 = sum(theo[m] for m in range(2, 7))
    p_ge3 = sum(theo[m] for m in range(3, 7))
    theo_ge2_3tk = (1.0 - (1.0 - p_ge2) ** 3) * test_window
    theo_ge3_3tk = (1.0 - (1.0 - p_ge3) ** 3) * test_window

    emp_ge2_1tk = sum(single_matches[m] for m in range(2, 7))
    emp_ge3_1tk = sum(single_matches[m] for m in range(3, 7))
    emp_ge2_3tk = sum(wheel3_max_matches[m] for m in range(2, 7))
    emp_ge3_3tk = sum(wheel3_max_matches[m] for m in range(3, 7))

    return {
        "game": cfg.name,
        "test_window_draws": test_window,
        "single_ticket_results": {
            "match_distribution": single_matches,
            "empirical_ge2_hits": emp_ge2_1tk,
            "random_expected_ge2_hits": round(theo_ge2_1tk, 2),
            "empirical_ge3_prizes": emp_ge3_1tk,
            "random_expected_ge3_prizes": round(theo_ge3_1tk, 2),
        },
        "wheel3_abbreviated_results": {
            "seed9_hit_distribution": seed9_hits,
            "max_match_distribution": wheel3_max_matches,
            "empirical_ge2_hits": emp_ge2_3tk,
            "random_expected_ge2_hits": round(theo_ge2_3tk, 2),
            "empirical_ge3_prizes": emp_ge3_3tk,
            "random_expected_ge3_prizes": round(theo_ge3_3tk, 2),
        },
    }


if __name__ == "__main__":
    for code in ["645", "655"]:
        morph = evaluate_historical_morphology(code)
        bt = run_walk_forward_backtest(code, test_window=150)
        print("=" * 80)
        print(f"KIỂM CHỨNG THỰC NGHIỆM: {bt['game']}")
        print(f"1. Thống kê Hình thái trên {morph['total_draws']} kỳ lịch sử:")
        print(f"   - Tổng trung bình thực tế: {morph['empirical_mean_sum']} (Lý thuyết: {morph['theoretical_median_sum']})")
        print(f"   - Tỷ lệ kết quả lịch sử nằm trong vùng lọc: {morph['relaxed_pass_rate_pct']}%")
        print(f"2. Kết quả Walk-Forward Backtest (150 kỳ gần nhất):")
        print(f"   - [1 Vé Đơn]: Trúng >=2 số: {bt['single_ticket_results']['empirical_ge2_hits']} kỳ (Ngẫu nhiên: {bt['single_ticket_results']['random_expected_ge2_hits']})")
        print(f"                 Trúng Giải (>=3 số): {bt['single_ticket_results']['empirical_ge3_prizes']} kỳ (Ngẫu nhiên: {bt['single_ticket_results']['random_expected_ge3_prizes']})")
        print(f"   - [Dàn 3 Vé Bao Rút Gọn]: Trúng >=2 số: {bt['wheel3_abbreviated_results']['empirical_ge2_hits']} kỳ (Ngẫu nhiên: {bt['wheel3_abbreviated_results']['random_expected_ge2_hits']})")
        print(f"                             Trúng Giải (>=3 số): {bt['wheel3_abbreviated_results']['empirical_ge3_prizes']} kỳ (Ngẫu nhiên: {bt['wheel3_abbreviated_results']['random_expected_ge3_prizes']})")
        print(f"                             Phân phối số trúng: {bt['wheel3_abbreviated_results']['max_match_distribution']}")

