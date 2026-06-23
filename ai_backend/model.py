import math
from data import universities


def calc_prob(gap: int) -> float:
    """Sigmoid 概率函数：gap 越大录取概率越高"""
    return 1 / (1 + math.exp(-gap / 15))


def recommend(user_score: int, province: str = "湖北省") -> list[dict]:
    result = []
    for u in universities:
        gap = user_score - u["min"]
        prob = calc_prob(gap)
        result.append({
            "name": u["name"],
            "min": u["min"],
            "prob": round(prob, 3),
            "year": u.get("year", 2025),
        })

    result.sort(key=lambda x: -x["prob"])
    return result
