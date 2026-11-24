# -*- coding: utf-8 -*-
"""
多样性重排模块
使用 MMR（Maximal Marginal Relevance）在“相关度”与“多样性”之间取得平衡，
避免推荐结果高度雷同。
"""


def mmr_rerank(candidates, similarity_fn, lambda_param=0.7, top_n=10):
    """对候选集做 MMR 重排。

    :param candidates: 已按相关度降序的 [(movie, score)]，score 需归一化到 [0,1]
    :param similarity_fn: callable(movie_a_id, movie_b_id) -> float 相似度 [0,1]
    :param lambda_param: 相关度权重（越大越看重相关度，越小越看重多样性）
    :param top_n: 返回条数
    :return: 重排后的 [(movie, score)]
    """
    if not candidates:
        return []
    pool = list(candidates)
    selected = []
    while pool and len(selected) < top_n:
        best = None
        best_val = float("-inf")
        for cand in pool:
            relevance = cand[1]
            redundancy = 0.0
            if selected:
                redundancy = max(similarity_fn(cand[0].id, s[0].id) for s in selected)
            value = lambda_param * relevance - (1.0 - lambda_param) * redundancy
            if value > best_val:
                best_val = value
                best = cand
        if best is None:
            break
        selected.append(best)
        pool.remove(best)
    return selected
