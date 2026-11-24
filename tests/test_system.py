# -*- coding: utf-8 -*-
"""
系统自检脚本
验证：1) NLP 分词与 TF-IDF；2) 内容推荐与协同过滤；3) 数据库集成与推荐服务。

运行方式：
    python tests/test_system.py           # 基础自检（不重置数据）
    python tests/test_system.py --reset   # 先重置并重新导入示例数据再自检
"""
import argparse
import os
import sys

# 将项目根目录与 vendor 目录加入模块搜索路径
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_VENDOR = os.path.join(ROOT, "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

_PASSED = []
_FAILED = []


def check(name, func):
    """执行一项检查并记录结果。"""
    try:
        func()
        _PASSED.append(name)
        print(f"[PASS] {name}")
    except Exception as exc:  # noqa: BLE001
        _FAILED.append((name, exc))
        print(f"[FAIL] {name}: {exc}")


def test_nlp():
    from nlp.feature import TextFeatureExtractor
    from nlp.text_processor import segment, tokenize

    words = tokenize("机器学习是人工智能领域的重要研究方向")
    assert len(words) > 0, "分词结果为空"
    seg = segment("中国古代历史与文化")
    assert " " in seg, "分词未正确连接"

    extractor = TextFeatureExtractor()
    matrix = extractor.fit_transform([
        "机器学习 人工智能 神经网络",
        "中国古代 历史 文化 文明",
        "机器学习 编程 Python 数据",
    ])
    assert matrix is not None, "TF-IDF 矩阵为空"
    sims = extractor.similarity(extractor.transform(["机器学习 人工智能"]))
    assert len(sims) == 3, "相似度维度错误"


def test_recommender_algorithms():
    from db.models import Movie
    from data.sample_data import MOVIES, RATINGS, USERS
    from recommender.collaborative import CollaborativeRecommender
    from recommender.content_based import ContentBasedRecommender
    from recommender.hybrid import HybridRecommender

    movies = [Movie(id=i + 1, title=b["title"], director=b["director"],
                  genre=b["genre"], description=b["desc"]) for i, b in enumerate(MOVIES)]
    title_to_id = {b["title"]: i + 1 for i, b in enumerate(MOVIES)}
    username_to_id = {u["username"]: i + 1 for i, u in enumerate(USERS)}
    ratings = [{"user_id": username_to_id[u], "movie_id": title_to_id[t], "score": s}
               for u, t, s, _c in RATINGS]

    # 内容推荐
    content = ContentBasedRecommender().fit(movies)
    sim = content.recommend_by_movie(1, top_n=5)
    assert len(sim) > 0, "内容推荐无结果"

    # 协同过滤
    collab = CollaborativeRecommender().fit(movies, ratings)
    cf = collab.recommend(username_to_id["alice"], top_n=5)
    assert len(cf) > 0, "协同过滤无结果"

    # 混合推荐
    hybrid = HybridRecommender().combine(sim, cf, top_n=5)
    assert len(hybrid) > 0, "混合推荐无结果"


def test_database_and_service(reset):
    from data.seed_data import seed
    from db.init_db import init_database
    from services.recommend_service import RecommendService
    from services.user_service import UserService

    init_database()
    seed(force=reset)

    user_service = UserService()
    alice, err = user_service.login("alice", "123456")
    assert err is None, f"登录失败: {err}"

    recommend = RecommendService()
    results = recommend.recommend_for_user(alice.id)
    assert len(results) > 0, "个性化推荐无结果"

    similar = recommend.similar_movies(results[0][0].id, top_n=5)
    assert len(similar) > 0, "相似推荐无结果"

    by_kw = recommend.recommend_by_keyword("科幻 宇宙", top_n=5)
    assert len(by_kw) > 0, "关键词推荐无结果"

    print(f"      个性化推荐 Top3: " +
          ", ".join(f"{b.title}({s:.2f})" for b, s in results[:3]))


def main():
    parser = argparse.ArgumentParser(description="Recomind 系统自检")
    parser.add_argument("--reset", action="store_true", help="重置并重新导入示例数据")
    args = parser.parse_args()

    check("NLP 分词与 TF-IDF", test_nlp)
    check("推荐算法（内容/协同/混合）", test_recommender_algorithms)
    check("数据库与服务集成", lambda: test_database_and_service(args.reset))

    print("\n" + "=" * 50)
    print(f"自检完成：通过 {len(_PASSED)} 项，失败 {len(_FAILED)} 项")
    if _FAILED:
        for name, exc in _FAILED:
            print(f"  - {name}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
