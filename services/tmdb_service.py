# -*- coding: utf-8 -*-
"""
TMDB 在线服务
提供全网电影实时搜索与单部电影完整元数据（详情、海报、关键词、真实影评）一键入库。
"""
import json
import urllib.parse
import urllib.request

import config
from services.movie_service import MovieService
from db import models
from db.connection import execute_query, execute_update
from utils.logger import get_logger

logger = get_logger("services.tmdb")

API = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"

TMDB_GENRE_MAP = {
    28: "动作", 12: "冒险", 16: "动画", 35: "喜剧", 80: "犯罪",
    99: "纪录", 18: "剧情", 10751: "家庭", 14: "奇幻", 36: "历史",
    27: "恐怖", 10402: "音乐", 9648: "悬疑", 10749: "爱情", 878: "科幻",
    10770: "电视电影", 53: "惊悚", 10752: "战争", 37: "西部",
}

GENRE_COLORS = {
    "动作": "#E74C3C", "冒险": "#E67E22", "动画": "#00B894", "喜剧": "#F39C12",
    "犯罪": "#8E44AD", "纪录": "#7F8C8D", "剧情": "#D35400", "家庭": "#16A085",
    "奇幻": "#0984E3", "历史": "#16A085", "恐怖": "#2D3436", "音乐": "#E84393",
    "悬疑": "#2D3436", "爱情": "#E84393", "科幻": "#6C5CE7", "电视电影": "#636E72",
    "惊悚": "#C0392B", "战争": "#7F8C8D", "西部": "#A0522D",
}
DEFAULT_COLOR = "#4A90D9"


def tmdb_get(path, params=None, language=None, timeout=15):
    """请求 TMDB v3 接口（自动携带 api_key 并带简单重试）。"""
    if not config.TMDB_API_KEY:
        raise ValueError("尚未在 config.py 中配置 TMDB_API_KEY")
    q = dict(params or {})
    q["api_key"] = config.TMDB_API_KEY
    if language is not None:
        if language:
            q["language"] = language
    else:
        q["language"] = config.TMDB_LANGUAGE

    url = API + path + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "Recomind/1.0"})
    last_err = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise last_err


def _extract_director(credits):
    names = [
        c.get("name") for c in (credits.get("crew") or [])
        if c.get("job") == "Director" and c.get("name")
    ]
    return " / ".join(dict.fromkeys(names)) if names else ""


def _extract_studio(detail):
    companies = detail.get("production_companies") or []
    return companies[0].get("name") if companies else ""


def _extract_genres(genres):
    names = [g.get("name") for g in (genres or []) if g.get("name")]
    return "/".join(names[:3]) if names else ""


def _extract_keywords(detail):
    kw_block = detail.get("keywords") or {}
    kws = [k.get("name") for k in (kw_block.get("keywords") or []) if k.get("name")]
    return " ".join(kws[:12])


def _extract_reviews(tmdb_id, detail):
    """优先取 detail 自带中文影评，为空时回退拉取英文影评。"""
    results = (detail.get("reviews") or {}).get("results") or []
    if not results:
        try:
            en_data = tmdb_get(f"/movie/{tmdb_id}/reviews", {"page": 1}, language="en-US", timeout=12)
            results = en_data.get("results") or []
        except Exception:  # noqa: BLE001
            results = []
    out = []
    seen = set()
    for r in results:
        content = (r.get("content") or "").strip()
        if not content or content in seen:
            continue
        seen.add(content)
        out.append({
            "author": r.get("author") or "匿名",
            "content": content[:1200],
            "rating": (r.get("author_details") or {}).get("rating") or 0,
            "created_at": (r.get("created_at") or "")[:19],
        })
        if len(out) >= 5:
            break
    return out


