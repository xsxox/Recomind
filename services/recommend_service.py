# -*- coding: utf-8 -*-
"""
推荐服务 (Enhanced Recommend Service)
=======================================
整合五种推荐算法：
  1. 内容推荐 (TF-IDF + LDA + 语义嵌入 三路融合)
  2. 物品协同过滤 (Item-CF，均值中心化余弦相似度)
  3. 用户协同过滤 (User-CF，基于偏差的 Pearson 相似度)
  4. 矩阵分解 (SVD 隐因子模型)  ← 新增
  5. 混合推荐 (动态权重归一化融合 + MMR 多样性重排)

新增特性：
  - 情感分析质量加权 (Sentiment-Weighted Scoring)
  - 推荐解释生成 (Explainable Recommendation)
  - SVD 矩阵分解推荐
"""
import re

import config
from db.connection import execute_query
from recommender.collaborative import CollaborativeRecommender
from recommender.content_based import ContentBasedRecommender
from recommender.diversity import mmr_rerank
from recommender.hybrid import HybridRecommender
from recommender.matrix_factorization import SVDRecommender
from recommender.user_cf import UserCFRecommender
from services.history_service import HistoryService
from services.movie_service import MovieService
from services.rating_service import RatingService
from services.setting_service import SettingService
from utils.logger import get_logger

logger = get_logger("services.recommend")


def _split_genres(genre_str):
    return {g.strip() for g in re.split(r"[/,、，\s]+", genre_str or "") if g.strip()}


