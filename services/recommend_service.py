# -*- coding: utf-8 -*-
"""
推荐服务
整合内容推荐（TF-IDF + LDA）、物品协同过滤、用户协同过滤与混合推荐，
支持 MMR 多样性重排与推荐解释，向上层界面提供统一推荐接口。
"""
import config
from recommender.collaborative import CollaborativeRecommender
from recommender.content_based import ContentBasedRecommender
from recommender.diversity import mmr_rerank
from recommender.hybrid import HybridRecommender
from recommender.user_cf import UserCFRecommender
from services.history_service import HistoryService
from services.movie_service import MovieService
from services.rating_service import RatingService
from services.setting_service import SettingService
from utils.logger import get_logger

logger = get_logger("services.recommend")


class RecommendService:
    """推荐业务编排。"""

    def __init__(self):
        self.movie_service = MovieService()
        self.rating_service = RatingService()
        self.history_service = HistoryService()
        self.setting_service = SettingService()

        self.content = ContentBasedRecommender(topic_weight=config.TOPIC_WEIGHT)
        self.item_cf = CollaborativeRecommender()
        self.user_cf = UserCFRecommender()
        self.hybrid = HybridRecommender()

    # ---------- 模型构建 ----------

    def _build_models(self):
        """从数据库读取电影与评分，拟合三类推荐模型。"""
        movies = self.movie_service.list_movies()
        ratings = self.rating_service.get_all_ratings()
        self.content.fit(movies)
        self.item_cf.fit(movies, ratings)
        self.user_cf.fit(movies, ratings)
        return movies, ratings

    # ---------- 核心推荐接口 ----------

    def recommend_for_user(self, user_id, top_n=None, settings=None):
        """为指定用户生成个性化推荐，返回 [(Movie, score)]。

        读取用户设置（推荐条数、算法开关、偏好类型）并作用于结果。
        """
        settings = settings or self.setting_service.get_settings(user_id)
        top_n = top_n or settings.get("recommend_top_n") or config.HYBRID_TOP_N
        movies, _ = self._build_models()
        if not movies:
            return []

        user_ratings = self.rating_service.get_user_ratings(user_id)
        rated_ids = {r.movie_id for r in user_ratings}
        liked_ids = [r.movie_id for r in user_ratings if r.score >= 4]

        content_results = (
            self.content.recommend_by_movies(liked_ids, top_n=50, exclude_ids=rated_ids)
            if (liked_ids and settings.get("enable_content", True)) else []
        )
        item_cf_results = (
            self.item_cf.recommend(user_id, top_n=50)
            if settings.get("enable_item_cf", True) else []
        )
        user_cf_results = (
            self.user_cf.recommend(user_id, top_n=50)
            if settings.get("enable_user_cf", True) else []
        )

        blended = self.hybrid.combine3(content_results, item_cf_results, user_cf_results, top_n=50)
        if not blended:
            return self._cold_start(user_id, top_n)

        # 偏好类型加权：命中的电影略微加分
        preferred = {g.strip() for g in (settings.get("preferred_genres") or "").split(",") if g.strip()}
        if preferred:
            boosted = []
            for movie, score in blended:
                genres = set((movie.genre or "").split("/"))
                boosted.append((movie, score + 0.12 if genres & preferred else score))
            boosted.sort(key=lambda kv: kv[1], reverse=True)
            blended = boosted

        # MMR 多样性重排
        return mmr_rerank(
            blended,
            similarity_fn=self.content.pairwise_similarity,
            lambda_param=config.MMR_LAMBDA,
            top_n=top_n,
        )

    def recommend_for_user_explained(self, user_id, top_n=None):
        """生成个性化推荐并附带解释，返回 [(Movie, score, reason)]。"""
        top_n = top_n or config.HYBRID_TOP_N
        movies, _ = self._build_models()
        if not movies:
            return []

        user_ratings = self.rating_service.get_user_ratings(user_id)
        rated_ids = {r.movie_id for r in user_ratings}
        liked_ids = [r.movie_id for r in user_ratings if r.score >= 4]

        content_results = (
            self.content.recommend_by_movies(liked_ids, top_n=50, exclude_ids=rated_ids)
            if liked_ids else []
        )
        item_cf_results = self.item_cf.recommend(user_id, top_n=50)
        user_cf_results = self.user_cf.recommend(user_id, top_n=50)

        content_scores = {m.id: s for m, s in content_results}
        item_scores = {m.id: s for m, s in item_cf_results}
        user_scores = {m.id: s for m, s in user_cf_results}

        blended = self.hybrid.combine3(content_results, item_cf_results, user_cf_results, top_n=50)
        reranked = mmr_rerank(
            blended, self.content.pairwise_similarity, config.MMR_LAMBDA, top_n
        )

        results = []
        for movie, score in reranked:
            reason = self._reason(
                user_id, movie, liked_ids,
                content_scores.get(movie.id, 0.0),
                item_scores.get(movie.id, 0.0),
                user_scores.get(movie.id, 0.0),
            )
            results.append((movie, score, reason))
        return results

    def explain_recommendation(self, user_id, movie_id):
        """解释某部电影为何被推荐给该用户。"""
        self._build_models()
        user_ratings = self.rating_service.get_user_ratings(user_id)
        liked_ids = [r.movie_id for r in user_ratings if r.score >= 4]
        movie = self.movie_service.get_movie(movie_id)
        if movie is None:
            return ""
        return self._reason(user_id, movie, liked_ids, 1.0, 0.0, 0.0)

    def _reason(self, user_id, movie, liked_ids, c, i, u):
        """根据三类来源的贡献选择主导来源并生成解释文本。"""
        source = max((("content", c), ("item_cf", i), ("user_cf", u)), key=lambda x: x[1])[0]
        if source == "content":
            best = self.content.best_source_movie(movie.id, liked_ids)
            if best and best[0]:
                src = self.movie_service.get_movie(best[0])
                if src:
                    return f"与你喜欢的《{src.title}》内容相似"
            return "与你喜欢的电影内容相似"
        if source == "item_cf":
            best = self.item_cf.best_source_movie(user_id, movie.id)
            if best and best[0]:
                src = self.movie_service.get_movie(best[0])
                if src:
                    return f"与你打过高分的《{src.title}》风格相近"
            return "与你评分较高的电影相似"
        neighbor_count = len(self.user_cf.neighbors(user_id))
        return f"与你口味相近的 {neighbor_count} 位用户也喜欢"

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
