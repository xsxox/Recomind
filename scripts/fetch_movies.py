# -*- coding: utf-8 -*-
"""
从 TMDB 拉取真实电影片库
用法：
    python -m scripts.fetch_movies            # 默认 3 页高分 + 3 页热门
    python -m scripts.fetch_movies --pages 5  # 拉取更多
会清空旧片库，重新写入真实电影、海报、TMDB 评分与影评，并为演示用户生成模拟评分。
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import date

import config
from data.simulate_ratings import simulate_ratings
from db.connection import execute_query, execute_update
from db.init_db import init_database
from utils.logger import get_logger

logger = get_logger("scripts.movies")

MIN_VOTE_COUNT = 300  # 过滤评分人数过少的冷门/新片

API = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"

GENRE_COLORS = {
    "动作": "#E74C3C", "冒险": "#E67E22", "动画": "#00B894", "喜剧": "#F39C12",
    "犯罪": "#8E44AD", "纪录": "#7F8C8D", "剧情": "#D35400", "家庭": "#16A085",
    "奇幻": "#0984E3", "历史": "#16A085", "恐怖": "#2D3436", "音乐": "#E84393",
    "悬疑": "#2D3436", "爱情": "#E84393", "科幻": "#6C5CE7", "电视电影": "#636E72",
    "惊悚": "#C0392B", "战争": "#7F8C8D", "西部": "#A0522D",
}
DEFAULT_COLOR = "#4A90D9"


def _get(path, params=None):
    params = dict(params or {})
    params["api_key"] = config.TMDB_API_KEY
    params["language"] = config.TMDB_LANGUAGE
    url = API + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Recomind/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _collect_ids(pages):
    ids = []
    for endpoint in ("/movie/top_rated", "/movie/popular"):
        for page in range(1, pages + 1):
            data = _get(endpoint, {"page": page})
            for result in data.get("results") or []:
                mid = result.get("id")
                if mid and mid not in ids:
                    ids.append(mid)
    return ids


def _detail(movie_id):
    return _get(f"/movie/{movie_id}", {"append_to_response": "credits,reviews"})


def _genres_text(genres):
    names = [g.get("name") for g in genres if g.get("name")]
    return "/".join(names[:2]) if names else ""


def _director(credits):
    names = [
        c.get("name") for c in (credits.get("crew") or [])
        if c.get("job") == "Director" and c.get("name")
    ]
    return " / ".join(dict.fromkeys(names)) if names else ""


def _studio(detail):
    companies = detail.get("production_companies") or []
    return companies[0].get("name") if companies else ""


def ingest(pages=3, keep=False):
    if not config.TMDB_API_KEY:
        print("请先在 config.py 填写 TMDB_API_KEY")
        return
    init_database()
    ids = _collect_ids(pages)
    print(f"待抓取电影 {len(ids)} 部")

    if not keep:
        execute_update("DELETE FROM reviews")
        execute_update("DELETE FROM browse_history")
        execute_update("DELETE FROM ratings")
        execute_update("DELETE FROM movies")
        print("已清空旧片库")

    inserted = 0
    review_count = 0
    for idx, mid in enumerate(ids, 1):
        try:
            detail = _detail(mid)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {mid}: {exc}")
            continue

        title = detail.get("title") or detail.get("original_title") or ""
        if not title:
            continue

        release_date = detail.get("release_date") or ""
        if release_date and release_date > date.today().isoformat():
            continue  # 跳过尚未上映的影片
        if (detail.get("vote_count") or 0) < MIN_VOTE_COUNT:
            continue  # 跳过评分人数过少的冷门影片

        genres = detail.get("genres") or []
        genre = _genres_text(genres)
        main_genre = genres[0].get("name") if genres else ""
        release = (detail.get("release_date") or "")[:4]
        year = int(release) if release.isdigit() else 0
        poster_path = detail.get("poster_path")
        poster_url = IMG + poster_path if poster_path else None
        color = GENRE_COLORS.get(main_genre, DEFAULT_COLOR)

        _, movie_id = execute_update(
            "INSERT INTO movies (tmdb_id, title, director, studio, genre, release_year, "
            "description, poster_color, poster_url, vote_average, vote_count) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                mid, title, _director(detail.get("credits") or {}), _studio(detail),
                genre, year, detail.get("overview") or "", color, poster_url,
                detail.get("vote_average") or 0, detail.get("vote_count") or 0,
            ),
        )
        inserted += 1

        for review in (detail.get("reviews") or {}).get("results", [])[:3]:
            content = (review.get("content") or "").strip()
            if not content:
                continue
            execute_update(
                "INSERT INTO reviews (movie_id, author, content, rating, created_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (
                    movie_id, review.get("author") or "匿名", content[:1000],
                    (review.get("author_details") or {}).get("rating") or 0,
                    (review.get("created_at") or "")[:19],
                ),
            )
            review_count += 1

        if idx % 20 == 0:
            print(f"进度 {idx}/{len(ids)}，已入库 {inserted} 部")
        time.sleep(0.12)

    print(f"完成：电影 {inserted} 部，影评 {review_count} 条")
    simulate_ratings()
    return inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 TMDB 拉取真实电影片库")
    parser.add_argument("--pages", type=int, default=3, help="每个榜单抓取页数（每页 20 部）")
    parser.add_argument("--keep", action="store_true", help="保留现有片库，不清空")
    args = parser.parse_args()
    ingest(pages=args.pages, keep=args.keep)
