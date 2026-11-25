import datetime
import hashlib
import itertools
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
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
        jackpot_high_threshold_billion=55.0,
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
        jackpot_high_threshold_billion=100.0,
    ),
}


# --- Xoay vòng theo ngày (daily rotation) -------------------------------------
# Engine vốn deterministic: với cùng 1 tập dữ liệu lịch sử, tổ hợp điểm cao nhất
# luôn là một. Để tránh gửi lại đúng 1 vé mỗi ngày, ta chọn trong tập "gần tối ưu"
# (cách điểm cao nhất không quá ROTATION_EPSILON) bằng một hash ổn định theo ngày.
# Cùng 1 ngày -> cùng 1 lựa chọn; sang ngày khác -> lựa chọn có thể đổi, nhưng vẫn
# nằm trong vùng điểm gần tốt nhất. Có thể loại thêm các vé đã phát gần đây.
ROTATION_EPSILON = 0.15
_OWNER_SALT = os.environ.get("GITHUB_REPOSITORY_OWNER", "proboy172").strip().lower()


def ticket_key(ticket: List[int]) -> str:
    """Khoá canon cho 1 bộ số (dùng để so sánh/loại trừ lặp)."""
    return " ".join(f"{n:02d}" for n in sorted(int(x) for x in ticket))


def daily_rotation_key(stats: dict, candidate_key: str) -> bytes:
    """Hash ổn định theo (ngày, chủ sở hữu, tổ hợp) - không dùng random."""
    day = str(stats.get("target_date") or datetime.date.today().isoformat())
    raw = f"{day}|{_OWNER_SALT}|{candidate_key}".encode("utf-8")
    return hashlib.sha256(raw).digest()


def _pick_daily_best(candidates: List[Tuple], stats: dict,
                     key_func=None, epsilon: float = ROTATION_EPSILON) -> Tuple:
    """
    Chọn 1 candidate từ tập gần tối ưu.
    - candidates: phần tử đầu tiên là điểm số (float), phần tử còn lại là dữ liệu.
    - key_func(candidate) -> khoá canon để hash theo ngày.
    - epsilon: chỉ xét các candidate có điểm >= best - epsilon.
    - stats["exclude_ticket_keys"] (tuỳ chọn): loại các tổ hợp đã phát gần đây.
    """
    if not candidates:
        raise ValueError("Không có candidate hợp lệ để chọn.")
    best_score = max(float(c[0]) for c in candidates)
    near = [c for c in candidates if float(c[0]) >= best_score - epsilon]
    excluded: Set[str] = set(stats.get("exclude_ticket_keys") or set())
    if excluded:
        key_fn = key_func or (lambda c: ticket_key(c[1]))
        fresh = [c for c in near if key_fn(c) not in excluded]
        if fresh:
            near = fresh
    if len(near) == 1:
        return near[0]
    key_fn = key_func or (lambda c: ticket_key(c[1]))
    return max(near, key=lambda c: daily_rotation_key(stats, key_fn(c)))


def compute_ac_value(ticket: List[int]) -> int:
    """
    Tính chỉ số Độ phức tạp số học (AC - Arithmetic Complexity).
    Với k=6 số, có C(6,2)=15 hiệu số dương. AC = (số hiệu số phân biệt) - (6 - 1).
    """
    diffs = set()
    s = sorted(ticket)
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            diffs.add(s[j] - s[i])
    return len(diffs) - (len(s) - 1)


