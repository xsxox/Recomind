# -*- coding: utf-8 -*-
"""
抓取 TMDB 关键词，丰富电影内容特征
用法：python -m scripts.fetch_keywords
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from db.connection import execute_query, execute_update
from db.init_db import init_database
from services.tmdb_service import tmdb_get
from utils.logger import get_logger

logger = get_logger("scripts.keywords")


def _fetch_one(movie):
    data = tmdb_get(f"/movie/{movie['tmdb_id']}/keywords", {}, language="")
    kws = [k.get("name") for k in (data.get("keywords") or []) if k.get("name")]
    return movie["id"], " ".join(kws[:12]) if kws else ""


def fetch_all():
    if not config.TMDB_API_KEY:
        print("请先在 config.py 填写 TMDB_API_KEY")
        return
    init_database()
    movies = execute_query("SELECT id, tmdb_id, title FROM movies WHERE tmdb_id IS NOT NULL")
    updated = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_fetch_one, m) for m in movies]
        for idx, fut in enumerate(as_completed(futures), 1):
            try:
                mid, kw_text = fut.result()
                if kw_text:
                    execute_update("UPDATE movies SET keywords=%s WHERE id=%s", (kw_text, mid))
                    updated += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("抓取关键词失败: %s", exc)
            if idx % 50 == 0:
                print(f"进度 {idx}/{len(movies)}")
    print(f"完成：为 {updated} 部电影写入关键词")


if __name__ == "__main__":
    fetch_all()