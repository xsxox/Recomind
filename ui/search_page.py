# -*- coding: utf-8 -*-
"""
电影浏览 / 搜索页
支持关键词检索、类型筛选与自适应流式影片墙展示。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ui.widgets import (MovieCard, FlowContainer, apply_shadow, make_icon,
                        populate_grid)
from utils.logger import get_logger

logger = get_logger("ui.search")


class SearchPage(QWidget):
    """电影浏览与搜索页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 20)
        root.setSpacing(18)

        # 标题行
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("影片库")
        title.setObjectName("pageTitle")
        subtitle = QLabel("按片名、导演或关键词快速检索全部电影，点击海报即可查看详情与评分")
        subtitle.setObjectName("subText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch()

        self.count_label = QLabel("共 0 本")
        self.count_label.setStyleSheet(
            "background-color: #EEF2FF; color: #4F46E5; border-radius: 10px;"
            "padding: 8px 14px; font-size: 13px; font-weight: bold;"
        )
        top.addWidget(self.count_label)
        root.addLayout(top)

        # 检索工具栏
        bar = QFrame()
        bar.setObjectName("spotlightBar")
        apply_shadow(bar, blur=20, y_offset=4, alpha=12)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 8, 10, 8)
        bar_layout.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(make_icon("search", "#6B7280", 19).pixmap(19, 19))
        bar_layout.addWidget(icon)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("spotlightInput")
        self.search_input.setMinimumHeight(40)
        self.search_input.setPlaceholderText("搜索片名、导演或内容关键词...")
        self.search_input.returnPressed.connect(self.refresh)
        bar_layout.addWidget(self.search_input, 1)

        self.genre_combo = QComboBox()
        self.genre_combo.setMinimumWidth(140)
        self.genre_combo.setMinimumHeight(40)
        self.genre_combo.currentIndexChanged.connect(lambda _i: self.refresh())
        bar_layout.addWidget(self.genre_combo)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumHeight(40)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self.refresh)
        bar_layout.addWidget(self.search_btn)

        root.addWidget(bar)

        # 流式网格
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = FlowContainer(h_spacing=18, v_spacing=20)
        self.grid = self.container.flow
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

    def refresh(self):
        """刷新电影列表（应用搜索词与类型筛选）。"""
        self._reload_categories()
        keyword = self.search_input.text().strip()
        genre = self.genre_combo.currentText()

        try:
            movies = self.main.movie_service.search_movies(keyword)
        except Exception:  # noqa: BLE001
            logger.exception("搜索电影失败")
            return

        if genre and genre != "全部类型":
            movies = [b for b in movies if b.genre == genre]

        self.count_label.setText(f"共 {len(movies)} 部电影")

        if not movies:
            populate_grid(self.grid, [])
            label = QLabel("没有找到相关电影，请尝试调整搜索词或类型筛选。")
            label.setObjectName("cardInfo")
            self.grid.addWidget(label)
            return

        cards = []
        for movie in movies:
            card = MovieCard(movie)
            card.clicked.connect(self.main.open_detail)
            cards.append(card)
        populate_grid(self.grid, cards)

    def _reload_categories(self):
        """从当前电影数据动态刷新类型下拉框。"""
        current = self.genre_combo.currentText()
        try:
            movies = self.main.movie_service.list_movies()
        except Exception:  # noqa: BLE001
            movies = []
        categories = sorted({b.genre for b in movies if b.genre})
        items = ["全部类型"] + categories
        self.genre_combo.blockSignals(True)
        self.genre_combo.clear()
        self.genre_combo.addItems(items)
        if current in items:
            self.genre_combo.setCurrentText(current)
        self.genre_combo.blockSignals(False)