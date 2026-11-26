# -*- coding: utf-8 -*-
"""
影片库页面
全屏无边框 2:3 海报墙 + 分批流畅加载 + 实时「搜全网 TMDB」自动入库。
"""
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

from services.tmdb_service import TmdbService
from ui.widgets import FlowContainer, MovieCard, make_icon, populate_grid
from utils.logger import get_logger

logger = get_logger("ui.search")

PAGE_BATCH_SIZE = 48


class OnlineSearchWorker(QThread):
    """后台在线搜索 TMDB 线程。"""
    finished_ok = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, tmdb_service, keyword, parent=None):
        super().__init__(parent)
        self.tmdb_service = tmdb_service
        self.keyword = keyword

    def run(self):
        try:
            self.finished_ok.emit(self.tmdb_service.search_online(self.keyword))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class SearchPage(QWidget):
    """影片库浏览与全网检索页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.tmdb_service = TmdbService()
        self._worker = None
        self._all_movies = []
        self._shown_count = 0
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 26, 36, 20)
        root.setSpacing(18)

        # 顶栏
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("影片库")
        title.setObjectName("pageTitle")
        subtitle = QLabel("浏览本地全题材片库，或输入片名点击「搜全网 TMDB」在线入库任意电影")
        subtitle.setObjectName("subText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch()

        self.count_label = QLabel("共 0 部")
        self.count_label.setObjectName("scoreBadge")
        top.addWidget(self.count_label)
        root.addLayout(top)

        # 暗色检索条
        bar = QFrame()
        bar.setObjectName("spotlightBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 6, 8, 6)
        bar_layout.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(make_icon("search", "#94A3B8", 18).pixmap(18, 18))
        bar_layout.addWidget(icon)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("spotlightInput")
        self.search_input.setMinimumHeight(38)
        self.search_input.setPlaceholderText("搜索片名、导演或关键词...")
        self.search_input.returnPressed.connect(self.refresh)
        bar_layout.addWidget(self.search_input, 1)

        self.genre_combo = QComboBox()
        self.genre_combo.setMinimumWidth(140)
        self.genre_combo.setMinimumHeight(38)
        self.genre_combo.currentIndexChanged.connect(lambda _i: self.refresh())
        bar_layout.addWidget(self.genre_combo)

        self.search_btn = QPushButton("搜本地")
        self.search_btn.setMinimumHeight(38)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self.refresh)
        bar_layout.addWidget(self.search_btn)

        self.online_btn = QPushButton("搜全网 TMDB")
        self.online_btn.setObjectName("secondaryBtn")
        self.online_btn.setMinimumHeight(38)
        self.online_btn.setCursor(Qt.PointingHandCursor)
        self.online_btn.clicked.connect(self.search_online)
        bar_layout.addWidget(self.online_btn)
        root.addWidget(bar)

        # 海报墙
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        scroll_body = QWidget()
        scroll_body.setObjectName("searchScrollBody")
        scroll_body.setStyleSheet("QWidget#searchScrollBody { background: transparent; }")
        body_layout = QVBoxLayout(scroll_body)
        body_layout.setContentsMargins(0, 4, 4, 16)
        body_layout.setSpacing(20)

        self.container = FlowContainer(h_spacing=22, v_spacing=24, margin=0)
        self.grid = self.container.flow
        body_layout.addWidget(self.container)

        self.load_more_btn = QPushButton("加载更多")
        self.load_more_btn.setObjectName("secondaryBtn")
        self.load_more_btn.setMinimumHeight(42)
        self.load_more_btn.setMinimumWidth(220)
        self.load_more_btn.setCursor(Qt.PointingHandCursor)
        self.load_more_btn.clicked.connect(lambda: self._append_batch(PAGE_BATCH_SIZE))
        self.load_more_btn.hide()
        body_layout.addWidget(self.load_more_btn, 0, Qt.AlignCenter)
        body_layout.addStretch()

        self.scroll.setWidget(scroll_body)
        root.addWidget(self.scroll, 1)

    def refresh(self):
        self._reload_categories()
        keyword = self.search_input.text().strip()
        genre = self.genre_combo.currentText()

        try:
            movies = self.main.movie_service.search_movies(keyword)
        except Exception:  # noqa: BLE001
            logger.exception("搜索电影失败")
            return

        if genre and genre != "全部类型":
            movies = [b for b in movies if genre in (b.genre or "")]

        self.count_label.setText(f"本地共 {len(movies)} 部")
        self._all_movies = movies
        self._shown_count = 0
        populate_grid(self.grid, [])

        if not movies:
            self.load_more_btn.hide()
            msg = QLabel("本地片库暂无匹配结果，点击右上「搜全网 TMDB」可直接在线检索并入库。")
            msg.setObjectName("cardInfo")
            self.grid.addWidget(msg)
            return

        self._append_batch(PAGE_BATCH_SIZE)

    def _append_batch(self, batch_size):
        end = min(len(self._all_movies), self._shown_count + batch_size)
        chunk = self._all_movies[self._shown_count:end]
        if not chunk:
            self.load_more_btn.hide()
            return

        self.container.setUpdatesEnabled(False)
        for movie in chunk:
            card = MovieCard(movie)
            card.clicked.connect(self._on_card_clicked)
            self.grid.addWidget(card)
        self.container.setUpdatesEnabled(True)

        self._shown_count = end
        remaining = len(self._all_movies) - self._shown_count
        if remaining > 0:
            self.load_more_btn.setText(f"加载更多（还有 {remaining} 部）")
            self.load_more_btn.show()
        else:
            self.load_more_btn.hide()

    def search_online(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.information(self, "提示", "请先输入片名再检索 TMDB 全网片库")
            return

        self.online_btn.setEnabled(False)
        self.online_btn.setText("检索中…")
        self.count_label.setText("正在检索 TMDB 全网…")
        self.load_more_btn.hide()
        populate_grid(self.grid, [])
        loading = QLabel(f"正在连接 TMDB 搜索“{keyword}”…")
        loading.setObjectName("cardInfo")
        self.grid.addWidget(loading)

        self._worker = OnlineSearchWorker(self.tmdb_service, keyword, self)
        self._worker.finished_ok.connect(self._on_online_results)
        self._worker.failed.connect(self._on_online_failed)
        self._worker.start()

    def _on_online_results(self, movies):
        self.online_btn.setEnabled(True)
        self.online_btn.setText("搜全网 TMDB")
        self.count_label.setText(f"全网命中 {len(movies)} 部（点击入库）")
        self._all_movies = movies
        self._shown_count = 0
        populate_grid(self.grid, [])

        if not movies:
            self.load_more_btn.hide()
            empty = QLabel("TMDB 全网未找到相关电影，请尝试更换片名（支持英文原名）。")
            empty.setObjectName("cardInfo")
            self.grid.addWidget(empty)
            return

        self._append_batch(PAGE_BATCH_SIZE)

    def _on_online_failed(self, err):
        self.online_btn.setEnabled(True)
        self.online_btn.setText("搜全网 TMDB")
        self.count_label.setText("在线检索失败")
        QMessageBox.warning(self, "在线检索失败", f"无法连接 TMDB：{err}")

    def _on_card_clicked(self, movie):
        if movie.id == 0 and movie.tmdb_id:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                saved = self.tmdb_service.import_movie(movie.tmdb_id)
                self.main.recommend_service.invalidate_cache()
            except Exception as exc:  # noqa: BLE001
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "入库失败", f"拉取电影详情失败：{exc}")
                return
            QApplication.restoreOverrideCursor()
            self._reload_categories()
            self.main.open_detail(saved)
            return
        self.main.open_detail(movie)

    def _reload_categories(self):
        current = self.genre_combo.currentText()
        try:
            movies = self.main.movie_service.list_movies()
        except Exception:  # noqa: BLE001
            movies = []
        categories = sorted({
            g.strip()
            for b in movies if b.genre
            for g in b.genre.split("/") if g.strip()
        })
        items = ["全部类型"] + categories
        self.genre_combo.blockSignals(True)
        self.genre_combo.clear()
        self.genre_combo.addItems(items)
        if current in items:
            self.genre_combo.setCurrentText(current)
        self.genre_combo.blockSignals(False)