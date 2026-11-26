# -*- coding: utf-8 -*-
"""
抓取 TMDB 真实影评（中文优先，无则英文兜底）
用法：python -m scripts.fetch_reviews
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from db.connection import execute_query, execute_update
from db.init_db import init_database
from services.tmdb_service import tmdb_get
from utils.logger import get_logger

logger = get_logger("scripts.reviews")


def _fetch_reviews_for_movie(movie, limit):
    results = []
    for lang in ("zh-CN", "en-US"):
        try:
            data = tmdb_get(f"/movie/{movie['tmdb_id']}/reviews", {"page": 1}, language=lang)
            results = data.get("results") or []
            if results:
                break
        except Exception:  # noqa: BLE001
            continue

    picked = []
    seen = set()
    for r in results:
        content = (r.get("content") or "").strip()
        if not content or content in seen:
            continue
        seen.add(content)
        picked.append({
            "movie_id": movie["id"],
            "author": r.get("author") or "匿名",
            "content": content[:1200],
            "rating": (r.get("author_details") or {}).get("rating") or 0,
            "created_at": (r.get("created_at") or "")[:19],
        })
        if len(picked) >= limit:
            break
    return picked


def fetch_all(limit=5):
    if not config.TMDB_API_KEY:
        print("请先在 config.py 填写 TMDB_API_KEY")
        return
    init_database()
    movies = execute_query(
        "SELECT id, tmdb_id, title FROM movies WHERE tmdb_id IS NOT NULL ORDER BY id"
    )
    execute_update("DELETE FROM reviews")
    print(f"待抓取 {len(movies)} 部电影的影评")

    total = 0
    covered = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_fetch_reviews_for_movie, m, limit) for m in movies]
        for idx, fut in enumerate(as_completed(futures), 1):
            try:
                items = fut.result()
                if items:
                    covered += 1
                    for rv in items:
                        execute_update(
                            "INSERT INTO reviews (movie_id, author, content, rating, created_at) "
                            "VALUES (%s,%s,%s,%s,%s)",
                            (rv["movie_id"], rv["author"], rv["content"], rv["rating"], rv["created_at"]),
                        )
                        total += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("抓取影评失败: %s", exc)
            if idx % 50 == 0:
                print(f"进度 {idx}/{len(movies)}，影评 {total} 条")

    print(f"完成：影评 {total} 条，覆盖 {covered}/{len(movies)} 部电影")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取 TMDB 真实影评")
    parser.add_argument("--limit", type=int, default=5, help="每部电影最多保留影评条数")
    args = parser.parse_args()
    fetch_all(limit=args.limit)