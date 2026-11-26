# -*- coding: utf-8 -*-
"""
推荐系统评估仪表盘数据模块 (Evaluation Dashboard)
===================================================
运行离线评估并返回结构化结果，供 UI 仪表盘展示。
新增指标：MRR、Intra-List Diversity、Coverage@K。

用法（命令行）：
  python -m scripts.evaluate --k 10 --ratio 0.2 --seed 42

用法（代码）：
  from evaluation.dashboard import run_full_evaluation
  results = run_full_evaluation(k=10, ratio=0.2)
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_VENDOR = os.path.join(ROOT, "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from evaluation.metrics import (  # noqa: E402
    coverage, diversity, evaluate_ranked, ndcg_at_k, precision_at_k, recall_at_k
)
from utils.logger import get_logger  # noqa: E402

logger = get_logger("evaluation.dashboard")


@dataclass
class AlgorithmResult:
    """单个算法的评估结果。"""
    name: str
    hit_rate: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    ndcg: float = 0.0
    mrr: float = 0.0
    coverage: float = 0.0
    diversity: float = 0.0
    runtime_ms: float = 0.0
    n_users: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """完整评估报告。"""
    k: int = 10
    ratio: float = 0.2
    seed: int = 42
    n_movies: int = 0
    n_users: int = 0
    n_ratings: int = 0
    algorithms: list[AlgorithmResult] = field(default_factory=list)
    baseline_popularity: AlgorithmResult | None = None
    baseline_random: AlgorithmResult | None = None
    timestamp: str = ""

    def best_algorithm(self) -> AlgorithmResult | None:
        if not self.algorithms:
            return None
        return max(self.algorithms, key=lambda a: a.ndcg)

    def as_dict(self) -> dict:
        return {
            "k": self.k,
            "n_movies": self.n_movies,
            "n_users": self.n_users,
            "n_ratings": self.n_ratings,
            "algorithms": [
                {
                    "name": a.name,
                    "hit_rate": round(a.hit_rate, 4),
                    "precision": round(a.precision, 4),
                    "recall": round(a.recall, 4),
                    "ndcg": round(a.ndcg, 4),
                    "mrr": round(a.mrr, 4),
                    "coverage": round(a.coverage, 4),
                    "diversity": round(a.diversity, 4),
                    "runtime_ms": round(a.runtime_ms, 1),
                    "n_users": a.n_users,
                }
                for a in self.algorithms
            ],
            "timestamp": self.timestamp,
        }


def _mrr_at_k(ranked_ids: list, relevant_ids: set, k: int) -> float:
    for i, mid in enumerate(ranked_ids[:k]):
        if mid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def _evaluate_algo(name: str, recommender_fn, test_users: list[int],
                   heldout: dict[int, set], all_movie_ids: list[int],
                   k: int, pairwise_sim_fn) -> AlgorithmResult:
    t0 = time.time()
    ranked_lists: dict[int, list[int]] = {}
    for uid in test_users:
        try:
            recs = recommender_fn(uid)
            ranked_lists[uid] = [mid for mid, _ in recs][:k] if recs else []
        except Exception as exc:
            logger.debug("用户 %d 推荐失败: %s", uid, exc)
            ranked_lists[uid] = []
    elapsed = (time.time() - t0) * 1000

    # 聚合指标
    hr_list, p_list, r_list, ndcg_list, mrr_list = [], [], [], [], []
    for uid, ranked in ranked_lists.items():
        rel = heldout.get(uid, set())
        if not rel:
            continue
        hr_list.append(1.0 if any(mid in rel for mid in ranked[:k]) else 0.0)
        p_list.append(precision_at_k(ranked, rel, k))
        r_list.append(recall_at_k(ranked, rel, k))
        ndcg_list.append(ndcg_at_k(ranked, rel, k))
        mrr_list.append(_mrr_at_k(ranked, rel, k))

    cov = coverage(list(ranked_lists.values()), len(all_movie_ids))

    # 多样性
    div = diversity(list(ranked_lists.values()), pairwise_sim_fn)

    return AlgorithmResult(
        name=name,
        hit_rate=float(np.mean(hr_list)) if hr_list else 0.0,
        precision=float(np.mean(p_list)) if p_list else 0.0,
        recall=float(np.mean(r_list)) if r_list else 0.0,
        ndcg=float(np.mean(ndcg_list)) if ndcg_list else 0.0,
        mrr=float(np.mean(mrr_list)) if mrr_list else 0.0,
        coverage=cov,
        diversity=div,
        runtime_ms=elapsed,
        n_users=len(hr_list),
    )


def run_full_evaluation(k: int = 10, ratio: float = 0.2, seed: int = 42) -> EvaluationReport:
    """
    运行完整的离线评估，返回 EvaluationReport。
    """
    import random
    from datetime import datetime

    from db.connection import execute_query
    from recommender.collaborative import CollaborativeRecommender
    from recommender.content_based import ContentBasedRecommender
    from recommender.hybrid import HybridRecommender
    from recommender.matrix_factorization import SVDRecommender
    from recommender.user_cf import UserCFRecommender
    from services.movie_service import MovieService
    from services.rating_service import RatingService

    rng = random.Random(seed)
    ms = MovieService()
    rs = RatingService()

    movies = ms.list_movies()
    all_ratings = rs.get_all_ratings()
    all_movie_ids = [m.id for m in movies]

    logger.info("评估数据：%d 电影, %d 评分", len(movies), len(all_ratings))

    # 按用户分组
    user_ratings: dict[int, list[dict]] = {}
    for r in all_ratings:
        uid = r["user_id"]
        if uid not in user_ratings:
            user_ratings[uid] = []
        user_ratings[uid].append(r)

    # 只保留评分 >= 2 条的用户
    valid_users = [uid for uid, rs_list in user_ratings.items() if len(rs_list) >= 2]
    if not valid_users:
        logger.warning("有效用户数为 0，评估无法运行")
        return EvaluationReport(k=k, ratio=ratio, seed=seed)

    # 留一法拆分：每个用户随机留出 ratio 比例的高分评分
    train_ratings: list[dict] = []
    heldout: dict[int, set] = {}
    for uid in valid_users:
        rs_list = user_ratings[uid]
        high = [r for r in rs_list if r["score"] >= 4]
        rng.shuffle(high)
        n_hold = max(1, int(len(high) * ratio))
        held = high[:n_hold]
        heldout[uid] = {r["movie_id"] for r in held}
        kept = set(r["movie_id"] for r in held)
        train_ratings.extend([r for r in rs_list if r["movie_id"] not in kept])

    # 训练各算法
    content = ContentBasedRecommender()
    content.fit(movies)

    item_cf = CollaborativeRecommender()
    item_cf.fit(movies, train_ratings)

    user_cf = UserCFRecommender()
    user_cf.fit(movies, train_ratings)

    svd = SVDRecommender(n_factors=50)
    svd.fit(movies, train_ratings)

    hybrid = HybridRecommender()

    # 相似度函数（用于多样性计算）
    def sim_fn(a_id, b_id):
        return content.pairwise_similarity(a_id, b_id)

    # 热门推荐基线
    from collections import Counter
    pop_counter = Counter(r["movie_id"] for r in train_ratings)
    pop_ranked = [mid for mid, _ in pop_counter.most_common()]

    def popularity_rec(uid):
        return [(mid, 0.0) for mid in pop_ranked[:k]]

    # 随机基线
    def random_rec(uid):
        sample = rng.sample(all_movie_ids, min(k, len(all_movie_ids)))
        return [(mid, 0.0) for mid in sample]

    # 内容推荐函数（基于用户已评高分电影）
    def content_rec(uid):
        liked = [r["movie_id"] for r in train_ratings if r["user_id"] == uid and r["score"] >= 4]
        if not liked:
            return []
        return content.recommend_by_movies(liked[:5], top_n=k)

    # 混合推荐
    def hybrid_rec(uid):
        c_res = content_rec(uid)
        i_res = item_cf.recommend(uid, top_n=k)
        u_res = user_cf.recommend(uid, top_n=k)
        return hybrid.combine3(c_res, i_res, u_res, top_n=k)

    test_users = [uid for uid in valid_users if uid in heldout]
    report = EvaluationReport(
        k=k, ratio=ratio, seed=seed,
        n_movies=len(movies),
        n_users=len(test_users),
        n_ratings=len(all_ratings),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    algo_configs = [
        ("内容推荐 (TF-IDF+LDA+Embed)", content_rec),
        ("物品协同过滤 (Item-CF)", lambda uid: item_cf.recommend(uid, top_n=k)),
        ("用户协同过滤 (User-CF)", lambda uid: user_cf.recommend(uid, top_n=k)),
        ("矩阵分解 (SVD)", lambda uid: svd.recommend(uid, top_n=k)),
        ("混合推荐 (Hybrid)", hybrid_rec),
    ]

    for name, fn in algo_configs:
        logger.info("评估算法: %s", name)
        result = _evaluate_algo(name, fn, test_users, heldout, all_movie_ids, k, sim_fn)
        report.algorithms.append(result)

    report.baseline_popularity = _evaluate_algo(
        "热门基线", popularity_rec, test_users, heldout, all_movie_ids, k, sim_fn)
    report.baseline_random = _evaluate_algo(
        "随机基线", random_rec, test_users, heldout, all_movie_ids, k, sim_fn)

    logger.info("评估完成，最佳算法: %s (NDCG@%d=%.4f)",
                report.best_algorithm().name if report.best_algorithm() else "N/A",
                k,
                report.best_algorithm().ndcg if report.best_algorithm() else 0.0)
    return report