def check_morphology_filter(ticket: List[int], cfg: GameConfig, strict: bool = True) -> Tuple[bool, dict]:
    """
    Bộ lọc Hình thái Phân phối Chuẩn (Gaussian Morphology Filter):
    Loại bỏ các vé nằm ở phần đuôi phân phối xác suất cực hiếm.
    """
    s = sorted(ticket)
    total_sum = sum(s)
    odd_count = sum(1 for x in s if x % 2 == 1)
    low_count = sum(1 for x in s if x <= cfg.low_high_split)
    ac_val = compute_ac_value(s)
    anti_crowd_count = sum(1 for x in s if x >= 32)
    decades = len(set(x // 10 for x in s))

    consec_pairs = sum(1 for i in range(5) if s[i + 1] - s[i] == 1)
    has_triple_consec = any(s[i + 2] - s[i] == 2 for i in range(4))
    last_digits = [x % 10 for x in s]
    unique_last_digits = len(set(last_digits))

    metrics = {
        "sum": total_sum,
        "odd_even": f"{odd_count}:{6 - odd_count}",
        "low_high": f"{low_count}:{6 - low_count}",
        "ac_value": ac_val,
        "anti_crowd_gt31": anti_crowd_count,
        "decades": decades,
        "consec_pairs": consec_pairs,
        "unique_last_digits": unique_last_digits,
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
            and (4 <= unique_last_digits <= 5)
        )
    else:
        passed = (
            (cfg.sum_min - 12 <= total_sum <= cfg.sum_max + 12)
            and (odd_count in (1, 2, 3, 4, 5))
            and (low_count in (1, 2, 3, 4, 5))
            and (ac_val >= cfg.min_ac - 1)
            and (anti_crowd_count >= 1)
            and (not has_triple_consec)
            and (3 <= unique_last_digits <= 6)
        )

    return passed, metrics


def analyze_historical_stats(game_code: str, draws_subset: List[dict] = None,
                             target_date: Optional[str] = None,
                             exclude_ticket_keys: Optional[List[str]] = None) -> dict:
    """
    Lõi Phân tích Định lượng 5 Chiều (5D Quantitative & Markov Engine):
    1. Kiểm định Chi-Square (Goodness-of-Fit)
    2. Tần suất Hậu nghiệm Bayesian Dirichlet-Multinomial (Toàn kỳ, 100 kỳ, 30 kỳ, 10 kỳ)
    3. Phân tích Sinh tồn / Chu kỳ nghỉ (Weibull / Geometric Survival Gap Analysis)
    4. Ma trận Chuyển tiếp Markov Bậc 1 (Lag-1 Markov Transition P(X_t = j | X_{t-1} = i))
    5. Ma trận Tương quan Cặp đôi & Bộ ba (Pairwise & Triplet Affinity)
    """
    cfg = GAME_CONFIGS[game_code]
    draws = draws_subset if draws_subset is not None else load_draws(game_code)
    n_draws = len(draws)
    # Ngày mục tiêu dùng cho daily rotation. Mặc định là ngày hiện tại (UTC+7).
    target_date_str = str(target_date) if target_date else datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=7))
    ).date().isoformat()
    max_b = cfg.max_ball

    freq_all = {b: 0 for b in range(1, max_b + 1)}
    freq_100 = {b: 0 for b in range(1, max_b + 1)}
    freq_30 = {b: 0 for b in range(1, max_b + 1)}
    freq_10 = {b: 0 for b in range(1, max_b + 1)}
    last_seen_idx = {b: -1 for b in range(1, max_b + 1)}

    # Ma trận đồng xuất hiện trong cùng kỳ (Co-occurrence)
    co_matrix = [[0] * (max_b + 1) for _ in range(max_b + 1)]
    # Ma trận chuyển tiếp Markov từ kỳ t-1 sang kỳ t: trans_matrix[prev_ball][next_ball]
    trans_matrix = [[0] * (max_b + 1) for _ in range(max_b + 1)]

    prev_balls = None
    for idx, d in enumerate(draws):
        balls = d["main"]
        for b in balls:
            freq_all[b] += 1
            if idx >= n_draws - 100:
                freq_100[b] += 1
            if idx >= n_draws - 30:
                freq_30[b] += 1
            if idx >= n_draws - 10:
                freq_10[b] += 1
            last_seen_idx[b] = idx

        for b1, b2 in itertools.combinations(balls, 2):
            co_matrix[b1][b2] += 1
            co_matrix[b2][b1] += 1

        if prev_balls is not None:
            for pb in prev_balls:
                for nb in balls:
                    trans_matrix[pb][nb] += 1
        prev_balls = balls

    expected_freq = (n_draws * 6.0) / max_b
    chi_sq = sum(((freq_all[b] - expected_freq) ** 2) / expected_freq for b in range(1, max_b + 1))

    mu_gap = max_b / 6.0
    gaps = {b: (n_draws - 1 - last_seen_idx[b]) if last_seen_idx[b] != -1 else n_draws for b in range(1, max_b + 1)}

    # Tập 6 số vừa về ở kỳ gần nhất để tính xác suất chuyển tiếp Markov P(b | last_draw)
    latest_balls = draws[-1]["main"]

    ball_scores = {}
    for b in range(1, max_b + 1):
        bayesian_long = (freq_all[b] + 2.0) / (expected_freq + 2.0)
        exp_100 = (min(100, n_draws) * 6.0) / max_b
        exp_30 = (min(30, n_draws) * 6.0) / max_b
        exp_10 = (min(10, n_draws) * 6.0) / max_b

        momentum_100 = freq_100[b] / exp_100
        momentum_30 = freq_30[b] / exp_30
        momentum_10 = freq_10[b] / exp_10

        # Điểm Markov Transition từ 6 quả bóng của kỳ vừa qua -> kỳ tiếp theo
        # Kỳ vọng mỗi cặp (pb -> b) xuất hiện: freq_all[pb] * (6 / max_b)
        markov_lift_sum = 0.0
        for pb in latest_balls:
            exp_trans = max(1.0, freq_all[pb] * (6.0 / max_b))
            markov_lift_sum += (trans_matrix[pb][b] + 0.5) / (exp_trans + 0.5)
        markov_score = markov_lift_sum / 6.0

        # Điểm Chu kỳ nghỉ theo Mô hình Phân tích Sinh tồn (Weibull & Geometric Hazard Rate):
        # Kết hợp đỉnh nhịp sinh học (Warm Gap 0.8 - 1.2 mu) và lực đẩy bứt phá của bóng nén lâu (Overdue)
        g_ratio = gaps[b] / mu_gap
        warm_peak = math.exp(-((g_ratio - 0.85) ** 2) / 0.35)
        # Weibull hazard function (k=1.15): tỷ lệ rủi ro/khả năng xuất hiện tăng dần theo thời gian tích lũy
        weibull_hazard = ((gaps[b] + 0.5) / mu_gap) ** 0.15
        overdue_peak = min(1.25, 0.80 * weibull_hazard * math.exp(-((max(0.0, g_ratio - 1.8)) ** 2) / 1.2))
        repeat_bonus = 0.75 if gaps[b] == 0 else 0.0
        gap_score = max(warm_peak, overdue_peak, repeat_bonus)

        # Tổng hợp điểm xác suất trúng thực nghiệm (tối ưu hóa cho Hit Rate >= 3 số)
        total_score = (
            0.24 * bayesian_long
            + 0.20 * momentum_100
            + 0.16 * momentum_30
            + 0.08 * momentum_10
            + 0.18 * markov_score
            + 0.14 * gap_score
        )

        ball_scores[b] = {
            "ball": b,
            "score": round(total_score, 4),
            "markov_lift": round(markov_score, 3),
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
        "target_date": target_date_str,
        "exclude_ticket_keys": set(exclude_ticket_keys or []),
        "latest_draw": draws[-1],
        "expected_freq": round(expected_freq, 2),
        "chi_square": round(chi_sq, 2),
        "degrees_of_freedom": max_b - 1,
        "mu_gap": round(mu_gap, 2),
        "ball_scores": ball_scores,
        "ranked_balls": ranked_balls,
        "co_matrix": co_matrix,
        "trans_matrix": trans_matrix,
    }


