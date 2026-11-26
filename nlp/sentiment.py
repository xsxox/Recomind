# -*- coding: utf-8 -*-
"""
情感分析模块 (Sentiment Analysis)
===================================
对用户评论进行情感极性分类（正面/中性/负面），
并将情感置信度整合进推荐算法作为质量信号。

技术路线：
  1. 优先使用 SnowNLP（中文情感分析，无需 GPU）
  2. 若 SnowNLP 不可用，降级到规则词典方法

毕设亮点：
  将用户评论情感分析结果量化为情感质量分，
  与评分信号融合，能过滤"高分低口碑"的虚假评分。
"""
from __future__ import annotations

import re
from typing import Literal

from utils.logger import get_logger

logger = get_logger("nlp.sentiment")

# 正面/负面情感词词典（基础版，可扩展）
_POS_WORDS = {
    "好看", "精彩", "震撼", "感动", "经典", "惊艳", "出色", "优秀", "完美", "强烈推荐",
    "神作", "绝了", "赞", "顶", "棒", "喜欢", "爱", "值得", "惊喜", "感人",
    "精良", "高质量", "好哭", "好笑", "刺激", "过瘾", "酣畅", "深刻", "出众",
}
_NEG_WORDS = {
    "烂", "差", "无聊", "失望", "boring", "糟糕", "垃圾", "废话", "浪费", "后悔",
    "难看", "平庸", "无意义", "无聊透顶", "剧情差", "逻辑漏洞", "不推荐", "坑",
    "水分", "注水", "剪辑差", "节奏慢", "拖沓", "强行", "尴尬", "恶心",
}
_INTENSIFIERS = {"非常", "特别", "极其", "超级", "相当", "十分", "很", "太", "极"}
_NEGATIONS = {"不", "没", "未", "无", "别", "莫", "非", "否"}

SentimentLabel = Literal["positive", "neutral", "negative"]


class SentimentAnalyzer:
    """情感分析器（支持 SnowNLP 和规则降级）。"""

    def __init__(self):
        self._snownlp_available = False
        try:
            import snownlp  # type: ignore
            self._snownlp = snownlp.SnowNLP
            self._snownlp_available = True
            logger.info("情感分析后端：SnowNLP")
        except ImportError:
            logger.info("情感分析后端：规则词典")

    def score(self, text: str) -> float:
        """
        返回情感得分 [0, 1]，越高表示越正面。
        0.5 为中性分界线。
        """
        if not text or len(text.strip()) < 3:
            return 0.5
        if self._snownlp_available:
            try:
                return float(self._snownlp(text[:500]).sentiments)
            except Exception:
                pass
        return self._rule_score(text)

    def label(self, text: str) -> SentimentLabel:
        """返回情感标签：positive / neutral / negative。"""
        s = self.score(text)
        if s >= 0.65:
            return "positive"
        if s <= 0.35:
            return "negative"
        return "neutral"

    def batch_score(self, texts: list[str]) -> list[float]:
        """批量情感分析，返回得分列表。"""
        return [self.score(t) for t in texts]

    def _rule_score(self, text: str) -> float:
        """基于词典的规则情感打分。"""
        words = list(re.findall(r"[\u4e00-\u9fa5a-zA-Z]+", text.lower()))
        pos_count = 0.0
        neg_count = 0.0
        for i, w in enumerate(words):
            # 检查否定词
            negated = any(words[max(0, i-2):i].count(n) > 0 for n in _NEGATIONS)
            # 检查强调词
            intensify = 1.5 if any(words[max(0, i-1):i].count(iv) > 0 for iv in _INTENSIFIERS) else 1.0
            if w in _POS_WORDS:
                if negated:
                    neg_count += intensify
                else:
                    pos_count += intensify
            elif w in _NEG_WORDS:
                if negated:
                    pos_count += intensify * 0.5
                else:
                    neg_count += intensify
        total = pos_count + neg_count
        if total < 0.5:
            return 0.5
        return min(1.0, max(0.0, pos_count / total))

    def aggregate_comment_quality(self, comments: list[tuple[str, float]]) -> float:
        """
        聚合多条评论的情感质量分。
        comments: [(text, rating_score), ...]
        返回综合情感质量分 [0, 1]。
        """
        if not comments:
            return 0.5
        weighted_sum = 0.0
        weight_total = 0.0
        for text, rating in comments:
            sent = self.score(text)
            # 权重：评分 5 分权重最高，1 分次之（用于检测差评）
            w = 1.0 + abs(rating - 3.0) * 0.3
            weighted_sum += sent * w
            weight_total += w
        return weighted_sum / weight_total if weight_total > 0 else 0.5


# 全局单例
_analyzer: SentimentAnalyzer | None = None


def get_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