class RecommendService:
    """推荐业务编排。"""

    def __init__(self):
        self.movie_service = MovieService()
        self.rating_service = RatingService()
        self.history_service = HistoryService()
        self.setting_service = SettingService()

        self.content = ContentBasedRecommender(
            topic_weight=config.TOPIC_WEIGHT,
            n_topics=config.LDA_TOPICS,
            embed_weight=getattr(config, "EMBED_WEIGHT", 0.55),
            tfidf_weight=getattr(config, "TFIDF_WEIGHT", 0.30),
        )
        self.item_cf = CollaborativeRecommender()
        self.user_cf = UserCFRecommender()
        self.svd = SVDRecommender(n_factors=getattr(config, "SVD_FACTORS", 50))   # 新增：矩阵分解
        self.hybrid = HybridRecommender()

        self._movies_sig = None
        self._ratings_sig = None
        self._cached_movies = []
        self._tmdb_quality = {}
        self._svd_fitted = False

    def invalidate_cache(self):
        """主动清空模型缓存。"""
        self._movies_sig = None
        self._ratings_sig = None

    def _load_review_signals(self):
        try:
            rows = execute_query("SELECT movie_id, content, rating FROM reviews")
        except Exception:  # noqa: BLE001
            return {}, {}

        texts = {}
        ratings_sum = {}
        ratings_cnt = {}
        for r in rows:
            mid = r["movie_id"]
            c = (r.get("content") or "").strip()
            if c:
                cur = texts.get(mid, "")
                if len(cur) < 600:
                    texts[mid] = (cur + " " + c[:260]).strip()
            rv_score = r.get("rating") or 0
            if rv_score > 0:
                ratings_sum[mid] = ratings_sum.get(mid, 0.0) + float(rv_score)
                ratings_cnt[mid] = ratings_cnt.get(mid, 0) + 1

        review_avg = {mid: ratings_sum[mid] / ratings_cnt[mid] for mid in ratings_sum}
        return texts, review_avg

    def _compute_tmdb_quality(self, movies, review_avg):
        valid = [m.vote_average for m in movies if (m.vote_count or 0) > 0 and (m.vote_average or 0) > 0]
        c_mean = sum(valid) / len(valid) if valid else 6.8
        m_prior = 500.0

        quality = {}
        for m in movies:
            v = float(m.vote_count or 0)
            r = float(m.vote_average or 0)
            if v > 0 and r > 0:
                wr = (v / (v + m_prior)) * r + (m_prior / (v + m_prior)) * c_mean
            else:
                wr = c_mean
            if m.id in review_avg:
                wr = 0.8 * wr + 0.2 * review_avg[m.id]
            quality[m.id] = round(min(1.0, max(0.0, wr / 10.0)), 4)
        return quality

    def _build_models(self):
        movies = self.movie_service.list_movies()
        ratings = self.rating_service.get_all_ratings()
        review_texts, review_avg = self._load_review_signals()

        movies_sig = (
            tuple((m.id, m.title, m.director, m.genre, m.keywords, m.description, m.vote_average, m.vote_count) for m in movies),
            tuple(sorted((k, len(v)) for k, v in review_texts.items())),
        )
        ratings_sig = tuple((r["user_id"], r["movie_id"], r["score"]) for r in ratings)

        if movies_sig != self._movies_sig:
            self.content.fit(movies, extra_texts=review_texts)
            self._tmdb_quality = self._compute_tmdb_quality(movies, review_avg)
            self._movies_sig = movies_sig
            self._ratings_sig = None

        if ratings_sig != self._ratings_sig:
            self.item_cf.fit(movies, ratings)
            self.user_cf.fit(movies, ratings)
            # 新增：SVD 矩阵分解训练
            try:
                self.svd.fit(movies, ratings)
                self._svd_fitted = True
                logger.info("SVD 矩阵分解模型训练完成")
            except Exception as exc:
                logger.warning("SVD 训练失败: %s", exc)
                self._svd_fitted = False
            self._ratings_sig = ratings_sig

        self._cached_movies = movies
        return movies, ratings

    def _compute_branches(self, user_id, settings, pool_n=150):
        user_ratings = self.rating_service.get_user_ratings(user_id)
        rated_ids = {r.movie_id for r in user_ratings}

        liked = [(r.movie_id, r.score - 2.5) for r in user_ratings if r.score >= 4]
        if not liked:
            liked = [(r.movie_id, 0.5) for r in user_ratings if r.score == 3]

        content_results = (
            self.content.recommend_by_movies(
                [mid for mid, _ in liked],
                top_n=pool_n,
                exclude_ids=rated_ids,
                weights=[w for _, w in liked],
            )
            if (liked and settings.get("enable_content", True)) else []
        )
        item_cf_results = (
            self.item_cf.recommend(user_id, top_n=pool_n)
            if settings.get("enable_item_cf", True) else []
        )
        user_cf_results = (
            self.user_cf.recommend(user_id, top_n=pool_n)
            if settings.get("enable_user_cf", True) else []
        )
        # 新增：SVD 推荐（若已训练且用户在矩阵中）
        svd_results = []
        if self._svd_fitted and settings.get("enable_svd", True):
            try:
                svd_results = self.svd.recommend(user_id, top_n=pool_n)
            except Exception:
                pass
        return rated_ids, [mid for mid, _ in liked], content_results, item_cf_results, user_cf_results, svd_results

    def _apply_quality_and_preference(self, candidates, preferred):
        out = []
        for movie, score in candidates:
            q = self._tmdb_quality.get(movie.id, 0.65)
            blended = 0.88 * score + 0.12 * q
            if preferred:
                genres = _split_genres(movie.genre)
                if genres & preferred:
                    blended = min(1.0, blended * 0.85 + 0.18)
                else:
                    blended = blended * 0.85
            out.append((movie, round(min(1.0, blended), 4)))
        out.sort(key=lambda kv: kv[1], reverse=True)
        return out

    def _blend_with_svd(self, content_res, item_res, user_res, svd_res, pool_n):
        """
        将 SVD 结果作为第四路融入混合推荐。
        SVD 权重 = 0.25（从 item_cf 权重中分摊）。
        """
        if not svd_res:
            return self.hybrid.combine3(content_res, item_res, user_res, top_n=pool_n)
        from recommender.hybrid import _normalize
        all_sources = [
            (content_res, 0.20),
            (item_res, 0.30),
            (user_res, 0.25),
            (svd_res, 0.25),
        ]
        active = [(pairs, w) for pairs, w in all_sources if pairs]
        if not active:
            return []
        total_w = sum(w for _, w in active)
        scores: dict = {}
        movie_map: dict = {}
        for pairs, w in active:
            for movie, s in _normalize(pairs):
                scores[movie.id] = scores.get(movie.id, 0.0) + (w / total_w) * s
                movie_map[movie.id] = movie
        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [(movie_map[mid], round(s, 4)) for mid, s in order[:pool_n]]

    def recommend_for_user(self, user_id, top_n=None, settings=None):
        """为指定用户生成个性化推荐，返回 [(Movie, score)]。"""
        settings = settings or self.setting_service.get_settings(user_id)
        top_n = top_n or settings.get("recommend_top_n") or 80
        movies, _ = self._build_models()
        if not movies:
            return []

        pool_n = max(150, top_n * 2)
        rated_ids, _liked_ids, content_res, item_res, user_res, svd_res = self._compute_branches(
            user_id, settings, pool_n=pool_n
        )
        # 融合：将 SVD 结果纳入混合推荐（作为第四路，权重=item_cf 权重的一半）
        blended = self._blend_with_svd(content_res, item_res, user_res, svd_res, pool_n)
        if not blended:
            return self._cold_start(user_id, top_n, settings=settings, exclude_ids=rated_ids)

        preferred = _split_genres(settings.get("preferred_genres") or "")
        blended = self._apply_quality_and_preference(blended, preferred)

        return mmr_rerank(
            blended,
            similarity_fn=self.content.pairwise_similarity,
            lambda_param=config.MMR_LAMBDA,
            top_n=top_n,
        )

    def recommend_for_user_explained(self, user_id, top_n=None, settings=None):
        """生成个性化推荐并附带解释，返回 [(Movie, score, reason)]。"""
        settings = settings or self.setting_service.get_settings(user_id)
        top_n = top_n or settings.get("recommend_top_n") or 80
        movies, _ = self._build_models()
        if not movies:
            return []

        pool_n = max(150, top_n * 2)
        rated_ids, liked_ids, content_res, item_res, user_res, svd_res = self._compute_branches(
            user_id, settings, pool_n=pool_n
        )
        content_scores = {m.id: s for m, s in content_res}
        item_scores = {m.id: s for m, s in item_res}
        user_scores = {m.id: s for m, s in user_res}

        blended = self._blend_with_svd(content_res, item_res, user_res, svd_res, pool_n)
        if not blended:
            cold = self._cold_start(user_id, top_n, settings=settings, exclude_ids=rated_ids)
            return [(m, s, "结合你的偏好设置与 TMDB 高口碑精选") for m, s in cold]

        preferred = _split_genres(settings.get("preferred_genres") or "")
        blended = self._apply_quality_and_preference(blended, preferred)

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
        self._build_models()
        movie = self.movie_service.get_movie(movie_id)
        if movie is None:
            return ""
        settings = self.setting_service.get_settings(user_id)
        _rated_ids, liked_ids, content_res, item_res, user_res = self._compute_branches(user_id, settings)
        c = dict((m.id, s) for m, s in content_res).get(movie_id, 0.0)
        i = dict((m.id, s) for m, s in item_res).get(movie_id, 0.0)
        u = dict((m.id, s) for m, s in user_res).get(movie_id, 0.0)
        if c == 0.0 and i == 0.0 and u == 0.0:
            preferred = _split_genres(settings.get("preferred_genres") or "")
            if preferred and (_split_genres(movie.genre) & preferred):
                return f"符合你偏好的「{'/'.join(_split_genres(movie.genre) & preferred)}」题材 · TMDB 高口碑推荐"
            return "TMDB 高口碑精选推荐"
        return self._reason(user_id, movie, liked_ids, c, i, u)

    def _reason(self, user_id, movie, liked_ids, c, i, u):
        source = max((("content", c), ("item_cf", i), ("user_cf", u)), key=lambda x: x[1])[0]
        if source == "content":
            best = self.content.best_source_movie(movie.id, liked_ids)
            if best and best[0]:
                src = self.movie_service.get_movie(best[0])
                if src:
                    return f"与你喜欢的《{src.title}》内容及影评语义相似"
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

    def _cold_start(self, user_id, top_n, settings=None, exclude_ids=None):
        settings = settings or {}
        exclude_ids = set(exclude_ids or ())
        preferred = _split_genres(settings.get("preferred_genres") or "")

        if preferred and self._cached_movies:
            text_scores = {}
            if settings.get("enable_content", True):
                for m, s in self.content.recommend_by_text(" ".join(preferred), top_n=120, exclude_ids=exclude_ids):
                    text_scores[m.id] = s

            scored = []
            for m in self._cached_movies:
                if m.id in exclude_ids:
                    continue
                m_genres = _split_genres(m.genre)
                overlap = len(m_genres & preferred)
                if overlap == 0 and m.id not in text_scores:
                    continue
                genre_score = overlap / len(preferred)
                quality_score = self._tmdb_quality.get(m.id, 0.65)
                t_score = text_scores.get(m.id, 0.0)
                total = round(min(1.0, 0.50 * genre_score + 0.32 * quality_score + 0.18 * t_score), 4)
                scored.append((m, total))
            if scored:
                scored.sort(key=lambda kv: kv[1], reverse=True)
                return mmr_rerank(
                    scored[:max(150, top_n * 2)],
                    similarity_fn=self.content.pairwise_similarity,
                    lambda_param=config.MMR_LAMBDA,
                    top_n=top_n,
                )

        history = self.history_service.get_user_history(user_id, limit=10)
        hist_ids = list(dict.fromkeys(item["movie_id"] for item in history))[:5]
        if hist_ids and settings.get("enable_content", True):
            results = self.content.recommend_by_movies(hist_ids, top_n=top_n, exclude_ids=exclude_ids)
            if results:
                return [(m, round(min(1.0, 0.85 * s + 0.15 * self._tmdb_quality.get(m.id, 0.65)), 4)) for m, s in results]

        return self.popular_movies(top_n, exclude_ids=exclude_ids)

    def similar_movies(self, movie_id, top_n=None):
        top_n = top_n or config.CONTENT_TOP_N
        self._build_models()
        return self.content.recommend_by_movie(movie_id, top_n)

    def recommend_by_keyword(self, keyword, top_n=None):
        """根据关键词/偏好描述推荐电影，默认支持百部级召回用于分页。"""
        top_n = top_n or 100
        self._build_models()
        results = self.content.recommend_by_text(keyword, top_n=max(top_n * 2, 160))
        adjusted = [
            (m, round(s * (0.88 + 0.12 * self._tmdb_quality.get(m.id, 0.65)), 4))
            for m, s in results
        ]
        adjusted.sort(key=lambda kv: kv[1], reverse=True)
        return adjusted[:top_n]

    def popular_movies(self, top_n=None, exclude_ids=None):
        top_n = top_n or 80
        exclude_ids = set(exclude_ids or ())
        movies = self._cached_movies or self.movie_service.list_movies()
        if not self._tmdb_quality and movies:
            _, review_avg = self._load_review_signals()
            self._tmdb_quality = self._compute_tmdb_quality(movies, review_avg)

        site_scores = {
            mid: min(1.0, float(avg) / 5.0)
            for mid, avg, _cnt in self.rating_service.get_popular_movies(len(movies) or 100)
        }

        scored = []
        for m in movies:
            if m.id in exclude_ids:
                continue
            q = self._tmdb_quality.get(m.id, 0.65)
            if m.id in site_scores:
                score = round(0.55 * site_scores[m.id] + 0.45 * q, 4)
            else:
                score = q
            scored.append((m, score))
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return scored[:top_n]