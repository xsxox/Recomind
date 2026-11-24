# -*- coding: utf-8 -*-
"""
个性推荐页
Spotlight 悬浮搜索栏 + 个性化问候 + 响应式流式电影网格。
"""
from datetime import datetime

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from ui.widgets import (MovieCard, FlowContainer, apply_shadow, make_icon,
                        populate_grid)
from utils.logger import get_logger

logger = get_logger("ui.recommend")


class RecommendPage(QWidget):
    """个性推荐页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._build()

    def _greeting_text(self):
        hour = datetime.now().hour
        if hour < 12:
            period = "上午好"
        elif hour < 18:
            period = "下午好"
        else:
            period = "晚上好"
        user = self.main.get_user()
        name = (user.nickname or user.username) if user else "同学"
        return f"{period}，{name}"

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 20)
        root.setSpacing(18)

        # 顶部欢迎行
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel(self._greeting_text())
        title.setObjectName("heroGreeting")
        subtitle = QLabel("结合 TF-IDF 内容语义与 Item-CF 协同过滤，为你持续发掘感兴趣的好片")
        subtitle.setObjectName("subText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch()

        self.refresh_btn = QPushButton("  换一批推荐")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.setIcon(make_icon("refresh", "#374151", 17))
        self.refresh_btn.setIconSize(QSize(17, 17))
        self.refresh_btn.setMinimumHeight(42)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        # Spotlight 悬浮搜索胶囊
        spot = QFrame()
        spot.setObjectName("spotlightBar")
        apply_shadow(spot, blur=24, y_offset=6, alpha=14)
        spot_layout = QHBoxLayout(spot)
        spot_layout.setContentsMargins(16, 8, 8, 8)
        spot_layout.setSpacing(10)

        search_icon = QLabel()
        search_icon.setPixmap(make_icon("sparkles", "#4F46E5", 20).pixmap(20, 20))
        spot_layout.addWidget(search_icon)

        self.kw_input = QLineEdit()
        self.kw_input.setObjectName("spotlightInput")
        self.kw_input.setMinimumHeight(40)
        self.kw_input.setPlaceholderText("输入你想看的题材或自然语言描述，例如：硬核科幻、谍战动作、悬疑烧脑...")
        self.kw_input.returnPressed.connect(self._keyword_recommend)
        spot_layout.addWidget(self.kw_input, 1)

        self.kw_btn = QPushButton("智能匹配")
        self.kw_btn.setMinimumHeight(40)
        self.kw_btn.setCursor(Qt.PointingHandCursor)
        self.kw_btn.clicked.connect(self._keyword_recommend)
        spot_layout.addWidget(self.kw_btn)
        root.addWidget(spot)

        # 快捷兴趣标签行
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        chip_lbl = QLabel("灵感标签：")
        chip_lbl.setObjectName("subText")
        chip_row.addWidget(chip_lbl)
        for text in ["科幻 太空", "动作 谍战", "悬疑 犯罪", "爱情 文艺", "动画 奇幻"]:
            chip = QPushButton(text)
            chip.setObjectName("chipBtn")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _c, t=text: self._quick_keyword(t))
            chip_row.addWidget(chip)
        chip_row.addStretch()
        root.addLayout(chip_row)

        # 结果分区标题
        self.status_label = QLabel("猜你喜欢")
        self.status_label.setObjectName("sectionTitle")
        root.addWidget(self.status_label)

        # 自适应流式卡片区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = FlowContainer(h_spacing=18, v_spacing=20)
        self.grid = self.container.flow
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

    def _quick_keyword(self, text):
        self.kw_input.setText(text)
        self._keyword_recommend()

    def refresh(self):
        """重新生成个性化推荐。"""
        user = self.main.get_user()
        self.status_label.setText("猜你喜欢 · 混合个性化推荐")
        self._set_message("正在为你计算个性化片单…")
        try:
            results = self.main.recommend_service.recommend_for_user(user.id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("个性化推荐失败")
            QMessageBox.critical(self, "错误", f"推荐生成失败：{exc}")
            return
        if not results:
            self._set_message("暂无推荐结果，请先在「电影浏览」中查看或评分几部电影。")
            return
        cards = []
        for movie, score in results:
            card = MovieCard(movie, score=score)
            card.clicked.connect(self.main.open_detail)
            cards.append(card)
        populate_grid(self.grid, cards)

    def _keyword_recommend(self):
        keyword = self.kw_input.text().strip()
        if not keyword:
            QMessageBox.information(self, "提示", "请输入关键词或偏好描述")
            return
        try:
            results = self.main.recommend_service.recommend_by_keyword(keyword)
        except Exception as exc:  # noqa: BLE001
            logger.exception("关键词推荐失败")
            QMessageBox.critical(self, "错误", f"推荐生成失败：{exc}")
            return
        self.status_label.setText(f"“{keyword}” 的语义匹配结果 · 共 {len(results)} 本")
        if not results:
            self._set_message("没有找到与描述相符的电影，换个关键词试试看吧。")
            return
        cards = []
        for movie, score in results:
            card = MovieCard(movie, score=score)
            card.clicked.connect(self.main.open_detail)
            cards.append(card)
        populate_grid(self.grid, cards)

    def _set_message(self, text):
        populate_grid(self.grid, [])
        label = QLabel(text)
        label.setObjectName("cardInfo")
        label.setWordWrap(True)
        self.grid.addWidget(label)