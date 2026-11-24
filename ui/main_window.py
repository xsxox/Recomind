# -*- coding: utf-8 -*-
"""
主窗口
极简纯白侧边栏 + 自绘矢量图标 + 页面切换容器。
"""
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QMessageBox, QPushButton, QStackedWidget,
                             QVBoxLayout, QWidget)

import config
from services.movie_service import MovieService
from services.history_service import HistoryService
from services.rating_service import RatingService
from services.recommend_service import RecommendService
from services.user_service import UserService
from ui.detail_dialog import DetailDialog
from ui.manage_page import ManagePage
from ui.recommend_page import RecommendPage
from ui.search_page import SearchPage
from ui.widgets import make_icon
from utils.logger import get_logger

logger = get_logger("ui.main")


class MainWindow(QMainWindow):
    """系统主窗口。"""

    def __init__(self, user):
        super().__init__()
        self.user_service = UserService()
        self.movie_service = MovieService()
        self.rating_service = RatingService()
        self.history_service = HistoryService()
        self.recommend_service = RecommendService()

        self.current_user = user
        self.want_relogin = False
        self._nav_buttons = []

        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.resize(1300, 860)
        self.setMinimumSize(1080, 720)
        self._build_ui()

    def get_user(self):
        """返回当前登录用户。"""
        return self.current_user

    def open_detail(self, movie):
        """打开电影详情对话框，关闭后刷新统计。"""
        dialog = DetailDialog(movie, self)
        dialog.exec_()
        self.manage_page.refresh_all()

    def _build_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.recommend_page = RecommendPage(self)
        self.search_page = SearchPage(self)
        self.manage_page = ManagePage(self)

        self.stack.addWidget(self.recommend_page)
        self.stack.addWidget(self.search_page)
        self.stack.addWidget(self.manage_page)
        root.addWidget(self.stack, 1)

        self.setCentralWidget(central)

        self.recommend_page.refresh()
        self.search_page.refresh()

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(244)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 26, 18, 20)
        layout.setSpacing(6)

        # 品牌标识
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo = QLabel("R")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);"
            "color: #FFFFFF; font-size: 18px; font-weight: bold; border-radius: 10px;"
        )
        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        brand = QLabel("Recomind")
        brand.setObjectName("brandTitle")
        sub = QLabel(f"智能推荐系统 v{config.APP_VERSION}")
        sub.setObjectName("brandSub")
        brand_col.addWidget(brand)
        brand_col.addWidget(sub)

        brand_row.addWidget(logo)
        brand_row.addLayout(brand_col, 1)
        layout.addLayout(brand_row)

        layout.addSpacing(26)

        nav_title = QLabel("导航菜单")
        nav_title.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: bold; padding-left: 10px;")
        layout.addWidget(nav_title)
        layout.addSpacing(4)

        self._nav_specs = [
            ("sparkles", "  个性推荐"),
            ("search", "  电影浏览"),
            ("layers", "  数据管理"),
        ]
        for idx, (icon_name, label) in enumerate(self._nav_specs):
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setMinimumHeight(46)
            btn.setIconSize(QSize(19, 19))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _c, i=idx: self._switch_page(i))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        self._update_nav_state(0)
        layout.addStretch()

        # 底部用户卡片
        user_card = QFrame()
        user_card.setObjectName("userCard")
        u_layout = QVBoxLayout(user_card)
        u_layout.setContentsMargins(14, 14, 14, 14)
        u_layout.setSpacing(12)

        info_row = QHBoxLayout()
        info_row.setSpacing(10)
        display_name = self.current_user.nickname or self.current_user.username
        avatar = QLabel(display_name[0].upper() if display_name else "U")
        avatar.setObjectName("userAvatar")
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        name_lbl = QLabel(display_name)
        name_lbl.setObjectName("userName")
        handle_lbl = QLabel(f"@{self.current_user.username}")
        handle_lbl.setObjectName("userHandle")
        name_col.addWidget(name_lbl)
        name_col.addWidget(handle_lbl)

        info_row.addWidget(avatar)
        info_row.addLayout(name_col, 1)
        u_layout.addLayout(info_row)

        logout_btn = QPushButton("  退出登录")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setIcon(make_icon("logout", "#4B5563", 16))
        logout_btn.setIconSize(QSize(16, 16))
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        u_layout.addWidget(logout_btn)

        layout.addWidget(user_card)
        return sidebar

    def _update_nav_state(self, active_index):
        for idx, btn in enumerate(self._nav_buttons):
            is_active = (idx == active_index)
            btn.setChecked(is_active)
            icon_name = self._nav_specs[idx][0]
            btn.setIcon(make_icon(icon_name, "#4F46E5" if is_active else "#6B7280", 19))

    def _switch_page(self, index):
        self._update_nav_state(index)
        self.stack.setCurrentIndex(index)
        if index == 2:
            self.manage_page.refresh_all()

    def _logout(self):
        if QMessageBox.question(self, "退出登录", "确定退出当前账号？") == QMessageBox.Yes:
            self.want_relogin = True
            self.close()