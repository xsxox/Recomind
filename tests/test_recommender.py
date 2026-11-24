# -*- coding: utf-8 -*-
"""推荐算法单元测试（用户协同过滤、内容主题、MMR 多样性重排）。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_V = os.path.join(ROOT, "vendor")
if os.path.isdir(_V) and _V not in sys.path:
    sys.path.insert(0, _V)

from db.models import Movie  # noqa: E402
from recommender.content_based import ContentBasedRecommender  # noqa: E402
from recommender.diversity import mmr_rerank  # noqa: E402
from recommender.user_cf import UserCFRecommender  # noqa: E402


def _make_movies():
    specs = [
        ("星际穿越", "科幻"), ("火星救援", "科幻"),
        ("速度与激情", "动作"), ("湄公河行动", "动作"),
        ("阿甘正传", "剧情"), ("肖申克的救赎", "剧情"),
    ]
    return [
        Movie(id=i + 1, title=t, genre=g, description=f"{g} 题材的电影《{t}》")
        for i, (t, g) in enumerate(specs)
    ]


def _make_ratings():
    # 用户1/2 喜欢科幻，用户2 兼看动作，用户3 喜欢动作，用户4 喜欢剧情
    return [
        {"user_id": 1, "movie_id": 1, "score": 5},
        {"user_id": 1, "movie_id": 2, "score": 4},
        {"user_id": 2, "movie_id": 1, "score": 5},
        {"user_id": 2, "movie_id": 2, "score": 4},
        {"user_id": 2, "movie_id": 3, "score": 5},
        {"user_id": 3, "movie_id": 3, "score": 5},
        {"user_id": 3, "movie_id": 4, "score": 4},
        {"user_id": 4, "movie_id": 5, "score": 5},
        {"user_id": 4, "movie_id": 6, "score": 4},
    ]


def _run(tests):
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {name}: {exc}")
            failed += 1
    print(f"\n通过 {passed} 项，失败 {failed} 项")
    return failed


def t_user_cf():
    movies = _make_movies()
    ucf = UserCFRecommender().fit(movies, _make_ratings())
    rec = ucf.recommend(1, top_n=5)
    ids = [m.id for m, _s in rec]
    assert 3 in ids, "用户1 应被推荐相似用户2 喜欢的动作片"
    assert 1 not in ids and 2 not in ids, "不应推荐已评分电影"


def t_content():
    movies = _make_movies()
    cb = ContentBasedRecommender(topic_weight=0.2).fit(movies)
    rec = cb.recommend_by_movie(1, top_n=5)
    ids = [m.id for m, _s in rec]
    assert 2 in ids, "《星际穿越》应推荐同为科幻的《火星救援》"
    assert 1 not in ids
    assert abs(cb.pairwise_similarity(1, 1) - 1.0) < 1e-6, "自身相似度应为 1"


def t_mmr():
    movies = _make_movies()
    cb = ContentBasedRecommender(topic_weight=0.2).fit(movies)
    candidates = [(movies[0], 1.0), (movies[1], 0.95), (movies[2], 0.6), (movies[4], 0.5)]
    ranked = mmr_rerank(candidates, cb.pairwise_similarity, lambda_param=0.5, top_n=3)
    assert len(ranked) == 3
    assert ranked[0][0].id == 1, "最高相关度应排在首位"


if __name__ == "__main__":
    sys.exit(_run([
        ("用户协同过滤", t_user_cf),
        ("内容推荐 (TF-IDF+LDA)", t_content),
        ("MMR 多样性重排", t_mmr),
    ]))
