# -*- coding: utf-8 -*-
"""
抓取 TMDB 关键词，丰富电影内容特征
用法：python -m scripts.fetch_keywords
"""
import json
import time
import urllib.parse
import urllib.request

import config
from db.connection import execute_query, execute_update
from db.init_db import init_database
from utils.logger import get_logger

logger = get_logger("scripts.keywords")

API = "https://api.themoviedb.org/3"


def _get(path, params):
    params = dict(params or {})
    params["api_key"] = config.TMDB_API_KEY
    url = API + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Recomind/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all():
    if not config.TMDB_API_KEY:
        print("请先在 config.py 填写 TMDB_API_KEY")
        return
    init_database()
    movies = execute_query("SELECT id, tmdb_id, title FROM movies WHERE tmdb_id IS NOT NULL")
    updated = 0
    for idx, movie in enumerate(movies, 1):
        try:
            data = _get(f"/movie/{movie['tmdb_id']}/keywords", {})
            keywords = [k.get("name") for k in (data.get("keywords") or []) if k.get("name")]
            if keywords:
                execute_update(
                    "UPDATE movies SET keywords=%s WHERE id=%s",
                    (" ".join(keywords[:10]), movie["id"]),
                )
                updated += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {movie['title']}: {exc}")
        if idx % 20 == 0:
            print(f"进度 {idx}/{len(movies)}")
        time.sleep(0.1)
    print(f"完成：为 {updated} 部电影写入关键词")


if __name__ == "__main__":
    fetch_all()
