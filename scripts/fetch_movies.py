# -*- coding: utf-8 -*-
"""
从 TMDB 增量扩充全题材电影片库
会自动跳过本地已存在的 tmdb_id，只拉取全新电影（带海报、关键词、TMDB 评分与中英文影评）。

用法：
    python -m scripts.fetch_movies --add 1000   # 在现有基础上再抓约 1000 部新电影
    python -m scripts.fetch_movies --pages 5    # 按页数增量抓取
    python -m scripts.fetch_movies --reset      # 清空后全量重建
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import config
from data.simulate_ratings import simulate_ratings
from db.connection import execute_query, execute_update
from db.init_db import init_database
from services.tmdb_service import TMDB_GENRE_MAP, TmdbService, tmdb_get
from utils.logger import get_logger

logger = get_logger("scripts.movies")

MIN_VOTE_COUNT = 100


def _collect_new_ids(existing_ids, target_candidates=1200, max_pages=15):
    """从多榜单及全 18 个类型发现流收集尚未入库的 TMDB ID。"""
    seen = set(existing_ids)
    new_ids = []

    def add_results(results):
        for r in results or []:
            mid = r.get("id")
            if mid and mid not in seen:
                seen.add(mid)
                new_ids.append(mid)

    # 1. 热门榜、高分榜、热映榜深翻页
    for page in range(1, max_pages + 1):
        endpoints = ("/movie/popular", "/movie/top_rated", "/movie/now_playing") if page <= 3 else ("/movie/popular", "/movie/top_rated")
        for endpoint in endpoints:
            try:
                data = tmdb_get(endpoint, {"page": page})
                add_results(data.get("results"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("采集 %s page=%s 失败: %s", endpoint, page, exc)
            if len(new_ids) >= target_candidates:
                return new_ids

    # 2. 全 18 个类型交替按评分人数 & 流行度深翻页
    for page in range(1, max_pages + 1):
        sort_by = "vote_count.desc" if page % 2 == 1 else "popularity.desc"
        for gid in TMDB_GENRE_MAP:
            try:
                data = tmdb_get(
                    "/discover/movie",
                    {
                        "with_genres": gid,
                        "sort_by": sort_by,
                        "vote_count.gte": MIN_VOTE_COUNT,
                        "page": page,
                    },
                )
                add_results(data.get("results"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("采集类型 %s page=%s 失败: %s", gid, page, exc)
            if len(new_ids) >= target_candidates:
                return new_ids

    return new_ids


def ingest(pages=3, keep=True, target_new=None):
    """增量/全量拉取电影；target_new 指定希望新增的部数。"""
    if not config.TMDB_API_KEY:
        print("请先在 config.py 填写 TMDB_API_KEY")
        return 0
    init_database()
    tmdb = TmdbService()

    if not keep:
        execute_update("DELETE FROM reviews")
        execute_update("DELETE FROM browse_history")
        execute_update("DELETE FROM ratings")
        execute_update("DELETE FROM movies")
        existing_ids = set()
        print("已清空旧片库")
    else:
        rows = execute_query("SELECT tmdb_id FROM movies WHERE tmdb_id IS NOT NULL")
        existing_ids = {r["tmdb_id"] for r in rows}
        print(f"本地已有 {len(existing_ids)} 部电影，将自动跳过这些片源")

    want_new = target_new if target_new is not None else pages * 180
    target_candidates = int(want_new * 1.2)
    max_pages = max(12, pages, (want_new // 60) + 4)

    ids = _collect_new_ids(existing_ids, target_candidates=target_candidates, max_pages=max_pages)
    print(f"已发现待抓新电影 {len(ids)} 部，开始 8 线程并发拉取详情与影评…")

    today_str = date.today().isoformat()
    bundles = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(tmdb.fetch_bundle, mid): mid for mid in ids}
        for idx, fut in enumerate(as_completed(futures), 1):
            mid = futures[fut]
            try:
                b = fut.result()
                if not b["title"]:
                    continue
                if b["release_date"] and b["release_date"] > today_str:
                    continue
                if (b["vote_count"] or 0) < MIN_VOTE_COUNT:
                    continue
                bundles.append(b)
            except Exception as exc:  # noqa: BLE001
                logger.warning("抓取电影 %s 失败: %s", mid, exc)
            if idx % 100 == 0 or idx == len(ids):
                print(f"拉取进度 {idx}/{len(ids)}，有效新片 {len(bundles)} 部")

    if target_new is not None and len(bundles) > target_new:
        bundles = bundles[:target_new]

    saved = 0
    review_count = 0
    for idx, b in enumerate(bundles, 1):
        tmdb.upsert_bundle(b)
        saved += 1
        review_count += len(b.get("reviews") or [])
        if idx % 200 == 0:
            print(f"写入数据库 {idx}/{len(bundles)}…")

    total_now = execute_query("SELECT COUNT(*) AS c FROM movies")[0]["c"]
    print(f"新增完成：本次入库 {saved} 部，同步影评 {review_count} 条，当前片库总计 {total_now} 部！")
    simulate_ratings()
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 TMDB 增量扩充电影片库")
    parser.add_argument("--pages", type=int, default=5, help="榜单翻页深度")
    parser.add_argument("--add", type=int, default=None, help="目标新增电影部数，例如 --add 1000")
    parser.add_argument("--reset", action="store_true", help="清空原有片库与评分后全量重建")
    args = parser.parse_args()
    ingest(pages=args.pages, keep=not args.reset, target_new=args.add)