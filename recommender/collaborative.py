# -*- coding: utf-8 -*-
"""
基于物品的协同过滤算法（Item-Based Collaborative Filtering）
"""
import numpy as np

from utils.logger import get_logger

logger = get_logger("recommender.collab")


class CollaborativeRecommender:
    """基于物品的协同过滤推荐器。"""

    def __init__(self, k=10):
        self.k = k
        self.movies = []
        self.ratings = []
        self.user_list = []
        self.movie_list = []
        self.user_idx = {}
        self.movie_idx = {}
        self.matrix = np.zeros((0, 0))
        self._item_sim = np.zeros((0, 0))

    def fit(self, movies, ratings):
        """载入电影与评分数据并构建评分与物品相似度矩阵。"""
        self.movies = list(movies)
        self.ratings = list(ratings)
        self._build_matrix()
        return self

    def _build_matrix(self):
        users = sorted({r["user_id"] for r in self.ratings})
        movie_ids = [b.id for b in self.movies]
        self.user_list = users
        self.movie_list = movie_ids
        self.user_idx = {u: i for i, u in enumerate(users)}
        self.movie_idx = {bid: i for i, bid in enumerate(movie_ids)}

        self.matrix = np.zeros((len(users), len(movie_ids)))
        for r in self.ratings:
            ui = self.user_idx.get(r["user_id"])
            bi = self.movie_idx.get(r["movie_id"])
            if ui is not None and bi is not None:
                self.matrix[ui, bi] = r["score"]

        self._item_sim = self._item_similarity()

    def _item_similarity(self):
        """计算调整余弦相似度（单评分或无方差用户回退中性基准 2.5，防止向量归零）。"""
        m = self.matrix
        n_movies = len(self.movie_list)
        if m.size == 0 or n_movies == 0:
            return np.zeros((n_movies, n_movies))

        rated = m > 0
        counts = rated.sum(axis=1)
        row_mean = np.where(counts > 0, np.where(rated, m, 0).sum(axis=1) / np.maximum(counts, 1), 0.0)
        row_max = np.where(rated, m, -np.inf).max(axis=1)
        row_min = np.where(rated, m, np.inf).min(axis=1)
        has_var = (counts >= 2) & ((row_max - row_min) > 1e-9)
        baseline = np.where(has_var, row_mean, 2.5)

        centered = np.where(rated, m - baseline[:, None], 0.0)
        norms = np.linalg.norm(centered, axis=0)
        norms[norms == 0] = 1e-9
        normed = centered / norms
        return normed.T @ normed

    def predict_scores(self, user_id):
        """预测目标用户对所有未评分电影的兴趣分，返回 {movie_index: score}。"""
        if user_id not in self.user_idx:
            return {}
        sim = self._item_sim
        ui = self.user_idx[user_id]
        user_vec = self.matrix[ui]
        rated_idx = np.where(user_vec > 0)[0]
        if rated_idx.size == 0:
            return {}

        scores = {}
        for bi in range(len(self.movie_list)):
            if user_vec[bi] > 0:
                continue
            s = sim[bi, rated_idx]
            pos = s > 0
            if not np.any(pos):
                continue
            pos_sims = s[pos]
            pos_ratings = user_vec[rated_idx[pos]]
            if pos_sims.size > self.k:
                top = np.argsort(pos_sims)[::-1][:self.k]
                pos_sims = pos_sims[top]
                pos_ratings = pos_ratings[top]
            denom = pos_sims.sum()
            if denom > 0:
                scores[bi] = float((pos_sims * pos_ratings).sum() / denom)
        return scores

    def best_source_movie(self, user_id, movie_id):
        """返回用户评分过的、与指定电影物品相似度最高的 (movie_id, sim)。"""
        if user_id not in self.user_idx or movie_id not in self.movie_idx:
            return None
        ui = self.user_idx[user_id]
        mi = self.movie_idx[movie_id]
        user_vec = self.matrix[ui]
        rated = np.where(user_vec > 0)[0]
        if rated.size == 0:
            return None
        sim = self._item_sim[mi, rated]
        top = int(np.argmax(sim))
        if sim[top] <= 0:
            return None
        return (self.movie_list[rated[top]], float(sim[top]))

    def recommend(self, user_id, top_n=10):
        """为目标用户推荐未评分电影，返回 [(Movie, score)]。"""
        scores = self.predict_scores(user_id)
        if not scores:
            return []
        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        results = []
        for bi, s in order:
            if s <= 0:
                continue
            results.append((self.movies[bi], float(s)))
            if len(results) >= top_n:
                break
        return results