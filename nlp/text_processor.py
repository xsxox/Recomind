# -*- coding: utf-8 -*-
"""
中文文本预处理模块
提供文本清洗、jieba 分词、停用词过滤等功能，为 TF-IDF 特征提取做准备。
"""
import os
import re

import jieba

import config

# 停用词集合（惰性加载 + 内存缓存）
_stopwords = None

# 内置基础停用词，与 data/stopwords.txt 合并使用
_BUILTIN_STOPWORDS = {
    "的", "了", "和", "是", "在", "就", "都", "而", "及", "与", "着", "或",
    "一个", "没有", "我们", "你们", "他们", "它们", "这个", "那个", "这些",
    "那些", "自己", "什么", "可以", "非常", "比较", "但是", "因为", "所以",
    "如果", "虽然", "然而", "而且", "因此", "对于", "关于", "通过", "作为",
    "进行", "已经", "以及", "等", "等等", "之一", "一种", "本书", "本书", "内容",
}


def load_stopwords():
    """加载停用词表（合并内置词与文件中的词）。"""
    global _stopwords
    if _stopwords is not None:
        return _stopwords

    _stopwords = set(_BUILTIN_STOPWORDS)
    if os.path.exists(config.STOPWORDS_FILE):
        try:
            with open(config.STOPWORDS_FILE, encoding="utf-8") as fp:
                for line in fp:
                    word = line.strip()
                    if word:
                        _stopwords.add(word)
        except Exception:  # noqa: BLE001
            pass
    return _stopwords


def clean_text(text):
    """清洗文本：统一小写、去除数字与标点符号，仅保留中英文。"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[0-9]+", " ", text)
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z]+", " ", text)
    return " ".join(text.split())


def tokenize(text, remove_stopwords=True):
    """对文本进行分词，返回词语列表。"""
    text = clean_text(text)
    if not text:
        return []
    words = [w.strip() for w in jieba.lcut(text) if w.strip()]
    if remove_stopwords:
        stop = load_stopwords()
        words = [w for w in words if w not in stop and len(w) > 1]
    return words


def segment(text):
    """对文本分词并用空格连接，供 TfidfVectorizer 使用。"""
    return " ".join(tokenize(text))
