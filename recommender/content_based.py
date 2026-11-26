# -*- coding: utf-8 -*-
"""
升级版内容推荐器 (Enhanced Content-Based Recommender)
=======================================================
在原 TF-IDF + LDA 基础上集成语义嵌入（Sentence-BERT / LSA）：

特征融合方案：
  sim_final = α·sim_tfidf + β·sim_lda + γ·sim_embed

默认权重（config 可覆盖）：
  α=0.30 (TF-IDF), β=0.15 (LDA), γ=0.55 (语义嵌入)

毕设亮点：
  三路特征各有所长：TF-IDF 精确匹配关键词，LDA 捕捉主题分布，
  语义嵌入处理同义词和语义近似（如"太空探索" ≈ "宇宙冒险"）。
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import config
from nlp.embedding import SemanticEmbedder
from nlp.feature import TextFeatureExtractor
from nlp.topic import TopicExtractor
from utils.logger import get_logger

logger = get_logger("recommender.content")


class ContentBasedRecommender:
    """
    三路融合内容推荐器：TF-IDF + LDA 主题 + 语义嵌入。
    """

    def __init__(self, topic_weight: float = 0.15, n_topics: int | None = None,
                 embed_weight: float = 0.55, tfidf_weight: float = 0.30):
        self.tfidf_weight = tfidf_weight
        self.topic_weight = topic_weight
        self.embed_weight = embed_weight

        self.extractor = TextFeatureExtractor()
        self.topic = TopicExtractor(n_topics=n_topics or config.LDA_TOPICS)
        self.embedder = SemanticEmbedder()   # 语义嵌入（新增）

        self.movies: list = []
        self.id_to_index: dict[int, int] = {}
        self.matrix = None          # TF-IDF 稀疏矩阵
        self.topic_matrix = None    # LDA 主题分布矩阵
        self.embed_matrix = None    # 语义嵌入矩阵 (n_docs, dim)
        self.sim_matrix: np.ndarray | None = None   # 融合相似度矩阵

    # ------------------------------------------------------------------
    # 拟合
    # ------------------------------------------------------------------

    def fit(self, movies, extra_texts: dict | None = None) -> "ContentBasedRecommender":
        """
        构建内容特征。
        extra_texts: {movie_id: extra_text_string}，用于将 TMDB 影评文本注入语料。
        """
        self.movies = list(movies)
        self.id_to_index = {m.id: i for i, m in enumerate(self.movies)}
        extra_texts = extra_texts or {}
        texts = [
            f"{m.text()} {extra_texts[m.id]}" if m.id in extra_texts else m.text()
            for m in self.movies
        ]

        # TF-IDF
        self.matrix = self.extractor.fit_transform(texts)
        # LDA 主题
        self.topic_matrix = self.topic.fit_transform(texts)
        # 语义嵌入（三路新增）
        try:
            self.embed_matrix = self.embedder.fit_transform(texts)
            logger.info("语义嵌入矩阵构建完成 shape=%s", self.embed_matrix.shape)
        except Exception as exc:
            logger.warning("语义嵌入失败，仅用 TF-IDF+LDA: %s", exc)
            self.embed_matrix = None

        self._build_sim_matrix()
        return self

    def _build_sim_matrix(self):
        """融合三路相似度矩阵。"""
        if self.matrix is None:
            self.sim_matrix = None
            return

        tfidf_sim = cosine_similarity(self.matrix).astype(np.float32)
        total_w = self.tfidf_weight
        sim = self.tfidf_weight * tfidf_sim

        if self.topic_matrix is not None and self.topic_weight > 0:
            topic_sim = cosine_similarity(self.topic_matrix).astype(np.float32)
            sim += self.topic_weight * topic_sim
            total_w += self.topic_weight

        if self.embed_matrix is not None and self.embed_weight > 0:
            embed_sim = cosine_similarity(self.embed_matrix).astype(np.float32)
            sim += self.embed_weight * embed_sim
            total_w += self.embed_weight

        self.sim_matrix = sim / max(total_w, 1e-9)
        logger.info("内容相似度矩阵构建完成，shape=%s", self.sim_matrix.shape)

    # ------------------------------------------------------------------
    # 推荐接口（与原版兼容）
    # ------------------------------------------------------------------

    def recommend_by_movie(self, movie_id: int, top_n: int = 10,
                           exclude_ids: list | None = None) -> list[tuple]:
        if self.sim_matrix is None or movie_id not in self.id_to_index:
            return []
        exclude = set(exclude_ids or []) | {movie_id}
        idx = self.id_to_index[movie_id]
        return self._top_results(self.sim_matrix[idx], top_n, exclude)

    def recommend_by_movies(self, movie_ids: list[int], top_n: int = 10,
                             exclude_ids: list | None = None,
                             weights: list | None = None) -> list[tuple]:
        if self.sim_matrix is None:
            return []
        pairs = [
            (self.id_to_index[mid], float(weights[i]) if weights else 1.0)
            for i, mid in enumerate(movie_ids) if mid in self.id_to_index
        ]
        if not pairs:
            return []
        indices = [i for i, _ in pairs]
        w_arr = np.array([w for _, w in pairs], dtype=float)
        w_arr /= w_arr.sum()
        exclude = set(exclude_ids or []) | set(movie_ids)
        sims = np.average(self.sim_matrix[indices], axis=0, weights=w_arr)
        return self._top_results(sims, top_n, exclude)

    def recommend_by_text(self, text: str, top_n: int = 10,
                          exclude_ids: list | None = None) -> list[tuple]:
        """支持自然语言查询推荐（语义搜索）。"""
        if not (text or "").strip():
            return []
        exclude = set(exclude_ids or [])

        tfidf_sims = np.zeros(len(self.movies), dtype=float)
        if self.matrix is not None:
            tfidf_vec = self.extractor.transform([text])
            ts = np.asarray(self.extractor.similarity(tfidf_vec), dtype=float)
            if ts.size == len(self.movies):
                tfidf_sims = ts

        topic_sims = np.zeros(len(self.movies), dtype=float)
        if self.topic_matrix is not None and self.topic_weight > 0:
            topic_vec = self.topic.transform([text])
            ts2 = np.asarray(self.topic.similarity(topic_vec), dtype=float)
            if ts2.size == len(self.movies):
                topic_sims = ts2

        embed_sims = np.zeros(len(self.movies), dtype=float)
        if self.embed_matrix is not None and self.embed_weight > 0:
            try:
                q_vec = self.embedder.transform([text])
                es = self.embedder.similarity(q_vec[0])
                if es.size == len(self.movies):
                    embed_sims = es
            except Exception:
                pass

        total_w = self.tfidf_weight + self.topic_weight + self.embed_weight
        sims = (self.tfidf_weight * tfidf_sims
                + self.topic_weight * topic_sims
                + self.embed_weight * embed_sims) / max(total_w, 1e-9)
        return self._top_results(sims, top_n, exclude)

    def pairwise_similarity(self, movie_a_id: int, movie_b_id: int) -> float:
        if self.sim_matrix is None:
            return 0.0
        ia = self.id_to_index.get(movie_a_id)
        ib = self.id_to_index.get(movie_b_id)
        if ia is None or ib is None:
            return 0.0
        return float(self.sim_matrix[ia, ib])

    def best_source_movie(self, movie_id: int, liked_ids: list[int]):
        best = None
        for lid in liked_ids:
            sim = self.pairwise_similarity(movie_id, lid)
            if best is None or sim > best[1]:
                best = (lid, sim)
        return best

    def _top_results(self, sims, top_n: int, exclude_ids: set) -> list[tuple]:
        if len(sims) == 0:
            return []
        order = np.argsort(sims)[::-1]
        results = []
        for i in order:
            movie = self.movies[i]
            if movie.id in exclude_ids or sims[i] <= 0:
                continue
            results.append((movie, float(round(sims[i], 4))))
            if len(results) >= top_n:
                break
        return results