class TmdbService:
    """TMDB 在线片源检索与导入服务。"""

    def __init__(self):
        self.movie_service = MovieService()

    def search_online(self, query, page=1):
        """实时检索 TMDB 全网片库，返回 [Movie]（已入库返回本地记录，未入库 id=0）。"""
        query = (query or "").strip()
        if not query:
            return []
        data = tmdb_get("/search/movie", {"query": query, "page": page, "include_adult": "false"})
        results = data.get("results") or []

        tmdb_ids = [r.get("id") for r in results if r.get("id")]
        existing_map = {}
        if tmdb_ids:
            placeholders = ",".join(["%s"] * len(tmdb_ids))
            rows = execute_query(
                f"SELECT * FROM movies WHERE tmdb_id IN ({placeholders})",
                tuple(tmdb_ids),
            )
            existing_map = {r["tmdb_id"]: models.Movie.from_dict(r) for r in rows}

        movies = []
        for r in results:
            tid = r.get("id")
            if not tid:
                continue
            if tid in existing_map:
                movies.append(existing_map[tid])
                continue
            title = r.get("title") or r.get("original_title") or ""
            if not title:
                continue
            gids = r.get("genre_ids") or []
            gnames = [TMDB_GENRE_MAP[g] for g in gids if g in TMDB_GENRE_MAP]
            genre_str = "/".join(gnames[:2]) if gnames else "剧情"
            main_genre = gnames[0] if gnames else ""
            release = (r.get("release_date") or "")[:4]
            year = int(release) if release.isdigit() else 0
            poster_path = r.get("poster_path")
            movies.append(models.Movie(
                id=0,
                tmdb_id=tid,
                title=title,
                director="TMDB 在线片源",
                studio="",
                genre=genre_str,
                release_year=year,
                description=r.get("overview") or "",
                poster_color=GENRE_COLORS.get(main_genre, DEFAULT_COLOR),
                poster_url=(IMG + poster_path) if poster_path else "",
                vote_average=float(r.get("vote_average") or 0),
                vote_count=int(r.get("vote_count") or 0),
            ))
        return movies

    def fetch_bundle(self, tmdb_id):
        """拉取单部电影的详情、演职员、关键词与影评。"""
        detail = tmdb_get(
            f"/movie/{tmdb_id}",
            {"append_to_response": "credits,keywords,reviews"},
            timeout=18,
        )
        # 若中文简介缺失，回退英文简介，避免特征空洞
        overview = (detail.get("overview") or "").strip()
        if not overview:
            try:
                en = tmdb_get(f"/movie/{tmdb_id}", {}, language="en-US", timeout=12)
                overview = (en.get("overview") or "").strip()
            except Exception:  # noqa: BLE001
                pass

        genres = detail.get("genres") or []
        main_genre = genres[0].get("name") if genres else ""
        release = (detail.get("release_date") or "")[:4]
        poster_path = detail.get("poster_path")

        return {
            "tmdb_id": tmdb_id,
            "title": detail.get("title") or detail.get("original_title") or "",
            "director": _extract_director(detail.get("credits") or {}),
            "studio": _extract_studio(detail),
            "genre": _extract_genres(genres),
            "release_year": int(release) if release.isdigit() else 0,
            "description": overview,
            "poster_color": GENRE_COLORS.get(main_genre, DEFAULT_COLOR),
            "poster_url": (IMG + poster_path) if poster_path else None,
            "keywords": _extract_keywords(detail),
            "vote_average": float(detail.get("vote_average") or 0),
            "vote_count": int(detail.get("vote_count") or 0),
            "release_date": detail.get("release_date") or "",
            "reviews": _extract_reviews(tmdb_id, detail),
        }

    def upsert_bundle(self, bundle):
        """将拉取到的电影与影评增量写入/更新到 MySQL，返回 local movie_id。"""
        existing = self.movie_service.get_by_tmdb_id(bundle["tmdb_id"])
        if existing:
            execute_update(
                "UPDATE movies SET title=%s, director=%s, studio=%s, genre=%s, "
                "release_year=%s, description=%s, poster_color=%s, poster_url=%s, "
                "keywords=%s, vote_average=%s, vote_count=%s WHERE id=%s",
                (
                    bundle["title"], bundle["director"], bundle["studio"], bundle["genre"],
                    bundle["release_year"], bundle["description"], bundle["poster_color"],
                    bundle["poster_url"], bundle["keywords"], bundle["vote_average"],
                    bundle["vote_count"], existing.id,
                ),
            )
            movie_id = existing.id
        else:
            _, movie_id = execute_update(
                "INSERT INTO movies (tmdb_id, title, director, studio, genre, release_year, "
                "description, poster_color, poster_url, keywords, vote_average, vote_count) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    bundle["tmdb_id"], bundle["title"], bundle["director"], bundle["studio"],
                    bundle["genre"], bundle["release_year"], bundle["description"],
                    bundle["poster_color"], bundle["poster_url"], bundle["keywords"],
                    bundle["vote_average"], bundle["vote_count"],
                ),
            )

        if bundle.get("reviews"):
            execute_update("DELETE FROM reviews WHERE movie_id=%s", (movie_id,))
            for rv in bundle["reviews"]:
                execute_update(
                    "INSERT INTO reviews (movie_id, author, content, rating, created_at) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (movie_id, rv["author"], rv["content"], rv["rating"], rv["created_at"]),
                )
        return movie_id

    def import_movie(self, tmdb_id):
        """在线拉取单部电影并入库，返回本地 Movie 实体。"""
        existing = self.movie_service.get_by_tmdb_id(tmdb_id)
        if existing and existing.director and existing.director != "TMDB 在线片源":
            return existing
        bundle = self.fetch_bundle(tmdb_id)
        movie_id = self.upsert_bundle(bundle)
        return self.movie_service.get_movie(movie_id)