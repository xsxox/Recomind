# -*- coding: utf-8 -*-
"""
离线推荐评估脚本
对内容推荐、物品协同过滤、用户协同过滤、混合推荐进行随机留出法评估，
并与热门、随机两个基线对比。

用法：
    python -m scripts.evaluate --k 10 --ratio 0.2 --seed 42
"""
import argparse
import os
import random
import sys
from collections import Counter, defaultdict

# 将项目根目录与 vendor 目录加入模块搜索路径
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_VENDOR = os.path.join(ROOT, "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

import config  # noqa: E402
from db import models  # noqa: E402
from db.connection import execute_query  # noqa: E402
from evaluation.metrics import coverage, diversity, evaluate_ranked  # noqa: E402
from recommender.collaborative import CollaborativeRecommender  # noqa: E402
from recommender.content_based import ContentBasedRecommender  # noqa: E402
from recommender.diversity import mmr_rerank  # noqa: E402
from recommender.hybrid import HybridRecommender  # noqa: E402
from recommender.user_cf import UserCFRecommender  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("scripts.evaluate")


def load_data():
    """从数据库加载电影与评分。"""
    movies = [models.Movie.from_dict(r) for r in execute_query("SELECT * FROM movies ORDER BY id")]
    ratings = execute_query("SELECT user_id, movie_id, score FROM ratings")
    return movies, ratings


def split_ratings(ratings, ratio, seed, min_train=2):
    """按用户做随机留出划分，返回 (train_ratings, heldout)。"""
    rng = random.Random(seed)
    by_user = defaultdict(list)
    for r in ratings:
        by_user[r["user_id"]].append(r)

    train, heldout = [], {}
    for uid, items in by_user.items():
        if len(items) < 3:
            train.extend(items)
            continue
        rng.shuffle(items)
        n_hold = max(1, int(round(len(items) * ratio)))
        n_hold = min(n_hold, len(items) - min_train)
        hold_items = items[:n_hold]
        train.extend(items[n_hold:])
        heldout[uid] = {r["movie_id"] for r in hold_items}
    return train, heldout


def main():
    parser = argparse.ArgumentParser(description="离线推荐评估")
    parser.add_argument("--k", type=int, default=config.EVAL_TOP_K)
    parser.add_argument("--ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    movies, ratings = load_data()
    if not movies or not ratings:
        print("数据不足，无法评估")
        return

    train, heldout = split_ratings(ratings, args.ratio, args.seed)
    users = list(heldout.keys())
    print(f"电影 {len(movies)} 部，评分 {len(ratings)} 条，评估用户 {len(users)} 人，Top-K={args.k}")

    content = ContentBasedRecommender(topic_weight=config.TOPIC_WEIGHT).fit(movies)
    item_cf = CollaborativeRecommender().fit(movies, train)
    user_cf = UserCFRecommender().fit(movies, train)
    hybrid = HybridRecommender()

    all_movie_ids = [m.id for m in movies]
    train_by_user = defaultdict(list)
    for r in train:
        train_by_user[r["user_id"]].append((r["movie_id"], r["score"]))

    # 热门基线：按训练集评分次数降序
    count = Counter(r["movie_id"] for r in train)
    popular_order = [mid for mid, _c in count.most_common()]

    def content_ranked(uid):
        items = train_by_user.get(uid, [])
        rated = {mid for mid, _s in items}
        profile = [mid for mid, s in items if s >= 4] or [mid for mid, _s in items]
        res = content.recommend_by_movies(profile, top_n=args.k, exclude_ids=rated)
        return [m.id for m, _s in res]

    def item_cf_ranked(uid):
        return [m.id for m, _s in item_cf.recommend(uid, top_n=args.k)]

    def user_cf_ranked(uid):
        return [m.id for m, _s in user_cf.recommend(uid, top_n=args.k)]

    def hybrid_ranked(uid):
        items = train_by_user.get(uid, [])
        rated = {mid for mid, _s in items}
        profile = [mid for mid, s in items if s >= 4] or [mid for mid, _s in items]
        c = content.recommend_by_movies(profile, top_n=50, exclude_ids=rated)
        icf = item_cf.recommend(uid, top_n=50)
        ucf = user_cf.recommend(uid, top_n=50)
        blended = hybrid.combine3(c, icf, ucf, top_n=50)
        reranked = mmr_rerank(blended, content.pairwise_similarity, config.MMR_LAMBDA, args.k)
        return [m.id for m, _s in reranked]

    def popular_ranked(uid):
        rated = {mid for mid, _s in train_by_user.get(uid, [])}
        return [mid for mid in popular_order if mid not in rated][:args.k]

    def random_ranked(uid):
        rated = {mid for mid, _s in train_by_user.get(uid, [])}
        pool = [mid for mid in all_movie_ids if mid not in rated]
        rng = random.Random(args.seed + uid)
        rng.shuffle(pool)
        return pool[:args.k]

    algorithms = {
        "内容推荐 (Content)": content_ranked,
        "物品协同 (Item-CF)": item_cf_ranked,
        "用户协同 (User-CF)": user_cf_ranked,
        "混合推荐 (Hybrid+MMR)": hybrid_ranked,
        "热门基线 (Popularity)": popular_ranked,
        "随机基线 (Random)": random_ranked,
    }

    print("\n" + "=" * 82)
    print(f"{'算法':<26}{'HitRate':>9}{'Precision':>11}{'Recall':>9}{'NDCG':>9}{'Coverage':>10}{'Diversity':>11}")
    print("-" * 82)
    for name, fn in algorithms.items():
        ranked = {uid: fn(uid) for uid in users}
        metrics = evaluate_ranked(ranked, heldout, args.k)
        cov = coverage(list(ranked.values()), len(all_movie_ids))
        div = diversity(list(ranked.values()), content.pairwise_similarity)
        print(
            f"{name:<26}"
            f"{metrics['hit_rate']:>9.4f}"
            f"{metrics['precision']:>11.4f}"
            f"{metrics['recall']:>9.4f}"
            f"{metrics['ndcg']:>9.4f}"
            f"{cov:>10.4f}"
            f"{div:>11.4f}"
        )
    print("=" * 82)


if __name__ == "__main__":
    main()
