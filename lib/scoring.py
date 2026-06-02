def calculate_metric_score(value: float | None, baseline: dict) -> float:
    median = baseline.get("baseline_median")
    q3 = baseline.get("baseline_q3")
    ceiling = baseline.get("baseline_ceiling")
    best = baseline.get("baseline_best")

    if value is None:
        return 0.0
    if median is None or q3 is None or ceiling is None:
        raise ValueError("baseline의 Median, Q3, Ceiling 값이 필요합니다.")
    median = float(median)
    q3 = float(q3)
    ceiling = float(ceiling)
    best = float(best) if best is not None else None

    if value <= median:
        return 75.0 * value / median if median > 0 else 0.0
    elif value <= q3:
        return 75.0 + 15.0 * (value - median) / (q3 - median)
    elif value <= ceiling:
        return 90.0 + 7.0 * (value - q3) / (ceiling - q3)
    elif best is not None and value <= best:
        return 97.0 + 3.0 * (value - ceiling) / (best - ceiling)
    else:
        return 100.0

def get_metric_values_by_class(class_name: str, key_action_cpm: float, back_attack_rate: float | None, head_attack_rate: float | None = None) -> dict:
    if class_name == "블레이드":
        return {
            "blade_burst_cpm": key_action_cpm,
            "blade_back_attack_rate": back_attack_rate,
        }
    if class_name == "브레이커":
        return {
            "breaker_nakhwa_cpm": key_action_cpm,
        }
    if class_name == "아르카나":
        return {
            "arcana_card_cpm": key_action_cpm,
        }
    raise ValueError("지원하지 않는 직업입니다.")

def calculate_final_score(
    class_name: str,
    rules: list,
    baselines: list,
    key_action_cpm: float,
    back_attack_rate: float | None = None,
    head_attack_rate: float | None = None
) -> float:
    baseline_map = {row["metric_name"]: row for row in baselines}
    metric_values = get_metric_values_by_class(
        class_name,
        key_action_cpm,
        back_attack_rate,
        head_attack_rate
    )
    final_score = 0.0
    total_weight = 0.0
    for rule in rules:
        metric_name = rule["metric_name"]
        weight = float(rule["weight"])
        value = metric_values.get(metric_name)
        baseline = baseline_map.get(metric_name)
        if baseline is None:
            raise ValueError(f"{metric_name} baseline이 없습니다.")
        metric_score = calculate_metric_score(value, baseline)
        final_score += metric_score * weight
        total_weight += weight
    if total_weight == 0:
        raise ValueError("가중치 합계가 0입니다.")
    return round(final_score / total_weight, 2)
