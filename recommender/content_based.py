# -*- coding: utf-8 -*-
"""
基于内容的推荐算法（Content-Based Filtering）
融合 TF-IDF 与 LDA 主题两种内容特征，用余弦相似度衡量电影文本的相似程度，
推荐与目标电影或目标文本语义最相近的电影。
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from nlp.feature import TextFeatureExtractor
from nlp.topic import TopicExtractor
from utils.logger import get_logger

logger = get_logger("recommender.content")


class ContentBasedRecommender:
    """基于内容的推荐器（TF-IDF + LDA 主题）。"""

    def __init__(self, topic_weight=0.2):
        self.topic_weight = topic_weight
        self.extractor = TextFeatureExtractor()
        self.topic = TopicExtractor()
        self.movies = []          # list[Movie]
        self.id_to_index = {}     # movie_id -> 下标
        self.matrix = None        # TF-IDF 稀疏矩阵
        self.topic_matrix = None  # LDA 主题分布矩阵
        self.sim_matrix = None    # 融合后的内容相似度矩阵 (n, n)

    def fit(self, movies):
        """根据电影列表构建内容特征与相似度矩阵。"""
        self.movies = list(movies)
        self.id_to_index = {m.id: i for i, m in enumerate(self.movies)}
        texts = [m.text() for m in self.movies]
        self.matrix = self.extractor.fit_transform(texts)
        self.topic_matrix = self.topic.fit_transform(texts)
        self._build_sim_matrix()
        return self

    def _build_sim_matrix(self):
        if self.matrix is None:
            self.sim_matrix = None
            return
        tfidf_sim = cosine_similarity(self.matrix)
        if self.topic_matrix is not None and self.topic_weight > 0:
            topic_sim = cosine_similarity(self.topic_matrix)
            self.sim_matrix = (1.0 - self.topic_weight) * tfidf_sim + self.topic_weight * topic_sim
        else:
            self.sim_matrix = tfidf_sim

    # ---------- 对外接口 ----------

    def recommend_by_movie(self, movie_id, top_n=10, exclude_ids=None):
        """返回与指定电影内容最相似的电影列表 [(Movie, score)]。"""
        if self.sim_matrix is None or movie_id not in self.id_to_index:
            return []
        exclude = set(exclude_ids or []) | {movie_id}
        idx = self.id_to_index[movie_id]
        sims = self.sim_matrix[idx]
        return self._top_results(sims, top_n, exclude)

    def recommend_by_movies(self, movie_ids, top_n=10, exclude_ids=None):
        """根据多部电影（如用户偏好的影片）的相似度均值进行推荐。"""
        if self.sim_matrix is None:
            return []
        indices = [self.id_to_index[mid] for mid in movie_ids if mid in self.id_to_index]
        if not indices:
            return []
        exclude = set(exclude_ids or []) | set(movie_ids)
        sims = np.mean(self.sim_matrix[indices], axis=0)
        return self._top_results(sims, top_n, exclude)

    def recommend_by_text(self, text, top_n=10, exclude_ids=None):
        """根据一段文本（如搜索关键词/偏好描述）推荐相似电影。"""
        if self.matrix is None or not text:
            return []
        exclude = set(exclude_ids or [])
        tfidf_vec = self.extractor.transform([text])
        tfidf_sims = self.extractor.similarity(tfidf_vec)
        if self.topic_matrix is not None and self.topic_weight > 0:
            topic_vec = self.topic.transform([text])
            topic_sims = self.topic.similarity(topic_vec)
            sims = (1.0 - self.topic_weight) * tfidf_sims + self.topic_weight * topic_sims
        else:
            sims = tfidf_sims
        return self._top_results(sims, top_n, exclude)

    def pairwise_similarity(self, movie_a_id, movie_b_id):
        """返回两部电影的内容相似度（用于 MMR 多样性重排）。"""
        if self.sim_matrix is None:
            return 0.0
        ia = self.id_to_index.get(movie_a_id)
        ib = self.id_to_index.get(movie_b_id)
        if ia is None or ib is None:
            return 0.0
        return float(self.sim_matrix[ia, ib])

    def best_source_movie(self, movie_id, liked_ids):
        """返回 liked_ids 中与 movie_id 内容最相似的 (movie_id, sim)。"""
        best = None
        for lid in liked_ids:
            sim = self.pairwise_similarity(movie_id, lid)
            if best is None or sim > best[1]:
                best = (lid, sim)
        return best

    # ---------- 内部工具 ----------

    def _top_results(self, sims, top_n, exclude_ids):
        """按相似度降序，过滤排除项，返回前 top_n 条。"""
        if len(sims) == 0:
            return []
        order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
        results = []
        for i in order:
            movie = self.movies[i]
            if movie.id in exclude_ids:
                continue
            if sims[i] <= 0:
                continue
            results.append((movie, float(sims[i])))
            if len(results) >= top_n:
                break
        return results