def select_stratified_candidates(stats: dict, pool_size: int = 14) -> List[int]:
    """
    Chọn tập hạt giống phân tầng (Stratified Candidate Selection):
    Lấy những bóng có điểm Bayesian + Markov + Gap cao nhất ở cả miền Nhỏ và miền Lớn.
    """
    cfg: GameConfig = stats["config"]
    ranked = stats["ranked_balls"]

    low_balls = [x["ball"] for x in ranked if x["ball"] <= cfg.low_high_split]
    high_balls = [x["ball"] for x in ranked if x["ball"] > cfg.low_high_split]
    anti_crowd_balls = [x["ball"] for x in ranked if x["ball"] >= 32]

    half = pool_size // 2
    selected = set(low_balls[:half] + high_balls[: pool_size - half])

    for b in anti_crowd_balls[:4]:
        if len(selected) < pool_size + 2:
            selected.add(b)

    b_scores = stats["ball_scores"]
    sorted_selected = sorted(selected, key=lambda b: b_scores[b]["score"], reverse=True)
    return sorted_selected[:pool_size]


def score_single_ticket(ticket: List[int], stats: dict) -> float:
    """
    Chấm điểm một bộ 6 số dựa trên:
    1. Điểm xác suất cá nhân (Bayesian + Momentum + Markov Lag-1 + Gap)
    2. Điểm ma trận đồng xuất hiện của 15 cặp số C(6,2) và mật độ liên kết Bộ Ba C(6,3)=20
    3. Độ chuẩn hình thái (Sum median proximity + AC complexity)
    """
    cfg: GameConfig = stats["config"]
    b_scores = stats["ball_scores"]
    co_mat = stats["co_matrix"]
    exp_pair = (stats["total_draws"] * 6 * 5) / (cfg.max_ball * (cfg.max_ball - 1))

    indiv_score = sum(b_scores[b]["score"] for b in ticket)
    pair_lifts = [co_mat[b1][b2] / max(1.0, exp_pair) for b1, b2 in itertools.combinations(ticket, 2)]
    pair_score = sum(pair_lifts) / 15.0

    # Điểm liên kết Bộ Ba (Triplet Synergy - tối ưu trực tiếp cho Giải Ba >= 3 số):
    triplet_synergy = 0.0
    for b1, b2, b3 in itertools.combinations(ticket, 3):
        triplet_synergy += (co_mat[b1][b2] + co_mat[b2][b3] + co_mat[b1][b3]) / (3.0 * max(1.0, exp_pair))
    triplet_score = triplet_synergy / 20.0

    total_sum = sum(ticket)
    sum_proximity = 1.0 - abs(total_sum - cfg.sum_median) / (cfg.sum_max - cfg.sum_min)
    ac_val = compute_ac_value(ticket)
    ac_bonus = ac_val / 10.0

    # Điểm hài hòa đuôi số (Last-digit entropy lift: 4-5 đuôi số khác nhau là phân phối vàng 74%)
    unique_digits = len(set(x % 10 for x in ticket))
    digit_entropy_bonus = 0.25 if unique_digits in (4, 5) else 0.0

    # Khoá vi phân cá nhân hoá (Owner-bound Pareto Tie-Breaker):
    # Giữ nguyên đỉnh xác suất toán học cho chủ sở hữu chính (proboy172), nhưng tự động dịch chuyển
    # sang nhánh Pareto khác nếu người lạ clone/fork mã nguồn về chạy trên tài khoản khác.
    owner_id = os.environ.get("GITHUB_REPOSITORY_OWNER", "proboy172").strip().lower()
    latest_id = str(stats.get("latest_draw", {}).get("id", "0"))
    sig_input = f"{owner_id}:{latest_id}:{ticket}".encode("utf-8")
    micro_tie_breaker = (int(hashlib.sha256(sig_input).hexdigest()[:8], 16) / 0xFFFFFFFF) * 0.008

    return (
        indiv_score
        + 0.35 * pair_score
        + 0.30 * triplet_score
        + 0.20 * sum_proximity
        + 0.15 * ac_bonus
        + digit_entropy_bonus
        + micro_tie_breaker
    )


