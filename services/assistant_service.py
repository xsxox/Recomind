# -*- coding: utf-8 -*-
"""
AI 观影助手服务（多轮对话式推荐 CRS · 对话状态追踪 DST + 双模 RAG 引擎）
========================================================================
1. 对话状态追踪 (DST - Dialogue State Tracking)：
   - 支持跨轮槽位继承与修饰 (Slot Carry-over)：在多轮对话中保留上一轮的核心意图（题材、年代、参考电影等）
   - 智能识别“换一批/再推荐几个/还有吗/不喜欢这些”等换片意图，动态过滤已展示影片 (shown_ids)
   - 支持增量修饰（例如“只要90年代的”、“不要太老的”、“再加点搞笑的”）并在已有偏好基础上迭代
2. 双模驱动：
   - 本地引擎：中文 NLU + SBERT/TF-IDF 语义检索 + TMDB 贝叶斯口碑 + MMR 多样性重排
   - 在线 LLM：兼容 OpenAI / DeepSeek / 通义千问，传入对话历史与候选片单，实现真实且防幻觉推荐
"""
import json
import math
import os
import re
import urllib.error
import urllib.request

import config
from recommender.diversity import mmr_rerank
from services.recommend_service import _split_genres
from utils.logger import get_logger

logger = get_logger("services.assistant")

LLM_CONFIG_PATH = os.path.join(config.DATA_DIR, "llm_config.json")

DEFAULT_LLM_CONFIG = {
    "enabled": False,
    "provider": "DeepSeek",
    "api_base": "https://api.deepseek.com/v1",
    "api_key": "",
    "model": "deepseek-chat",
}

LLM_PRESETS = {
    "DeepSeek": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "通义千问 (DashScope)": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "硅基流动 (SiliconFlow)": ("https://api.siliconflow.cn/v1", "Qwen/Qwen2.5-7B-Instruct"),
    "OpenAI": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "自定义 (OpenAI 兼容)": ("", ""),
}

ALL_KNOWN_GENRES = [
    "科幻", "动作", "剧情", "喜剧", "动画", "悬疑", "犯罪", "爱情",
    "历史", "战争", "奇幻", "惊悚", "冒险", "家庭", "音乐", "恐怖", "纪录", "西部",
]

# 口语/情绪/主题词到标准电影类型的映射
GENRE_SYNONYMS = {
    "科幻": ["科幻", "太空", "宇宙", "外星", "未来", "赛博", "机器人", "人工智能", "星际", "穿越", "末世"],
    "动作": ["动作", "打斗", "枪战", "谍战", "特工", "武打", "功夫", "飙车", "爆米花", "爽片", "热血"],
    "剧情": ["剧情", "现实", "人生", "人性", "文艺", "催泪", "感人", "深度", "传记"],
    "喜剧": ["喜剧", "搞笑", "幽默", "轻松", "开心", "爆笑", "欢乐", "解压", "逗趣"],
    "动画": ["动画", "动漫", "卡通", "二次元", "皮克斯", "宫崎骏", "吉卜力"],
    "悬疑": ["悬疑", "烧脑", "反转", "推理", "破案", "侦探", "谜案", "解密", "脑洞"],
    "犯罪": ["犯罪", "黑帮", "警匪", "卧底", "罪案", "越狱", "抢劫", "复仇"],
    "爱情": ["爱情", "浪漫", "恋爱", "情侣", "虐恋", "青春", "暗恋", "甜宠"],
    "历史": ["历史", "古代", "古装", "朝代", "一战", "二战", "年代感"],
    "战争": ["战争", "战场", "军事", "士兵", "抗战"],
    "奇幻": ["奇幻", "魔幻", "魔法", "巫师", "神话", "奇遇"],
    "惊悚": ["惊悚", "紧张", "刺激", "心理战", "密室"],
    "冒险": ["冒险", "探险", "寻宝", "荒野", "求生", "奇观"],
    "家庭": ["家庭", "亲情", "亲子", "合家欢", "治愈", "温暖", "成长"],
    "音乐": ["音乐", "歌舞", "乐队", "钢琴", "摇滚"],
    "恐怖": ["恐怖", "吓人", "鬼片", "灵异", "丧尸"],
    "纪录": ["纪录", "记录", "真实事件"],
}

