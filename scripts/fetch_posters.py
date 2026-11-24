# -*- coding: utf-8 -*-
"""
抓取 TMDB 电影海报
用法：先在 config.py 填入 TMDB_API_KEY，再运行：
    python -m scripts.fetch_posters
可选参数：--force 重新抓取已有海报
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

logger = get_logger("scripts.posters")

TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"


def _search_poster(title, year):
    params = {
        "api_key": config.TMDB_API_KEY,
        "query": title,
        "language": config.TMDB_LANGUAGE,
        "include_adult": "false",
    }
    if year:
        params["year"] = str(year)
    url = TMDB_SEARCH + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Recomind/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for result in data.get("results") or []:
        if result.get("poster_path"):
            return TMDB_IMG + result["poster_path"]
    return None


def fetch_all(force=False):
    if not config.TMDB_API_KEY:
        print("请先在 config.py 中填写 TMDB_API_KEY")
        print("免费申请：https://www.themoviedb.org/settings/api")
        return
    init_database()
    rows = execute_query("SELECT id, title, release_year, poster_url FROM movies ORDER BY id")
    updated = 0
    for row in rows:
        if row.get("poster_url") and not force:
            continue
        try:
            url = _search_poster(row["title"], row["release_year"])
            if url:
                execute_update("UPDATE movies SET poster_url=%s WHERE id=%s", (url, row["id"]))
                updated += 1
                print(f"OK   {row['title']} -> {url}")
            else:
                print(f"--   {row['title']} 未找到海报")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {row['title']}: {exc}")
        time.sleep(0.26)  # 控制请求频率
    print(f"完成：更新 {updated} 部电影海报")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取 TMDB 电影海报")
    parser.add_argument("--force", action="store_true", help="重新抓取已有海报")
    args = parser.parse_args()
    fetch_all(force=args.force)