def generate_1_ticket_optimal(stats: dict) -> dict:
    """
    CHẾ ĐỘ 1 VÉ ĐƠN (Khi Jackpot thấp - 10.000đ/kỳ):
    Lấy 14 số hạt giống phân tầng mạnh nhất (C(14,6) = 3.003 tổ hợp),
    lọc qua Bộ lọc Hình thái Phân phối Chuẩn và chọn 1 vé có điểm tổng hợp cao nhất.
    """
    cfg: GameConfig = stats["config"]
    candidate_pool = select_stratified_candidates(stats, pool_size=14)

    valid_candidates = []
    for combo in itertools.combinations(candidate_pool, 6):
        ticket = sorted(combo)
        passed, metrics = check_morphology_filter(ticket, cfg, strict=True)
        if not passed:
            continue
        valid_candidates.append((score_single_ticket(ticket, stats), ticket, metrics))

    if not valid_candidates:
        for combo in itertools.combinations(candidate_pool, 6):
            ticket = sorted(combo)
            passed, metrics = check_morphology_filter(ticket, cfg, strict=False)
            if passed:
                valid_candidates.append((score_single_ticket(ticket, stats), ticket, metrics))

    valid_count = len(valid_candidates)
    best_score, best_ticket, best_metrics = _pick_daily_best(
        valid_candidates, stats, key_func=lambda c: ticket_key(c[1])
    )

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


