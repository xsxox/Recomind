# -*- coding: utf-8 -*-
"""
推荐系统评估指标
包含命中率、精确率、召回率、NDCG、覆盖率与多样性等常用离线评测指标。
"""
import numpy as np


def hit_rate(ranked_ids, relevant_ids, k):
    """Top-K 命中率：推荐列表中是否至少命中一个相关项。"""
    return 1.0 if any(i in relevant_ids for i in ranked_ids[:k]) else 0.0


def precision_at_k(ranked_ids, relevant_ids, k):
    """Top-K 精确率：推荐列表中相关项占比。"""
    if k <= 0:
        return 0.0
    hits = sum(1 for i in ranked_ids[:k] if i in relevant_ids)
    return hits / k


def recall_at_k(ranked_ids, relevant_ids, k):
    """Top-K 召回率：相关项中被推荐出的占比。"""
    if not relevant_ids:
        return 0.0
    hits = sum(1 for i in ranked_ids[:k] if i in relevant_ids)
    return hits / len(relevant_ids)


def ndcg_at_k(ranked_ids, relevant_ids, k):
    """Top-K NDCG（二值相关，DCG 采用对数折损）。"""
    dcg = sum(1.0 / np.log2(idx + 2) for idx, i in enumerate(ranked_ids[:k]) if i in relevant_ids)
    ideal_n = min(k, len(relevant_ids))
    idcg = sum(1.0 / np.log2(idx + 2) for idx in range(ideal_n))
    return dcg / idcg if idcg > 0 else 0.0


def coverage(ranked_lists, n_items):
    """覆盖率：所有推荐结果命中的不同物品占物品总数的比例。"""
    seen = set()
    for ranked in ranked_lists:
        seen.update(ranked)
    return len(seen) / n_items if n_items else 0.0


def diversity(ranked_lists, similarity_fn):
    """多样性：各推荐列表内 1 - 平均两两相似度 的均值。"""
    divs = []
    for ranked in ranked_lists:
        if len(ranked) < 2:
            divs.append(0.0)
            continue
        total = 0.0
        cnt = 0
        for a in range(len(ranked)):
            for b in range(a + 1, len(ranked)):
                total += similarity_fn(ranked[a], ranked[b])
                cnt += 1
        divs.append(1.0 - total / cnt if cnt else 0.0)
    return float(np.mean(divs)) if divs else 0.0


def evaluate_ranked(ranked_lists, heldout, k):
    """汇总各用户的命中率/精确率/召回率/NDCG，返回平均指标。

    :param ranked_lists: {user_id: [movie_id, ...]} 每个用户的 Top-K 推荐
    :param heldout: {user_id: set(movie_id)} 每个用户留出的真实相关项
    :param k: Top-K
    """
    hr, prec, rec, ndcg = [], [], [], []
    for uid, ranked in ranked_lists.items():
        rel = heldout.get(uid, set())
        if not rel:
            continue
        hr.append(hit_rate(ranked, rel, k))
        prec.append(precision_at_k(ranked, rel, k))
        rec.append(recall_at_k(ranked, rel, k))
        ndcg.append(ndcg_at_k(ranked, rel, k))
    return {
        "hit_rate": float(np.mean(hr)) if hr else 0.0,
        "precision": float(np.mean(prec)) if prec else 0.0,
        "recall": float(np.mean(rec)) if rec else 0.0,
        "ndcg": float(np.mean(ndcg)) if ndcg else 0.0,
    }
