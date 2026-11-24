# -*- coding: utf-8 -*-
"""
在线海报异步加载器
使用 QNetworkAccessManager 异步下载海报图，带内存与磁盘缓存；
下载失败或离线时返回 None，由调用方回落到绘制海报。
"""
import hashlib
import os

from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

import config

_CACHE_DIR = os.path.join(config.DATA_DIR, "posters")


class PosterLoader(QObject):
    """异步海报图加载器。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._pixmaps = {}
        self._callbacks = {}
        self._replies = {}

    def load(self, url, callback):
        """请求海报图：命中缓存立即回调，否则异步下载后回调（失败回调 None）。"""
        if not url:
            return
        if url in self._pixmaps:
            self._safe_call(callback, self._pixmaps[url])
            return

        cached = self._load_disk(url)
        if cached is not None:
            self._pixmaps[url] = cached
            self._safe_call(callback, cached)
            return

        pending = self._callbacks.setdefault(url, [])
        pending.append(callback)
        if len(pending) > 1:
            return  # 该地址正在下载，复用同一个请求

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
        reply = self._manager.get(request)
        self._replies[url] = reply  # 保持强引用，避免 reply 被回收导致信号断开
        reply.finished.connect(lambda r=reply, u=url: self._on_finished(u, r))

    def _on_finished(self, url, reply):
        self._replies.pop(url, None)
        callbacks = self._callbacks.pop(url, [])
        pixmap = None
        try:
            if reply.error() == QNetworkReply.NoError:
                candidate = QPixmap()
                if candidate.loadFromData(reply.readAll()) and not candidate.isNull():
                    pixmap = candidate
                    self._pixmaps[url] = pixmap
                    self._save_disk(url, pixmap)
        finally:
            reply.deleteLater()
        for callback in callbacks:
            self._safe_call(callback, pixmap)

    @staticmethod
    def _safe_call(callback, pixmap):
        try:
            callback(pixmap)
        except RuntimeError:
            pass  # 目标控件已销毁

    def _disk_path(self, url):
        try:
            os.makedirs(_CACHE_DIR, exist_ok=True)
        except Exception:  # noqa: BLE001
            return None
        return os.path.join(
            _CACHE_DIR, hashlib.md5(url.encode("utf-8")).hexdigest() + ".png"
        )

    def _load_disk(self, url):
        path = self._disk_path(url)
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                return pixmap
        return None

    def _save_disk(self, url, pixmap):
        path = self._disk_path(url)
        if path:
            try:
                pixmap.save(path, "PNG")
            except Exception:  # noqa: BLE001
                pass


_loader = None


def get_loader():
    """获取全局海报加载器。"""
    global _loader
    if _loader is None:
        _loader = PosterLoader()
    return _loader