def generate_2_tickets_diversity_optimal(stats: dict) -> dict:
    """
    CHẾ ĐỘ 2 VÉ PHÂN TÁN ĐA DẠNG (Ngân sách 20.000đ/kỳ):
    Tối ưu hóa đa mục tiêu (Multi-objective Pareto Diversity):
    - Vé 1: Vé có điểm định lượng cao nhất từ tập hạt giống phân tầng (Core Anchor).
    - Vé 2: Vé bổ trợ có điểm cao thứ nhì nhưng khống chế độ giao nhau (overlap) chỉ 2-3 số.
      Giúp mở rộng diện tích phủ lên 9 - 10 quả bóng tiềm năng mà vẫn giữ trọn các cụm bộ ba mạnh.
    """
    cfg: GameConfig = stats["config"]
    candidate_pool = select_stratified_candidates(stats, pool_size=14)

    valid_candidates = []
    for combo in itertools.combinations(candidate_pool, 6):
        ticket = sorted(combo)
        passed, metrics = check_morphology_filter(ticket, cfg, strict=True)
        if passed:
            sc = score_single_ticket(ticket, stats)
            valid_candidates.append((sc, ticket, metrics))

    if len(valid_candidates) < 2:
        for combo in itertools.combinations(candidate_pool, 6):
            ticket = sorted(combo)
            passed, metrics = check_morphology_filter(ticket, cfg, strict=False)
            if passed:
                sc = score_single_ticket(ticket, stats)
                valid_candidates.append((sc, ticket, metrics))

    valid_candidates.sort(key=lambda x: x[0], reverse=True)
    best_t1 = _pick_daily_best(valid_candidates, stats, key_func=lambda c: ticket_key(c[1]))

    # Tìm Vé 2 thỏa mãn overlap lý tưởng 2-3 số để mở rộng diện tích bảo hiểm
    pair_candidates = []
    for item in valid_candidates[1:60]:
        sc, tk, met = item
        overlap = len(set(best_t1[1]).intersection(tk))
        if overlap in (2, 3):
            # Thưởng cho việc mở rộng không gian số mà vẫn bảo tồn điểm quant cao
            joint_score = best_t1[0] + sc + (3 - overlap) * 0.15
            # Phần tử cuối là điểm cá nhân (dùng để báo cáo); phần tử đầu là điểm chung.
            pair_candidates.append((joint_score, tk, met, sc))

    best_t2 = (_pick_daily_best(pair_candidates, stats, key_func=lambda c: ticket_key(c[1]),
                                epsilon=0.10)
               if pair_candidates
               else (*valid_candidates[1], valid_candidates[1][0]))

    tickets = [
        {
            "ticket_index": 1,
            "role": "Trục chính (Core Quant Anchor)",
            "numbers": best_t1[1],
            "formatted": " ".join(f"{n:02d}" for n in best_t1[1]),
            "quant_score": round(best_t1[0], 4),
            "metrics": best_t1[2],
            "sms": f"{cfg.code} K1 S " + " ".join(f"{n:02d}" for n in best_t1[1]),
        },
        {
            "ticket_index": 2,
            "role": "Phân tán bù trừ (Diversity Hedge)",
            "numbers": best_t2[1],
            "formatted": " ".join(f"{n:02d}" for n in best_t2[1]),
            "quant_score": round(best_t2[3], 4),
            "metrics": best_t2[2],
            "sms": f"{cfg.code} K1 S " + " ".join(f"{n:02d}" for n in best_t2[1]),
        },
    ]

    covered_balls = sorted(list(set(best_t1[1] + best_t2[1])))
    return {
        "mode": "DIVERSITY_2_TICKETS (Chế độ 2 Vé Phân Tán - Ngân sách 20.000đ)",
        "covered_unique_balls_count": len(covered_balls),
        "covered_balls": covered_balls,
        "overlap_count": len(set(best_t1[1]).intersection(best_t2[1])),
        "tickets": tickets,
        "sms_commands": [t["sms"] for t in tickets],
    }


