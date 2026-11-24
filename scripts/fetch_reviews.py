# -*- coding: utf-8 -*-
"""
抓取 TMDB 真实影评（中文优先，无则英文兜底）
用法：python -m scripts.fetch_reviews
会清空 reviews 表，按电影重新抓取，每部最多保留 LIMIT 条。
"""
import argparse
import json
import time
import urllib.parse
import urllib.request

import config
from db.connection import execute_query, execute_update
from db.init_db import init_database
from utils.logger import get_logger

logger = get_logger("scripts.reviews")

API = "https://api.themoviedb.org/3"


def _get(path, params):
    params = dict(params)
    params["api_key"] = config.TMDB_API_KEY
    url = API + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Recomind/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _reviews(tmdb_id, language):
    try:
        data = _get(f"/movie/{tmdb_id}/reviews", {"language": language, "page": 1})
        return data.get("results") or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("获取影评失败 %s: %s", tmdb_id, exc)
        return []


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
    for idx, movie in enumerate(movies, 1):
        results = _reviews(movie["tmdb_id"], "zh-CN")
        if not results:
            results = _reviews(movie["tmdb_id"], config.TMDB_LANGUAGE)
        if not results:
            results = _reviews(movie["tmdb_id"], "en-US")

        picked = 0
        seen = set()
        for review in results:
            content = (review.get("content") or "").strip()
            if not content or content in seen:
                continue
            seen.add(content)
            execute_update(
                "INSERT INTO reviews (movie_id, author, content, rating, created_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (
                    movie["id"],
                    review.get("author") or "匿名",
                    content[:1200],
                    (review.get("author_details") or {}).get("rating") or 0,
                    (review.get("created_at") or "")[:19],
                ),
            )
            picked += 1
            total += 1
            if picked >= limit:
                break
        if picked:
            covered += 1
        if idx % 20 == 0:
            print(f"进度 {idx}/{len(movies)}，影评 {total} 条")
        time.sleep(0.12)

    print(f"完成：影评 {total} 条，覆盖 {covered}/{len(movies)} 部电影")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取 TMDB 真实影评")
    parser.add_argument("--limit", type=int, default=5, help="每部电影最多保留影评条数")
    args = parser.parse_args()
    fetch_all(limit=args.limit)