CHINESE_NUMS = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

# “换一批”典型口语匹配正则
REFRESH_PATTERNS = [
    r"换一批", r"换一组", r"换换", r"再来几个", r"再来一部", r"再来点", r"还有吗",
    r"还有没有", r"再推荐", r"下一批", r"换个别的", r"看不中", r"不太喜欢这些",
    r"别的呢", r"换电影", r"重新推荐"
]


def load_llm_config():
    cfg = dict(DEFAULT_LLM_CONFIG)
    if os.path.exists(LLM_CONFIG_PATH):
        try:
            with open(LLM_CONFIG_PATH, encoding="utf-8") as fp:
                data = json.load(fp)
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:  # noqa: BLE001
            pass
    return cfg


def save_llm_config(cfg):
    os.makedirs(os.path.dirname(LLM_CONFIG_PATH), exist_ok=True)
    merged = dict(DEFAULT_LLM_CONFIG)
    merged.update(cfg or {})
    with open(LLM_CONFIG_PATH, "w", encoding="utf-8") as fp:
        json.dump(merged, fp, ensure_ascii=False, indent=2)
    return merged


def _post_chat_completion(cfg, messages, timeout=30):
    """使用标准库 urllib 调用 OpenAI 兼容 /chat/completions 接口。"""
    base = (cfg.get("api_base") or "").strip().rstrip("/")
    key = (cfg.get("api_key") or "").strip()
    model = (cfg.get("model") or "").strip()
    if not base or not key or not model:
        raise ValueError("请完整填写 API Base、API Key 和模型名称")

    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 900,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Recomind/2.2",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:200]}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("接口未返回 choices 内容")
    return (choices[0].get("message") or {}).get("content") or ""


def test_llm_connection(cfg):
    """测试在线模型连通性，返回 (是否成功, 提示信息)。"""
    try:
        reply = _post_chat_completion(
            cfg,
            [{"role": "user", "content": "请仅回复：连接成功"}],
            timeout=15,
        )
        return True, f"连接成功！模型回复：{reply.strip()[:60]}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