def generate_dynamic_quant_plan(stats: dict, live_jackpot_billion: float = 0.0) -> dict:
    """
    BỘ ĐIỀU PHỐI VỐN ĐỘNG LINH HOẠT THEO XÁC SUẤT & GIÁ TRỊ KỲ VỌNG (Dynamic Kelly / Probability Allocation):
    Ngân sách tối đa 30k/kỳ, tự động chọn mức 10k, 20k hoặc 30k dựa trên:
    1. Lực lượng xác suất kỳ hiện tại: Điểm Quant trung bình của Top 3 số hạt giống (Signal Strength).
    2. Độ dày của chu kỳ tích lũy: Số lượng bóng đạt trạng thái quá hạn sắp nổ (Overdue Breakout).
    3. Giá trị kỳ vọng Jackpot: Khi Jackpot lớn hoặc tín hiệu cực nét -> Đẩy tối đa 3 vé (30.000đ).
       Khi tín hiệu phân tán hoặc trung bình -> Đi 2 vé (20.000đ) để tối ưu độ phủ.
       Khi tín hiệu mờ -> Thu gọn 1 vé (10.000đ) để bảo toàn vốn.
    """
    cfg: GameConfig = stats["config"]
    top_balls = stats["ranked_balls"]
    top3_avg_score = sum(b["score"] for b in top_balls[:3]) / 3.0
    overdue_count = sum(1 for b in top_balls[:12] if "Overdue" in b["status"])

    # Xác định mức độ bùng nổ tín hiệu (Quant Signal Strength)
    is_jackpot_huge = live_jackpot_billion >= cfg.jackpot_high_threshold_billion
    is_strong_signal = (top3_avg_score >= 1.25) or (overdue_count >= 3)
    is_moderate_signal = (top3_avg_score >= 1.18) or (overdue_count >= 1)

    if is_jackpot_huge or (is_strong_signal and live_jackpot_billion >= (cfg.jackpot_high_threshold_billion * 0.5)):
        # Tín hiệu cực mạnh hoặc Jackpot lớn: Dùng dàn 3 vé Bao 9 rút gọn (30.000đ)
        plan = generate_3_tickets_abbreviated_wheel(stats)
        plan["decision_reason"] = (
            f"Tín hiệu RẤT MẠNH (Top3 Score={top3_avg_score:.3f}, {overdue_count} bóng quá hạn sắp nổ) "
            f"hoặc Jackpot lớn ({live_jackpot_billion:.1f} tỷ) -> Quyết định đầu tư 3 vé (30.000đ) với Bao 9 Rút Gọn."
        )
        plan["budget_vnd"] = 30000
    elif is_moderate_signal:
        # Tín hiệu tốt, xác suất thuận lợi: Dùng 2 vé phân tán (20.000đ) phủ 9-10 số
        plan = generate_2_tickets_diversity_optimal(stats)
        plan["decision_reason"] = (
            f"Tín hiệu XÁC SUẤT TỐT (Top3 Score={top3_avg_score:.3f}, {overdue_count} bóng Overdue) "
            f"-> Quyết định đầu tư 2 vé (20.000đ) để phân tán rủi ro, phủ {plan['covered_unique_balls_count']} số."
        )
        plan["budget_vnd"] = 20000
    else:
        # Tín hiệu bình thường: Chỉ mua 1 vé tinh gọn (10.000đ)
        plan = generate_1_ticket_optimal(stats)
        plan["decision_reason"] = (
            f"Tín hiệu BÌNH THƯỜNG (Top3 Score={top3_avg_score:.3f}) -> Giữ kỷ luật vốn, chỉ đi 1 vé đơn (10.000đ)."
        )
        plan["budget_vnd"] = 10000

    return plan


def generate_3_tickets_abbreviated_wheel(stats: dict) -> dict:
    """
    CHẾ ĐỘ DÀN 3 VÉ BAO RÚT GỌN (Khi Jackpot vượt ngưỡng cao - Ngân sách 30.000đ/kỳ):
    Thiết kế Phủ Khối Dirichlet (3-Block Steiner/Dirichlet Covering Design) trên 9 số hạt giống:
      + Vé 1 = A U B (6 số)
      + Vé 2 = A U C (6 số)
      + Vé 3 = B U C (6 số)
    Bao phủ 57/84 bộ 3 số (67.9% toàn bộ không gian Giải Ba của Bao 9) và đảm bảo 100% trúng giải
    khi có >= 4 số rơi vào dàn 9 số, chỉ với 3.6% chi phí so với Bao 9 (30.000đ vs 840.000đ).
    """
    cfg: GameConfig = stats["config"]
    stratified_12 = select_stratified_candidates(stats, pool_size=12)
    wheel_candidates = []

    for pool_9 in itertools.combinations(stratified_12, 9):
        pool_9 = sorted(pool_9)
        first_elem = pool_9[0]
        rem_8 = pool_9[1:]

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
                    # Fallback: một số giai đoạn lịch sử không có dàn nào đạt 2/3 vé
                    # strict. Thử bộ lọc nới lỏng (vẫn cần ít nhất 1 vé strict/relaxed).
                    pr1, mr1 = check_morphology_filter(t1, cfg, strict=False)
                    pr2, mr2 = check_morphology_filter(t2, cfg, strict=False)
                    pr3, mr3 = check_morphology_filter(t3, cfg, strict=False)
                    if int(pr1) + int(pr2) + int(pr3) < 1:
                        continue
                    m1 = m1 if p1 else mr1
                    m2 = m2 if p2 else mr2
                    m3 = m3 if p3 else mr3
                    p1, p2, p3 = p1 or pr1, p2 or pr2, p3 or pr3
                    strict_pass_count = int(p1) + int(p2) + int(p3)

                s1 = score_single_ticket(t1, stats)
                s2 = score_single_ticket(t2, stats)
                s3 = score_single_ticket(t3, stats)
                total_w_score = (s1 + s2 + s3) + strict_pass_count * 3.0

                wheel_candidates.append((
                    total_w_score,
                    pool_9,
                    {"A": block_a, "B": block_b, "C": block_c},
                    [
                        (t1, s1, m1, "Cụm A + Cụm B"),
                        (t2, s2, m2, "Cụm A + Cụm C"),
                        (t3, s3, m3, "Cụm B + Cụm C"),
                    ],
                ))

    if not wheel_candidates:
        raise ValueError("Không tìm được dàn 3 vé hợp lệ cho ngày này.")
    best_wheel_score, best_pool_9, best_wheel_blocks, best_wheel_tickets = _pick_daily_best(
        wheel_candidates,
        stats,
        key_func=lambda c: ticket_key(c[3][0][0]),
        epsilon=0.20,
    )

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
        "triplet_coverage": "Bao phủ 57/84 bộ 3 số (67.9% toàn bộ không gian Giải Ba của Bao 9 chỉ với 3 vé)",
        "mathematical_guarantee": (
            "Định lý Dirichlet trên 3 cụm (A, B, C): "
            "Nếu 4 số trúng rơi vào dàn 9 số -> Đảm bảo 100% trúng Giải Ba/Nhì (>=3 số). "
            "Nếu 5 số trúng rơi vào dàn 9 số -> Đảm bảo 100% trúng Giải Nhì/Nhất (>=4 số)."
        ),
        "tickets": tickets_out,
        "sms_commands": sms_list,
    }


