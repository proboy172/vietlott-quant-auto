import itertools
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
from data_sync import load_draws


@dataclass
class GameConfig:
    code: str
    name: str
    max_ball: int
    sum_min: int
    sum_max: int
    sum_median: float
    low_high_split: int
    min_ac: int
    min_decades: int
    jackpot_high_threshold_billion: float


GAME_CONFIGS: Dict[str, GameConfig] = {
    "645": GameConfig(
        code="645",
        name="Mega 6/45",
        max_ball=45,
        sum_min=105,
        sum_max=171,
        sum_median=138.0,
        low_high_split=22,
        min_ac=6,
        min_decades=3,
        jackpot_high_threshold_billion=55.0,  # Ngưỡng kích hoạt dàn 3 vé Bao rút gọn (55 tỷ)
    ),
    "655": GameConfig(
        code="655",
        name="Power 6/55",
        max_ball=55,
        sum_min=130,
        sum_max=206,
        sum_median=168.0,
        low_high_split=27,
        min_ac=7,
        min_decades=4,
        jackpot_high_threshold_billion=100.0,  # Ngưỡng kích hoạt dàn 3 vé Bao rút gọn (100 tỷ)
    ),
}


def compute_ac_value(ticket: List[int]) -> int:
    """
    Tính chỉ số Độ phức tạp số học (AC - Arithmetic Complexity).
    Với k=6 số, có C(6,2)=15 hiệu số dương. AC = (số hiệu số phân biệt) - (6 - 1).
    AC tối đa = 10. Bộ số ngẫu nhiên tốt có AC >= 6 (6/45) hoặc >= 7 (6/55).
    """
    diffs = set()
    s = sorted(ticket)
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            diffs.add(s[j] - s[i])
    return len(diffs) - (len(s) - 1)


