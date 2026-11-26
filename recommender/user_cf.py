# -*- coding: utf-8 -*-
"""
基于用户的协同过滤算法（User-Based Collaborative Filtering）
"""
import numpy as np

from utils.logger import get_logger

logger = get_logger("recommender.usercf")


class UserCFRecommender:
    """基于用户的协同过滤推荐器。"""

    def __init__(self, k=20):
        self.k = k
        self.movies = []
        self.ratings = []
        self.user_list = []
        self.movie_list = []
        self.user_idx = {}
        self.movie_idx = {}
        self.matrix = np.zeros((0, 0))
        self._user_baseline = np.array([])
        self._user_sim = np.zeros((0, 0))

    def fit(self, movies, ratings):
        """载入电影与评分数据并构建用户相似度矩阵。"""
        self.movies = list(movies)
        self.ratings = list(ratings)
        users = sorted({r["user_id"] for r in self.ratings})
        movie_ids = [m.id for m in self.movies]
        self.user_list = users
        self.movie_list = movie_ids
        self.user_idx = {u: i for i, u in enumerate(users)}
        self.movie_idx = {bid: i for i, bid in enumerate(movie_ids)}

        self.matrix = np.zeros((len(users), len(movie_ids)))
        for r in self.ratings:
            ui = self.user_idx.get(r["user_id"])
            mi = self.movie_idx.get(r["movie_id"])
            if ui is not None and mi is not None:
                self.matrix[ui, mi] = r["score"]
        self._user_sim = self._compute_user_similarity()
        return self

    def _compute_user_similarity(self):
        """计算用户-用户余弦相似度（无方差用户回退中性基准 2.5）。"""
        m = self.matrix
        n_users = len(self.user_list)
        if m.size == 0 or n_users == 0:
            self._user_baseline = np.array([])
            return np.zeros((n_users, n_users))

        rated = m > 0
        counts = rated.sum(axis=1)
        row_mean = np.where(counts > 0, np.where(rated, m, 0).sum(axis=1) / np.maximum(counts, 1), 0.0)
        row_max = np.where(rated, m, -np.inf).max(axis=1)
        row_min = np.where(rated, m, np.inf).min(axis=1)
        has_var = (counts >= 2) & ((row_max - row_min) > 1e-9)
        self._user_baseline = np.where(has_var, row_mean, 2.5)

        centered = np.where(rated, m - self._user_baseline[:, None], 0.0)
        norms = np.linalg.norm(centered, axis=1)
        norms[norms == 0] = 1e-9
        normed = centered / norms[:, None]
        return normed @ normed.T

    def neighbors(self, user_id, k=None):
        """返回与目标用户最相似的前 k 个正相关用户 [(user_id, sim)]。"""
        k = k or self.k
        if user_id not in self.user_idx or self._user_sim.size == 0:
            return []
        ui = self.user_idx[user_id]
        sims = self._user_sim[ui]
        order = np.argsort(sims)[::-1]
        out = []
        for j in order:
            if j == ui or sims[j] <= 0:
                continue
            out.append((self.user_list[j], float(sims[j])))
            if len(out) >= k:
                break
        return out

    def predict_scores(self, user_id):
        """预测目标用户对未评分电影的兴趣分，返回 {movie_index: score}。"""
        if user_id not in self.user_idx:
            return {}
        ui = self.user_idx[user_id]
        user_vec = self.matrix[ui]
        neighbors = self.neighbors(user_id)
        if not neighbors:
            return {}

        target_base = float(self._user_baseline[ui])
        scores = {}
        for mi in range(len(self.movie_list)):
            if user_vec[mi] > 0:
                continue
            num = 0.0
            den = 0.0
            for nuid, sim in neighbors:
                nui = self.user_idx[nuid]
                r = self.matrix[nui, mi]
                if r > 0:
                    num += sim * (r - float(self._user_baseline[nui]))
                    den += sim
            if den > 0:
                pred = max(0.5, min(5.0, target_base + num / den))
                scores[mi] = float(pred)
        return scores

    def recommend(self, user_id, top_n=10):
        """为目标用户推荐未评分电影，返回 [(Movie, score)]。"""
        scores = self.predict_scores(user_id)
        if not scores:
            return []
        order = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        results = []
        for mi, s in order:
            if s <= 0:
                continue
            results.append((self.movies[mi], float(s)))
            if len(results) >= top_n:
                break
        return results