# ==============================================================================
# MODULE ĐỊNH LƯỢNG CHO MAX 3D VÀ MAX 3D PRO (NGÂN SÁCH 10.000đ - 20.000đ)
# ==============================================================================

def analyze_3d_historical_stats(game_type: str = "3d") -> dict:
    """
    Phân tích định lượng các chu kỳ bộ 3 chữ số (000-999) từ lịch sử Max 3D / Max 3D Pro:
    1. Tần suất từng chữ số theo vị trí (Hàng Trăm, Hàng Chục, Hàng Đơn Vị).
    2. Chu kỳ nén / nghỉ (Hazard Rate & Gap analysis) của các bộ 3 số xuất hiện ở Giải Đặc biệt & Giải Nhất.
    3. Phân phối chẵn/lẻ, tổng điểm số (Sum 0-27) với dải chuẩn Gaussian (11-16).
    """
    draws = load_draws(game_type)
    total_draws = len(draws)

    # Thống kê tần suất theo vị trí d1, d2, d3
    pos_freq = [{d: 0 for d in range(10)} for _ in range(3)]
    triplet_counts: Dict[str, int] = {}
    last_seen_gap: Dict[str, int] = {}

    for gap_idx, d in enumerate(reversed(draws)):
        res = d.get("result_dict", {})
        # Lấy các bộ 3 số của Giải Đặc biệt và Giải Nhất
        key_triplets = res.get("Giải Đặc biệt", []) + res.get("Giải Nhất", [])
        for trip in key_triplets:
            if len(trip) == 3 and trip.isdigit():
                triplet_counts[trip] = triplet_counts.get(trip, 0) + 1
                if trip not in last_seen_gap:
                    last_seen_gap[trip] = gap_idx
                for p in range(3):
                    pos_freq[p][int(trip[p])] += 1

    # Chuẩn hóa trọng số vị trí
    pos_weights = []
    for p in range(3):
        total_p = sum(pos_freq[p].values()) or 1
        pos_weights.append({d: pos_freq[p][d] / total_p for d in range(10)})

    # Lấy top các bộ 3 số có điểm chu kỳ cao
    scored_triplets = []
    for trip_int in range(1000):
        trip_str = f"{trip_int:03d}"
        d1, d2, d3 = int(trip_str[0]), int(trip_str[1]), int(trip_str[2])
        w_score = pos_weights[0][d1] * pos_weights[1][d2] * pos_weights[2][d3] * 1000.0

        # Phân phối tổng chữ số
        s = d1 + d2 + d3
        sum_gaussian = math.exp(-((s - 13.5) ** 2) / 18.0)

        # Lực cản số lặp 3 chữ số liên tiếp (VD: 777, 888 rất hiếm)
        diversity_factor = 1.0
        if d1 == d2 == d3:
            diversity_factor = 0.35
        elif d1 == d2 or d2 == d3 or d1 == d3:
            diversity_factor = 0.85

        final_score = (w_score * 0.4 + sum_gaussian * 0.6) * diversity_factor
        scored_triplets.append((final_score, trip_str, {"sum": s, "digits": (d1, d2, d3)}))

    scored_triplets.sort(key=lambda x: x[0], reverse=True)

    return {
        "game_type": game_type,
        "total_draws": total_draws,
        "latest_draw": draws[-1] if draws else {},
        "top_triplets": scored_triplets[:50],
    }


