# -*- coding: utf-8 -*-
"""
混合推荐算法（Hybrid Recommendation）
将内容推荐、物品协同过滤、用户协同过滤三类结果按权重融合，
兼顾“内容相似”“物品关联”与“群体偏好”三个维度。
"""
import config
from utils.logger import get_logger

logger = get_logger("recommender.hybrid")


def _normalize(pairs):
    """将 [(movie, score)] 的分数做最小-最大归一化到 [0, 1]。"""
    if not pairs:
        return []
    values = [s for _, s in pairs]
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [(b, 1.0) for b, _ in pairs]
    return [(b, (s - lo) / (hi - lo)) for b, s in pairs]


class HybridRecommender:
    """混合推荐器（内容 + 物品协同 + 用户协同）。"""

    def __init__(self, content_weight=None, item_cf_weight=None, user_cf_weight=None):
        self.content_weight = content_weight if content_weight is not None else config.HYBRID_CONTENT_WEIGHT
        self.item_cf_weight = item_cf_weight if item_cf_weight is not None else config.HYBRID_ITEM_CF_WEIGHT
        self.user_cf_weight = user_cf_weight if user_cf_weight is not None else config.HYBRID_USER_CF_WEIGHT

    def combine(self, content_results, collab_results, top_n=None):
        """兼容旧接口：collab_results 视为物品协同过滤结果。"""
        return self.combine3(content_results, collab_results, [], top_n)

    def combine3(self, content_results, item_cf_results, user_cf_results, top_n=None):
        """融合三类推荐结果，返回 [(Movie, score)]。"""
        top_n = top_n or config.HYBRID_TOP_N
        total = self.content_weight + self.item_cf_weight + self.user_cf_weight
        if total <= 0:
            total = 1.0

        scores = {}
        movie_map = {}
        for pairs, weight in [
            (content_results, self.content_weight),
            (item_cf_results, self.item_cf_weight),
            (user_cf_results, self.user_cf_weight),
        ]:
            if weight <= 0:
                continue
            for movie, s in _normalize(pairs):
                scores[movie.id] = scores.get(movie.id, 0.0) + (weight / total) * s
                movie_map[movie.id] = movie

        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [(movie_map[mid], round(s, 4)) for mid, s in order[:top_n]]