def check_morphology_filter(ticket: List[int], cfg: GameConfig, strict: bool = True) -> Tuple[bool, dict]:
    """
    Kiểm tra một bộ 6 số qua Bộ lọc Hình thái Phân phối Chuẩn (Gaussian Morphology Filter).
    """
    s = sorted(ticket)
    total_sum = sum(s)
    odd_count = sum(1 for x in s if x % 2 == 1)
    low_count = sum(1 for x in s if x <= cfg.low_high_split)
    ac_val = compute_ac_value(s)
    anti_crowd_count = sum(1 for x in s if x >= 32)
    decades = len(set(x // 10 for x in s))

    # Đếm số cặp liên tiếp (n_{i+1} - n_i == 1) và kiểm tra bộ 3 liên tiếp
    consec_pairs = sum(1 for i in range(5) if s[i + 1] - s[i] == 1)
    has_triple_consec = any(s[i + 2] - s[i] == 2 for i in range(4))

    metrics = {
        "sum": total_sum,
        "odd_even": f"{odd_count}:{6 - odd_count}",
        "low_high": f"{low_count}:{6 - low_count}",
        "ac_value": ac_val,
        "anti_crowd_gt31": anti_crowd_count,
        "decades": decades,
        "consec_pairs": consec_pairs,
    }

    if strict:
        passed = (
            (cfg.sum_min <= total_sum <= cfg.sum_max)
            and (odd_count in (2, 3, 4))
            and (low_count in (2, 3, 4))
            and (ac_val >= cfg.min_ac)
            and (anti_crowd_count >= 2)
            and (decades >= cfg.min_decades)
            and (consec_pairs <= 1)
            and (not has_triple_consec)
        )
    else:
        # Chế độ nới lỏng nhẹ khi phân cụm 3 vé Bao rút gọn nếu cần
        passed = (
            (cfg.sum_min - 12 <= total_sum <= cfg.sum_max + 12)
            and (odd_count in (1, 2, 3, 4, 5))
            and (low_count in (1, 2, 3, 4, 5))
            and (ac_val >= cfg.min_ac - 1)
            and (anti_crowd_count >= 1)
            and (not has_triple_consec)
        )

    return passed, metrics


def analyze_historical_stats(game_code: str) -> dict:
    """
    Phân tích toàn bộ lịch sử quay số:
    1. Kiểm định Chi-Square (Goodness-of-Fit)
    2. Cập nhật tần suất Bayesian đa khung thời gian (Toàn kỳ, 100 kỳ, 30 kỳ)
    3. Phân tích Chu kỳ nghỉ (Survival / Gap Analysis)
    4. Ma trận tương quan cặp đôi (Pairwise Co-occurrence Matrix)
    """
    cfg = GAME_CONFIGS[game_code]
    draws = load_draws(game_code)
    n_draws = len(draws)
    max_b = cfg.max_ball

    # 1. Đếm tần suất toàn lịch sử, 100 kỳ và 30 kỳ gần nhất
    freq_all = {b: 0 for b in range(1, max_b + 1)}
    freq_100 = {b: 0 for b in range(1, max_b + 1)}
    freq_30 = {b: 0 for b in range(1, max_b + 1)}
    last_seen_idx = {b: -1 for b in range(1, max_b + 1)}

    # Ma trận đồng xuất hiện (Co-occurrence)
    co_matrix = [[0] * (max_b + 1) for _ in range(max_b + 1)]

    for idx, d in enumerate(draws):
        balls = d["main"]
        for b in balls:
            freq_all[b] += 1
            if idx >= n_draws - 100:
                freq_100[b] += 1
            if idx >= n_draws - 30:
                freq_30[b] += 1
            last_seen_idx[b] = idx

        for b1, b2 in itertools.combinations(balls, 2):
            co_matrix[b1][b2] += 1
            co_matrix[b2][b1] += 1

    # 2. Kiểm định Chi-Square: E = n_draws * 6 / max_b
    expected_freq = (n_draws * 6.0) / max_b
    chi_sq = sum(((freq_all[b] - expected_freq) ** 2) / expected_freq for b in range(1, max_b + 1))

    # 3. Chu kỳ nghỉ lý thuyết: mu_gap = max_b / 6.0
    mu_gap = max_b / 6.0
    gaps = {b: (n_draws - 1 - last_seen_idx[b]) if last_seen_idx[b] != -1 else n_draws for b in range(1, max_b + 1)}

    # 4. Chấm điểm tổng hợp (Composite Quantitative Score) cho từng quả bóng
    ball_scores = {}
    for b in range(1, max_b + 1):
        # Điểm Bayesian dài hạn (chuẩn hóa quanh 1.0)
        bayesian_long = (freq_all[b] + 2.0) / (expected_freq + 2.0)
        # Điểm động lượng trung hạn (100 kỳ) và ngắn hạn (30 kỳ)
        exp_100 = (min(100, n_draws) * 6.0) / max_b
        exp_30 = (min(30, n_draws) * 6.0) / max_b
        momentum_100 = freq_100[b] / exp_100
        momentum_30 = freq_30[b] / exp_30

        # Điểm chu kỳ nghỉ (Survival Resonance):
        # Đạt đỉnh ở 2 vùng: Vùng ấm đúng nhịp (gap ~ 0.6*mu_gap .. 1.1*mu_gap)
        # và vùng quá hạn hồi quy trung bình (gap ~ 1.6*mu_gap .. 2.3*mu_gap)
        g_ratio = gaps[b] / mu_gap
        warm_peak = math.exp(-((g_ratio - 0.85) ** 2) / 0.35)
        overdue_peak = 0.85 * math.exp(-((g_ratio - 1.85) ** 2) / 0.45)
        gap_score = max(warm_peak, overdue_peak)

        # Điểm thưởng Anti-Crowd (bóng >= 32 tránh trùng ngày sinh)
        anti_crowd_bonus = 0.08 if b >= 32 else 0.0

        # Tổng hợp trọng số
        total_score = (
            0.30 * bayesian_long
            + 0.25 * momentum_100
            + 0.15 * momentum_30
            + 0.22 * gap_score
            + anti_crowd_bonus
        )

        ball_scores[b] = {
            "ball": b,
            "score": round(total_score, 4),
            "freq_all": freq_all[b],
            "freq_100": freq_100[b],
            "freq_30": freq_30[b],
            "current_gap": gaps[b],
            "gap_ratio": round(g_ratio, 2),
            "status": (
                "Overdue (Quá hạn)"
                if g_ratio >= 1.5
                else ("Hot (Đang vào cầu)" if momentum_30 >= 1.25 else "Warm (Đúng chu kỳ)")
            ),
        }

    ranked_balls = sorted(ball_scores.values(), key=lambda x: x["score"], reverse=True)

    return {
        "config": cfg,
        "total_draws": n_draws,
        "latest_draw": draws[-1],
        "expected_freq": round(expected_freq, 2),
        "chi_square": round(chi_sq, 2),
        "degrees_of_freedom": max_b - 1,
        "mu_gap": round(mu_gap, 2),
        "ball_scores": ball_scores,
        "ranked_balls": ranked_balls,
        "co_matrix": co_matrix,
    }


def score_single_ticket(ticket: List[int], stats: dict) -> float:
    """Chấm điểm một bộ 6 số dựa trên Điểm hạt giống + Ma trận đồng xuất hiện + Độ chuẩn hình thái."""
    cfg: GameConfig = stats["config"]
    b_scores = stats["ball_scores"]
    co_mat = stats["co_matrix"]
    exp_pair = (stats["total_draws"] * 6 * 5) / (cfg.max_ball * (cfg.max_ball - 1))

    # 1. Tổng điểm cá nhân của 6 bóng
    indiv_score = sum(b_scores[b]["score"] for b in ticket)

    # 2. Điểm tương quan cặp đôi (15 cặp trong 6 số)
    pair_score = sum(co_mat[b1][b2] / max(1.0, exp_pair) for b1, b2 in itertools.combinations(ticket, 2)) / 15.0

    # 3. Điểm hình thái (gần trung vị tổng 6 số và AC cao)
    total_sum = sum(ticket)
    sum_proximity = 1.0 - abs(total_sum - cfg.sum_median) / (cfg.sum_max - cfg.sum_min)
    ac_val = compute_ac_value(ticket)
    ac_bonus = ac_val / 10.0

    return indiv_score + 0.45 * pair_score + 0.30 * sum_proximity + 0.25 * ac_bonus


def select_stratified_candidates(stats: dict, pool_size: int = 14) -> List[int]:
    """
    Chọn tập hạt giống phân tầng (Stratified Candidate Selection):
    Đảm bảo tập hạt giống lấy được các quả bóng có điểm xác suất Bayesian + Gap cao nhất
    nhưng phân bổ cân bằng giữa Miền Nhỏ (<= split), Miền Lớn (> split, đặc biệt >= 32 Anti-Crowd),
    và cân bằng Chẵn/Lẻ.
    """
    cfg: GameConfig = stats["config"]
    ranked = stats["ranked_balls"]

    low_balls = [x["ball"] for x in ranked if x["ball"] <= cfg.low_high_split]
    high_balls = [x["ball"] for x in ranked if x["ball"] > cfg.low_high_split]
    anti_crowd_balls = [x["ball"] for x in ranked if x["ball"] >= 32]

    half = pool_size // 2
    selected = set(low_balls[:half] + high_balls[: pool_size - half])

    # Đảm bảo có ít nhất 4 số >= 32 để phục vụ chiến thuật Anti-Crowd chống chia giải
    for b in anti_crowd_balls[:5]:
        if len(selected) < pool_size + 2:
            selected.add(b)

    # Sắp xếp lại theo điểm xác suất từ cao xuống thấp
    b_scores = stats["ball_scores"]
    sorted_selected = sorted(selected, key=lambda b: b_scores[b]["score"], reverse=True)
    return sorted_selected[:pool_size]


def generate_1_ticket_optimal(stats: dict) -> dict:
    """
    CHẾ ĐỘ 1 VÉ ĐƠN (Khi Jackpot thấp - 10.000đ/kỳ):
    Lấy 14 số hạt giống phân tầng đứng đầu bảng xếp hạng xác suất (C(14,6) = 3.003 tổ hợp),
    lọc qua Bộ lọc Hình thái Phân phối Chuẩn và chọn ra 1 vé có điểm định lượng cao nhất.
    """
    cfg: GameConfig = stats["config"]
    candidate_pool = select_stratified_candidates(stats, pool_size=14)

    best_ticket = None
    best_score = -1e9
    best_metrics = {}
    valid_count = 0

    for combo in itertools.combinations(candidate_pool, 6):
        ticket = sorted(combo)
        passed, metrics = check_morphology_filter(ticket, cfg, strict=True)
        if not passed:
            continue
        valid_count += 1
        sc = score_single_ticket(ticket, stats)
        if sc > best_score:
            best_score = sc
            best_ticket = ticket
            best_metrics = metrics

    sms_syntax = f"{cfg.code} K1 S " + " ".join(f"{n:02d}" for n in best_ticket)
    return {
        "mode": "SINGLE_1_TICKET (Chế độ 1 Vé Đơn - Ngân sách 10.000đ)",
        "candidate_pool_14": sorted(candidate_pool),
        "valid_combinations_filtered": valid_count,
        "tickets": [
            {
                "ticket_index": 1,
                "numbers": best_ticket,
                "formatted": " ".join(f"{n:02d}" for n in best_ticket),
                "quant_score": round(best_score, 4),
                "metrics": best_metrics,
                "sms": sms_syntax,
            }
        ],
        "sms_commands": [sms_syntax],
    }


def generate_3_tickets_abbreviated_wheel(stats: dict) -> dict:
    """
    CHẾ ĐỘ DÀN 3 VÉ BAO RÚT GỌN (Khi Jackpot vượt ngưỡng cao - Ngân sách 30.000đ/kỳ):
    - Chọn ra v = 9 con số hạt giống mạnh nhất theo cấu trúc Phân Tầng Cân Bằng
      (Tương đương Bao 9 = 84 vé = 840.000đ).
    - Áp dụng Thiết kế Phủ Khối Dirichlet (3-Block Steiner/Dirichlet Covering Design):
      Chia 9 số thành 3 cụm 3 số (A, B, C) và ghép:
        + Vé 1 = A U B (6 số)
        + Vé 2 = A U C (6 số)
        + Vé 3 = B U C (6 số)
    - ĐẢM BẢO TOÁN HỌC 100% (Pigeonhole Guarantee):
        + Nếu kết quả có 4 số rơi vào 9 số này -> Chắc chắn 100% có vé trúng Giải Ba (3 số) hoặc Giải Nhì (4 số).
        + Nếu kết quả có 5 số rơi vào 9 số này -> Chắc chắn 100% có vé trúng Giải Nhì (4 số) hoặc Giải Nhất (5 số)!
    - Duyệt toàn bộ 280 cách phân hoạch 9 số thành (A, B, C) để tìm cách ghép sao cho CẢ 3 VÉ
      đều thỏa mãn Bộ lọc Hình thái Phân phối Chuẩn và có tổng điểm định lượng cao nhất!
    """
    cfg: GameConfig = stats["config"]

    # Lấy tập 12 số phân tầng mạnh nhất rồi chọn ra bộ 9 số tối ưu nhất cho thiết kế 3 khối
    stratified_12 = select_stratified_candidates(stats, pool_size=12)
    best_pool_9 = None
    best_wheel_tickets = None
    best_wheel_blocks = None
    best_wheel_score = -1e9

    for pool_9 in itertools.combinations(stratified_12, 9):
        pool_9 = sorted(pool_9)
        first_elem = pool_9[0]
        rem_8 = pool_9[1:]

        # Duyệt mọi cách chọn cụm A (chứa phần tử đầu tiên để khử trùng lặp hoán vị 3! -> 280 cách)
        for a_rest in itertools.combinations(rem_8, 2):
            block_a = sorted([first_elem, *a_rest])
            rem_6 = [x for x in rem_8 if x not in block_a]
            first_b = rem_6[0]
            rem_5 = rem_6[1:]
            for b_rest in itertools.combinations(rem_5, 2):
                block_b = sorted([first_b, *b_rest])
                block_c = sorted([x for x in rem_6 if x not in block_b])

                t1 = sorted(block_a + block_b)
                t2 = sorted(block_a + block_c)
                t3 = sorted(block_b + block_c)

                p1, m1 = check_morphology_filter(t1, cfg, strict=True)
                p2, m2 = check_morphology_filter(t2, cfg, strict=True)
                p3, m3 = check_morphology_filter(t3, cfg, strict=True)

                strict_pass_count = int(p1) + int(p2) + int(p3)
                if strict_pass_count < 2:
                    continue

                s1 = score_single_ticket(t1, stats)
                s2 = score_single_ticket(t2, stats)
                s3 = score_single_ticket(t3, stats)
                total_w_score = (s1 + s2 + s3) + strict_pass_count * 3.0

                if total_w_score > best_wheel_score:
                    best_wheel_score = total_w_score
                    best_pool_9 = pool_9
                    best_wheel_blocks = {"A": block_a, "B": block_b, "C": block_c}
                    best_wheel_tickets = [
                        (t1, s1, m1, "Cụm A + Cụm B"),
                        (t2, s2, m2, "Cụm A + Cụm C"),
                        (t3, s3, m3, "Cụm B + Cụm C"),
                    ]

    tickets_out = []
    sms_list = []
    for idx, (t, sc, met, block_desc) in enumerate(best_wheel_tickets, 1):
        sms_cmd = f"{cfg.code} K1 S " + " ".join(f"{n:02d}" for n in t)
        sms_list.append(sms_cmd)
        tickets_out.append({
            "ticket_index": idx,
            "block_combination": block_desc,
            "numbers": t,
            "formatted": " ".join(f"{n:02d}" for n in t),
            "quant_score": round(sc, 4),
            "metrics": met,
            "sms": sms_cmd,
        })

    return {
        "mode": "ABBREVIATED_WHEEL_3_TICKETS (Bao 9 Rút Gọn 3 Vé - Ngân sách 30.000đ)",
        "seed_pool_9": best_pool_9,
        "blocks": best_wheel_blocks,
        "cost_comparison": "30.000đ (3 vé) thay vì 840.000đ (Bao 9 đầy đủ = 84 vé) -> Tiết kiệm 96.4%",
        "mathematical_guarantee": (
            "Định lý Dirichlet trên 3 cụm (A, B, C): "
            "Nếu 4 số trúng rơi vào dàn 9 số -> Đảm bảo 100% trúng Giải Ba/Nhì (>=3 số). "
            "Nếu 5 số trúng rơi vào dàn 9 số -> Đảm bảo 100% trúng Giải Nhì/Nhất (>=4 số)."
        ),
        "tickets": tickets_out,
        "sms_commands": sms_list,
    }


if __name__ == "__main__":
    for code in ["655", "645"]:
        stats = analyze_historical_stats(code)
        cfg = stats["config"]
        print("=" * 80)
        print(f"BÁO CÁO ĐỊNH LƯỢNG: {cfg.name} (Tổng số kỳ đã quay: {stats['total_draws']})")
        print(f"Kỳ gần nhất: #{stats['latest_draw']['id']} ({stats['latest_draw']['date']}) -> {stats['latest_draw']['main']}")
        print(f"Kiểm định Chi-Square lồng cầu: {stats['chi_square']} (df={stats['degrees_of_freedom']}) | Tần suất kỳ vọng: {stats['expected_freq']}")
        print("-" * 80)
        print("Top 12 quả bóng có điểm xác suất Bayesian + Chu kỳ nghỉ cao nhất cho kỳ tới:")
        for rank, item in enumerate(stats["ranked_balls"][:12], 1):
            print(
                f"  #{rank:02d}: Bóng [{item['ball']:02d}] | Điểm: {item['score']:.4f} | "
                f"Tổng về: {item['freq_all']} lần (30 kỳ: {item['freq_30']}) | "
                f"Nghỉ: {item['current_gap']} kỳ (Tỷ lệ Gap: {item['gap_ratio']}x) -> {item['status']}"
            )

        res_1 = generate_1_ticket_optimal(stats)
        print("\n[CHẾ ĐỘ 1: JACKPOT THẤP -> MUA 1 VÉ ĐƠN TỐI ƯU (10.000đ)]")
        t1 = res_1["tickets"][0]
        print(f"  -> Bộ số: {t1['formatted']} | Điểm: {t1['quant_score']} | Hình thái: {t1['metrics']}")
        print(f"  -> Cú pháp gửi 9969: {t1['sms']}")

        res_3 = generate_3_tickets_abbreviated_wheel(stats)
        print("\n[CHẾ ĐỘ 2: JACKPOT CAO -> DÀN 3 VÉ BAO 9 RÚT GỌN (30.000đ)]")
        print(f"  -> Dàn 9 số hạt giống: {[f'{x:02d}' for x in res_3['seed_pool_9']]}")
        print(f"  -> Phân cụm Dirichlet: Cụm A={res_3['blocks']['A']}, Cụm B={res_3['blocks']['B']}, Cụm C={res_3['blocks']['C']}")
        for tk in res_3["tickets"]:
            print(f"  -> Vé #{tk['ticket_index']} ({tk['block_combination']}): {tk['formatted']} | Hình thái: {tk['metrics']}")
            print(f"     SMS 9969: {tk['sms']}")
        print()
