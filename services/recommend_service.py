# -*- coding: utf-8 -*-
"""
推荐服务
整合内容推荐、协同过滤与混合推荐，向上层界面提供统一的推荐接口。
"""
import config
from recommender.collaborative import CollaborativeRecommender
from recommender.content_based import ContentBasedRecommender
from recommender.hybrid import HybridRecommender
from services.movie_service import MovieService
from services.history_service import HistoryService
from services.rating_service import RatingService
from utils.logger import get_logger

logger = get_logger("services.recommend")


class RecommendService:
    """推荐业务编排。"""

    def __init__(self):
        self.movie_service = MovieService()
        self.rating_service = RatingService()
        self.history_service = HistoryService()

        self.content = ContentBasedRecommender()
        self.collab = CollaborativeRecommender()
        self.hybrid = HybridRecommender()

    # ---------- 模型构建 ----------

    def _build_models(self):
        """从数据库读取电影与评分，拟合内容推荐与协同过滤模型。"""
        movies = self.movie_service.list_movies()
        ratings = self.rating_service.get_all_ratings()
        self.content.fit(movies)
        self.collab.fit(movies, ratings)
        return movies, ratings

    # ---------- 核心推荐接口 ----------

    def recommend_for_user(self, user_id, top_n=None):
        """为指定用户生成个性化推荐，返回 [(Movie, score)]。"""
        top_n = top_n or config.HYBRID_TOP_N
        movies, _ = self._build_models()
        if not movies:
            return []

        user_ratings = self.rating_service.get_user_ratings(user_id)
        rated_ids = {r.movie_id for r in user_ratings}
        liked_ids = [r.movie_id for r in user_ratings if r.score >= 4]

        # 内容推荐：基于用户高分电影的兴趣向量
        content_results = []
        if liked_ids:
            content_results = self.content.recommend_by_movies(
                liked_ids, top_n=config.CONTENT_TOP_N, exclude_ids=rated_ids
            )

        # 协同过滤：基于评分矩阵
        collab_results = self.collab.recommend(user_id, top_n=config.COLLAB_TOP_N)

        if content_results and collab_results:
            results = self.hybrid.combine(content_results, collab_results, top_n)
        elif collab_results:
            results = collab_results[:top_n]
        elif content_results:
            results = content_results[:top_n]
        else:
            results = self._cold_start(user_id, top_n)

        return results

    def _cold_start(self, user_id, top_n):
        """冷启动兜底：优先按最近浏览做内容推荐，否则返回热门电影。"""
        history = self.history_service.get_user_history(user_id, limit=5)
        for item in history:
            results = self.content.recommend_by_movie(item["movie_id"], top_n)
            if results:
                return results
        return self.popular_movies(top_n)

    def similar_movies(self, movie_id, top_n=None):
        """返回与指定电影相似的电影（内容推荐）。"""
        top_n = top_n or config.CONTENT_TOP_N
        self._build_models()
        return self.content.recommend_by_movie(movie_id, top_n)

    def recommend_by_keyword(self, keyword, top_n=None):
        """根据关键词/偏好描述推荐电影。"""
        top_n = top_n or config.CONTENT_TOP_N
        self._build_models()
        return self.content.recommend_by_text(keyword, top_n)

    def popular_movies(self, top_n=None):
        """返回热门电影（按平均分与评分人数）。"""
        top_n = top_n or config.HYBRID_TOP_N
        results = []
        for movie_id, avg, _cnt in self.rating_service.get_popular_movies(top_n):
            movie = self.movie_service.get_movie(movie_id)
            if movie:
                results.append((movie, float(avg)))
        # 若评分不足，用最新入库电影补足
        if len(results) < top_n:
            existing_ids = {b.id for b, _ in results}
            for movie in self.movie_service.list_movies()[::-1]:
                if len(results) >= top_n:
                    break
                if movie.id not in existing_ids:
                    results.append((movie, 0.0))
        return results
