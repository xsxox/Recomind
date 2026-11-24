# -*- coding: utf-8 -*-
"""
混合推荐算法（Hybrid Recommendation）
将内容推荐与协同过滤的结果按权重融合，兼顾“内容相似”与“群体偏好”两个维度。
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
    """混合推荐器。"""

    def __init__(self, content_weight=None):
        self.content_weight = content_weight if content_weight is not None else config.HYBRID_CONTENT_WEIGHT

    def combine(self, content_results, collab_results, top_n=None):
        """融合两类推荐结果，返回 [(Movie, score)]。"""
        top_n = top_n or config.HYBRID_TOP_N
        collab_weight = 1.0 - self.content_weight

        content_norm = _normalize(content_results)
        collab_norm = _normalize(collab_results)

        scores = {}
        movie_map = {}
        for movie, s in content_norm:
            scores[movie.id] = scores.get(movie.id, 0.0) + self.content_weight * s
            movie_map[movie.id] = movie
        for movie, s in collab_norm:
            scores[movie.id] = scores.get(movie.id, 0.0) + collab_weight * s
            movie_map[movie.id] = movie

        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [(movie_map[bid], round(s, 4)) for bid, s in order[:top_n]]
