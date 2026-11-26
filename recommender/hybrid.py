# -*- coding: utf-8 -*-
"""
混合推荐算法（Hybrid Recommendation）
"""
import config
from utils.logger import get_logger

logger = get_logger("recommender.hybrid")


def _normalize(pairs):
    """将 [(movie, score)] 归一化到 [0, 1]。"""
    if not pairs:
        return []
    values = [s for _, s in pairs]
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        # 仅 1 条或分数完全一致时，按量纲合理缩放（CF 1~5 分按 /5，相似度保持原值）
        val = values[0]
        scaled = min(1.0, max(0.0, val / 5.0 if val > 1.0 else val))
        return [(b, scaled) for b, _ in pairs]
    return [(b, (s - lo) / (hi - lo)) for b, s in pairs]


class HybridRecommender:
    """混合推荐器（内容 + 物品协同 + 用户协同）。"""

    def __init__(self, content_weight=None, item_cf_weight=None, user_cf_weight=None):
        self.content_weight = content_weight if content_weight is not None else config.HYBRID_CONTENT_WEIGHT
        self.item_cf_weight = item_cf_weight if item_cf_weight is not None else config.HYBRID_ITEM_CF_WEIGHT
        self.user_cf_weight = user_cf_weight if user_cf_weight is not None else config.HYBRID_USER_CF_WEIGHT

    def combine(self, content_results, collab_results, top_n=None):
        return self.combine3(content_results, collab_results, [], top_n)

    def combine3(self, content_results, item_cf_results, user_cf_results, top_n=None):
        """按有效分支权重动态归一化融合三类推荐结果，返回 [(Movie, score)]。"""
        top_n = top_n or config.HYBRID_TOP_N
        active = [
            (pairs, weight)
            for pairs, weight in [
                (content_results, self.content_weight),
                (item_cf_results, self.item_cf_weight),
                (user_cf_results, self.user_cf_weight),
            ]
            if pairs and weight > 0
        ]
        if not active:
            return []

        total = sum(w for _, w in active)
        scores = {}
        movie_map = {}
        for pairs, weight in active:
            for movie, s in _normalize(pairs):
                scores[movie.id] = scores.get(movie.id, 0.0) + (weight / total) * s
                movie_map[movie.id] = movie

        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [(movie_map[mid], round(s, 4)) for mid, s in order[:top_n]]