class AssistantService:
    """AI 观影助手业务逻辑（支持多轮上下文与 DST 槽位追踪）。"""

    def __init__(self, recommend_service):
        self.recommend_service = recommend_service
        # 会话状态管理
        self.last_intent = None        # 上一轮意图对象
        self.shown_movie_ids = set()   # 对话中已展示过的电影ID，避免重复
        self.dialogue_history = []     # 对话历史 [{"role": "user"/"assistant", "content": ...}]

    def reset_session(self):
        """清空会话状态。"""
        self.last_intent = None
        self.shown_movie_ids.clear()
        self.dialogue_history.clear()
        logger.info("AI 助手会话状态已重置")

    # ---------- 1. 多轮自然语言意图解析 (NLU + DST) ----------

    def parse_intent(self, query, movies):
        q = (query or "").strip()
        q_lower = q.lower()

        # 检查是否为“换一批”意图
        is_refresh = any(re.search(pat, q) for pat in REFRESH_PATTERNS)

        # 推荐条数（默认 5 部）
        top_n = 5
        m_num = re.search(r"(\d+)\s*[部个条套]", q)
        if m_num:
            top_n = max(1, min(12, int(m_num.group(1))))
        else:
            m_cn = re.search(r"([一两二三四五六七八九十])\s*[部个条套]", q)
            if m_cn and m_cn.group(1) in CHINESE_NUMS:
                top_n = CHINESE_NUMS[m_cn.group(1)]

        # 否定过滤（例如“不要恐怖/别太血腥”）
        excluded = set()
        for neg_seg in re.findall(r"(?:不要|别|不想看|不喜欢|排除|别推荐)([^，。,.！？!?\n]{1,14})", q):
            for genre, words in GENRE_SYNONYMS.items():
                if any(w in neg_seg for w in words):
                    excluded.add(genre)

        # 目标类型与情绪映射
        preferred = set()
        for genre, words in GENRE_SYNONYMS.items():
            if genre in excluded:
                continue
            if any(w in q_lower for w in words):
                preferred.add(genre)

        # 年代意图
        year_min, year_max = None, None
        era_label = ""
        m_decade = re.search(r"(80|90|00|10)\s*年代", q)
        if m_decade:
            d = int(m_decade.group(1))
            start = 1900 + d if d >= 50 else 2000 + d
            year_min, year_max = start, start + 9
            era_label = f"{m_decade.group(1)}年代"
        elif any(k in q for k in ("老电影", "老片", "怀旧")):
            year_max = 2012
            era_label = "经典老片"
        elif any(k in q for k in ("新片", "最近", "最新", "近几年", "不要太老", "别太老")):
            year_min = 2019
            era_label = "近年新片"
        elif "经典" in q:
            year_max = 2018
            era_label = "经典佳作"

        prefer_classic = "经典" in q
        prefer_high_rating = prefer_classic or any(
            k in q for k in ("高分", "神作", "口碑", "佳作", "必看", "好看", "推荐", "精品")
        )

        # 匹配句子中提到的参考片名（如“类似星际穿越”）
        ref_movie = None
        best_len = 0
        for mv in movies:
            t = (mv.title or "").strip()
            if len(t) >= 2 and t in q and len(t) > best_len:
                ref_movie = mv
                best_len = len(t)

        # 清洗停用词/提问助词，提炼核心语义文本
        cleaned = re.sub(
            r"(换一批|换一组|换换|再来几个|还有吗|再推荐|我想看|想看|帮我推荐|给我推荐|推荐|来几部|来\d+部|有没有|一部|几部|电影|影片|片子|的|一个|那种|适合|喜欢)",
            " ",
            q,
        ).strip()

        # ====== DST 核心逻辑：多轮上下文槽位继承与修饰 (Slot Carry-over) ======
        prev = self.last_intent
        is_carry_over = False

        if is_refresh and prev:
            # “换一批”模式：完整继承上一轮全部检索约束与语义
            preferred = set(prev.get("preferred") or set())
            excluded = set(prev.get("excluded") or set()) | excluded
            year_min = year_min or prev.get("year_min")
            year_max = year_max or prev.get("year_max")
            era_label = era_label or prev.get("era_label", "")
            prefer_classic = prefer_classic or prev.get("prefer_classic", False)
            prefer_high_rating = prefer_high_rating or prev.get("prefer_high_rating", False)
            ref_movie = ref_movie or prev.get("ref_movie")
            cleaned = prev.get("cleaned") or cleaned
            is_carry_over = True
            logger.info("DST: 识别为【换一批】意图，继承上一轮意图: %s", prev.get("tags"))

        elif prev and not preferred and not ref_movie:
            # 增量修饰模式：用户没说新类型，而是补充条件（如“只要高分的”、“不要恐怖的”、“90年代的”）
            if excluded or year_min or year_max or prefer_high_rating or len(cleaned) <= 6:
                preferred = set(prev.get("preferred") or set())
                excluded = set(prev.get("excluded") or set()) | excluded
                if not year_min and not year_max:
                    year_min = prev.get("year_min")
                    year_max = prev.get("year_max")
                    era_label = era_label or prev.get("era_label", "")
                prefer_classic = prefer_classic or prev.get("prefer_classic", False)
                prefer_high_rating = prefer_high_rating or prev.get("prefer_high_rating", False)
                ref_movie = ref_movie or prev.get("ref_movie")
                if not cleaned or len(cleaned) <= 4:
                    cleaned = prev.get("cleaned", cleaned)
                is_carry_over = True
                logger.info("DST: 识别为【增量修饰】意图，继承并融合上一轮意图")

        tags = []
        if is_refresh:
            tags.append("模式: 换一批")
        elif is_carry_over:
            tags.append("模式: 延续上下文")
        if preferred:
            tags.append("题材: " + "/".join(sorted(preferred)))
        if era_label:
            tags.append(f"年代: {era_label}")
        if prefer_high_rating:
            tags.append("口碑: 高分精选")
        if ref_movie:
            tags.append(f"参考: 《{ref_movie.title}》")
        if excluded:
            tags.append("排除: " + "/".join(sorted(excluded)))
        tags.append(f"数量: {top_n} 部")

        current_intent = {
            "raw": q,
            "cleaned": cleaned or q,
            "top_n": top_n,
            "preferred": preferred,
            "excluded": excluded,
            "year_min": year_min,
            "year_max": year_max,
            "era_label": era_label,
            "prefer_classic": prefer_classic,
            "prefer_high_rating": prefer_high_rating,
            "ref_movie": ref_movie,
            "tags": tags,
            "is_refresh": is_refresh,
            "is_carry_over": is_carry_over,
        }
        return current_intent

    # ---------- 2. RAG 候选检索与排序（支持已展示过滤） ----------

    def retrieve_candidates(self, intent, user_id=None, pool_size=15, exclude_ids=None):
        movies, _ = self.recommend_service._build_models()
        if not movies:
            return []

        content_model = self.recommend_service.content
        quality_map = self.recommend_service._tmdb_quality
        exclude_pool = set(exclude_ids or set())

        # 语义向量/文本相关性检索
        text_sims = {}
        for m, s in content_model.recommend_by_text(intent["cleaned"], top_n=150):
            text_sims[m.id] = s
        if intent["raw"] != intent["cleaned"]:
            for m, s in content_model.recommend_by_text(intent["raw"], top_n=150):
                text_sims[m.id] = max(text_sims.get(m.id, 0.0), s)

        # 参考电影相似检索
        ref_sims = {}
        if intent["ref_movie"] is not None:
            for m, s in content_model.recommend_by_movie(intent["ref_movie"].id, top_n=100):
                ref_sims[m.id] = s

        # 用户个人先验
        user_rated = set()
        if user_id:
            user_rated = {r.movie_id for r in self.recommend_service.rating_service.get_user_ratings(user_id)}

        def score_pool(strict_era=True, skip_shown=True):
            scored = []
            for m in movies:
                if intent["ref_movie"] and m.id == intent["ref_movie"].id:
                    continue
                # 过滤当前对话已推荐过的电影
                if skip_shown and m.id in exclude_pool:
                    continue
                m_genres = _split_genres(m.genre)
                if intent["excluded"] and (m_genres & intent["excluded"]):
                    continue

                y = m.release_year or 0
                if strict_era:
                    if intent["year_min"] and (y == 0 or y < intent["year_min"]):
                        continue
                    if intent["year_max"] and (y == 0 or y > intent["year_max"]):
                        continue

                genre_score = 0.0
                if intent["preferred"]:
                    overlap = len(m_genres & intent["preferred"])
                    if overlap == 0 and m.id not in text_sims and m.id not in ref_sims:
                        continue
                    genre_score = overlap / len(intent["preferred"])

                sem_score = max(text_sims.get(m.id, 0.0), ref_sims.get(m.id, 0.0))
                if not intent["preferred"] and not intent["ref_movie"] and sem_score <= 0 and not intent["prefer_high_rating"]:
                    continue

                q_score = quality_map.get(m.id, 0.65)
                pop_bonus = min(1.0, math.log10((m.vote_count or 0) + 10) / 4.5) if intent["prefer_classic"] else 0.0

                if intent["preferred"]:
                    total = 0.45 * genre_score + 0.25 * min(1.0, sem_score * 1.8) + 0.22 * q_score + 0.08 * pop_bonus
                elif intent["ref_movie"]:
                    total = 0.62 * min(1.0, ref_sims.get(m.id, 0.0) * 1.6) + 0.20 * min(1.0, sem_score * 1.5) + 0.18 * q_score
                else:
                    total = 0.55 * min(1.0, sem_score * 1.8) + 0.35 * q_score + 0.10 * pop_bonus

                if m.id not in user_rated:
                    total += 0.03

                scored.append((m, round(min(1.0, total), 4)))
            scored.sort(key=lambda kv: kv[1], reverse=True)
            return scored

        candidates = score_pool(strict_era=True, skip_shown=True)

        # 若排除已展示影片后数量不足，放宽年代限制
        if len(candidates) < intent["top_n"] and (intent["year_min"] or intent["year_max"]):
            seen_ids = {m.id for m, _ in candidates}
            for m, s in score_pool(strict_era=False, skip_shown=True):
                if m.id not in seen_ids:
                    candidates.append((m, round(s * 0.9, 4)))
                    seen_ids.add(m.id)

        # 如果整个库内该类影片几乎全部被展示过了，才回滚允许历史影片再次进入备选池
        if len(candidates) < intent["top_n"]:
            logger.info("未展示候选不足，放宽已展示过滤池")
            seen_ids = {m.id for m, _ in candidates}
            for m, s in score_pool(strict_era=False, skip_shown=False):
                if m.id not in seen_ids:
                    candidates.append((m, round(s * 0.8, 4)))
                    seen_ids.add(m.id)

        if not candidates:
            return []

        # 使用 MMR 进行多样性打散
        return mmr_rerank(
            candidates[:80],
            similarity_fn=content_model.pairwise_similarity,
            lambda_param=0.72,
            top_n=max(pool_size, intent["top_n"]),
        )

    # ---------- 3. 本地自然语言回复生成 (NLG) ----------

    def _local_reason(self, movie, intent):
        parts = []
        m_genres = _split_genres(movie.genre)
        hit = m_genres & intent["preferred"]
        if hit:
            parts.append(f"契合「{'/'.join(sorted(hit))}」题材")
        elif intent["ref_movie"]:
            parts.append(f"与《{intent['ref_movie'].title}》风格相近")
        if intent["prefer_classic"] and movie.release_year and movie.release_year <= 2018:
            parts.append(f"{movie.release_year}年经典佳片")
        elif movie.release_year:
            parts.append(f"{movie.release_year}年上映")
        if movie.vote_average and movie.vote_average >= 7.5:
            parts.append(f"TMDB评分 {movie.vote_average:.1f}")
        elif movie.vote_average:
            parts.append(f"评分 {movie.vote_average:.1f}")
        overview = (movie.description or "").strip()
        if overview:
            snippet = overview[:50] + ("…" if len(overview) > 50 else "")
            parts.append(f"看点：{snippet}")
        return "；".join(parts)

    def _build_local_reply(self, intent, picked):
        if not picked:
            return (
                "抱歉，在当前偏好与已推荐过滤下，没有找到更多契合的电影。\n"
                "你可以尝试输入新的题材偏好（如「悬疑烧脑」、「轻松喜剧」），或者点击右上角「清空对话」重新开始。"
            )
        prefix = "好的，已为你换一批契合的片单：\n" if intent.get("is_refresh") else f"已结合上下文为你精选了 {len(picked)} 部电影：\n"
        lines = [prefix]
        for idx, (m, _s) in enumerate(picked, 1):
            lines.append(f"{idx}. 《{m.title}》 — {self._local_reason(m, intent)}")
        lines.append("\n点击下方电影海报可直接查看详情；随时告诉我「换一批」或继续补充条件！")
        return "\n".join(lines)

    # ---------- 4. 在线 LLM 精排与生成（结合多轮对话上下文） ----------

    def _ask_online_llm(self, cfg, query, intent, candidates):
        cand_lines = []
        cand_map = {}
        for m, s in candidates[:12]:
            cand_map[m.id] = (m, s)
            desc = (m.description or "").replace("\n", " ")[:120]
            cand_lines.append(
                f"- id:{m.id} | 片名:《{m.title}》 | 年份:{m.release_year or '未知'} | "
                f"类型:{m.genre or '未知'} | 导演:{m.director or '未知'} | "
                f"TMDB评分:{m.vote_average:.1f} | 简介:{desc}"
            )

        sys_prompt = (
            "你是 Recomind 智能电影推荐系统的专业 AI 观影伴侣。\n"
            "【核心规则】\n"
            "1. 你必须严格从给定的【候选电影列表】中挑选电影，绝对不得编造或推荐列表之外的任何电影；\n"
            "2. 理解用户的连续多轮对话上下文（例如用户说‘换一批’时，理解用户依然想要上一轮类型的电影）；\n"
            f"3. 挑选出最符合要求的 {intent['top_n']} 部电影，并严格返回以下 JSON 格式（不要添加额外文字）：\n"
            '{"analysis":"一句话分析用户需求或换片诉求","picks":[{"id":电影数字ID,"reason":"生动自然的个性化推荐理由（30~60字）"}],"closing":"一句简短结语"}'
        )

        # 组装带历史对话的 messages 列表
        messages = [{"role": "system", "content": sys_prompt}]
        for hist in self.dialogue_history[-4:]:
            messages.append({"role": hist["role"], "content": hist["content"]})

        user_content = (
            f"用户最新发言：{query}\n"
            f"【候选电影列表（已排除历史推荐）】：\n" + "\n".join(cand_lines)
        )
        messages.append({"role": "user", "content": user_content})

        raw_text = _post_chat_completion(cfg, messages)

        m_json = re.search(r"\{[\s\S]*\}", raw_text)
        if not m_json:
            raise ValueError("模型未返回有效 JSON 格式")
        parsed = json.loads(m_json.group(0))

        picked = []
        used_ids = set()
        reason_lines = []
        analysis = (parsed.get("analysis") or "").strip()
        if analysis:
            reason_lines.append(analysis + "\n")

        for item in (parsed.get("picks") or []):
            try:
                mid = int(item.get("id"))
            except Exception:  # noqa: BLE001
                continue
            if mid in cand_map and mid not in used_ids:
                used_ids.add(mid)
                mv, sc = cand_map[mid]
                picked.append((mv, sc))
                reason = (item.get("reason") or "").strip() or self._local_reason(mv, intent)
                reason_lines.append(f"{len(picked)}. 《{mv.title}》 — {reason}")
                if len(picked) >= intent["top_n"]:
                    break

        for mv, sc in candidates:
            if len(picked) >= intent["top_n"]:
                break
            if mv.id not in used_ids:
                used_ids.add(mv.id)
                picked.append((mv, sc))
                reason_lines.append(f"{len(picked)}. 《{mv.title}》 — {self._local_reason(mv, intent)}")

        closing = (parsed.get("closing") or "").strip()
        if closing:
            reason_lines.append("\n" + closing)
        return "\n".join(reason_lines), picked

    # ---------- 5. 对外统一入口 ----------

    def chat(self, query, user_id=None):
        """处理用户的自然语言推荐请求，支持多轮状态继承。"""
        movies, _ = self.recommend_service._build_models()
        intent = self.parse_intent(query, movies)

        # 召回候选电影（排查当前会话已展示过的电影）
        candidates = self.retrieve_candidates(
            intent, user_id=user_id, pool_size=15, exclude_ids=self.shown_movie_ids
        )

        cfg = load_llm_config()
        if cfg.get("enabled") and (cfg.get("api_key") or "").strip() and candidates:
            try:
                reply, picked = self._ask_online_llm(cfg, query, intent, candidates)
                # 记录状态
                self._update_session_state(query, reply, intent, picked)
                return {
                    "reply": reply,
                    "intent_tags": intent["tags"],
                    "movies": picked,
                    "mode": "llm",
                    "model_name": cfg.get("model") or "在线 LLM",
                }
            except Exception as exc:  # noqa: BLE001
                logger.warning("在线 LLM 调用失败，自动降级本地引擎: %s", exc)
                picked = candidates[:intent["top_n"]]
                fallback_reply = (
                    f"⚠️ 在线大模型暂不可用（{exc}），已自动切换本地 NLP 引擎为您推荐：\n\n"
                    + self._build_local_reply(intent, picked)
                )
                self._update_session_state(query, fallback_reply, intent, picked)
                return {
                    "reply": fallback_reply,
                    "intent_tags": intent["tags"],
                    "movies": picked,
                    "mode": "local",
                    "model_name": "本地 NLP+RAG 引擎（已降级）",
                }

        picked = candidates[:intent["top_n"]]
        reply = self._build_local_reply(intent, picked)
        self._update_session_state(query, reply, intent, picked)
        return {
            "reply": reply,
            "intent_tags": intent["tags"],
            "movies": picked,
            "mode": "local",
            "model_name": "本地 NLP+RAG 引擎",
        }

    def _update_session_state(self, query, reply, intent, picked):
        """更新会话上下文与已展示集合。"""
        self.last_intent = intent
        for m, _ in picked:
            self.shown_movie_ids.add(m.id)
        self.dialogue_history.append({"role": "user", "content": query})
        self.dialogue_history.append({"role": "assistant", "content": reply})
        if len(self.dialogue_history) > 10:
            self.dialogue_history = self.dialogue_history[-10:]