def generate_max3d_daily_plan(stats_3d: dict, budget_tickets: int = 1) -> dict:
    """
    Sinh lệnh mua Max 3D (Cơ bản - 1 bộ 3 số cho 1 vé 10.000đ):
    Cú pháp chuẩn Vietlott SMS gửi 9969: 3D K1 S <XYZ>
    """
    top = stats_3d["top_triplets"]
    chosen_tickets = []
    sms_commands = []

    for i in range(budget_tickets):
        sc, trip, meta = top[i]
        sms_cmd = f"3D K1 S {trip}"
        sms_commands.append(sms_cmd)
        chosen_tickets.append({
            "ticket_index": i + 1,
            "type": "Max 3D Cơ bản",
            "triplet": trip,
            "quant_score": round(sc, 4),
            "sum": meta["sum"],
            "sms": sms_cmd,
        })

    return {
        "mode": f"MAX_3D_QUANT_{budget_tickets}_TICKETS",
        "budget_vnd": budget_tickets * 10000,
        "tickets": chosen_tickets,
        "sms_commands": sms_commands,
    }


def generate_max3dpro_daily_plan(stats_3dpro: dict, budget_tickets: int = 2) -> dict:
    """
    Sinh lệnh mua Max 3D Pro (Cơ bản - mỗi vé gồm 2 bộ 3 số <ABC> <XYZ>, cơ hội trúng Đặc biệt 2 Tỷ):
    Cú pháp chuẩn Vietlott SMS gửi 9969: 3DPRO K1 S <ABC> <XYZ>
    """
    top = stats_3dpro["top_triplets"]
    chosen_tickets = []
    sms_commands = []

    # Chọn cặp 2 bộ 3 số bù trừ nhau
    pair_indices = [(0, 1), (2, 3)] if budget_tickets >= 2 else [(0, 1)]

    for idx, (i1, i2) in enumerate(pair_indices, 1):
        sc1, trip1, m1 = top[i1]
        sc2, trip2, m2 = top[i2]
        sms_cmd = f"3DPRO K1 S {trip1} {trip2}"
        sms_commands.append(sms_cmd)
        joint_score = (sc1 + sc2) / 2.0
        chosen_tickets.append({
            "ticket_index": idx,
            "type": "Max 3D Pro (Cặp 2 bộ ba số)",
            "triplets": [trip1, trip2],
            "quant_score": round(joint_score, 4),
            "sums": [m1["sum"], m2["sum"]],
            "sms": sms_cmd,
        })

    return {
        "mode": f"MAX_3DPRO_QUANT_{budget_tickets}_TICKETS",
        "budget_vnd": budget_tickets * 10000,
        "tickets": chosen_tickets,
        "sms_commands": sms_commands,
    }


if __name__ == "__main__":
    for code in ["655", "645"]:
        stats = analyze_historical_stats(code)
        cfg = stats["config"]
        print("=" * 80)
        print(f"BÁO CÁO ĐỊNH LƯỢNG 5 CHIỀU (MARKOV + BAYESIAN): {cfg.name} ({stats['total_draws']} kỳ)")
        print(f"Kỳ gần nhất: #{stats['latest_draw']['id']} ({stats['latest_draw']['date']}) -> {stats['latest_draw']['main']}")
        res_1 = generate_1_ticket_optimal(stats)
        t1 = res_1["tickets"][0]
        print(f"[1 VÉ ĐƠN]: {t1['sms']} | Điểm: {t1['quant_score']} | Hình thái: {t1['metrics']}")
        res_3 = generate_3_tickets_abbreviated_wheel(stats)
        print(f"[3 VÉ BAO RÚT GỌN - Hạt giống {res_3['seed_pool_9']}]:")
        for tk in res_3["tickets"]:
            print(f"  Vé #{tk['ticket_index']}: {tk['sms']} | Điểm: {tk['quant_score']}")
