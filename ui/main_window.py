# -*- coding: utf-8 -*-
"""
主窗口
极简纯白侧边栏 + 自绘矢量图标 + 页面切换容器，
包含：个性推荐、电影浏览、个人中心、设置，以及仅管理员可见的后台管理。
"""
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMainWindow,
                             QMessageBox, QPushButton, QStackedWidget,
                             QVBoxLayout, QWidget)

import config
from services.history_service import HistoryService
from services.movie_service import MovieService
from services.rating_service import RatingService
from services.recommend_service import RecommendService
from services.setting_service import SettingService
from services.user_service import UserService
from ui.detail_dialog import DetailDialog
from ui.manage_page import ManagePage
from ui.profile_page import ProfilePage
from ui.recommend_page import RecommendPage
from ui.search_page import SearchPage
from ui.settings_page import SettingsPage
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
        self.setting_service = SettingService()

        self.current_user = user
        self.want_relogin = False
        self._nav_buttons = []
        self._nav_items = []

        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.resize(1300, 860)
        self.setMinimumSize(1080, 720)
        self._build_ui()

    # ---------- 对外接口 ----------

    def get_user(self):
        """返回当前登录用户。"""
        return self.current_user

    def open_detail(self, movie):
        """打开电影详情对话框，关闭后刷新统计。"""
        dialog = DetailDialog(movie, self)
        dialog.exec_()
        self.manage_page.refresh_all()
        self.profile_page.refresh()

    def refresh_user_display(self):
        """刷新侧边栏与个人中心里展示的用户信息。"""
        display = self.current_user.nickname or self.current_user.username
        self.sidebar_avatar.setText(display[0].upper() if display else "U")
        self.sidebar_name_label.setText(display)
        self.sidebar_handle_label.setText(f"@{self.current_user.username}")

    # ---------- 界面构建 ----------

    def _build_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.recommend_page = RecommendPage(self)
        self.search_page = SearchPage(self)
        self.profile_page = ProfilePage(self)
        self.settings_page = SettingsPage(self)
        self.manage_page = ManagePage(self)

        for page in (self.recommend_page, self.search_page, self.profile_page,
                     self.settings_page, self.manage_page):
            self.stack.addWidget(page)
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

        # 导航项：(图标, 文案, 页面栈下标, 是否仅管理员)
        is_admin = self.user_service.is_admin(self.current_user)
        all_items = [
            ("sparkles", "  个性推荐", 0, False),
            ("search", "  电影浏览", 1, False),
            ("users", "  个人中心", 2, False),
            ("settings", "  设置", 3, False),
            ("layers", "  后台管理", 4, True),
        ]
        self._nav_items = [(ic, lb, si) for ic, lb, si, admin in all_items if not admin or is_admin]

        for nav_index, (icon_name, label, _stack_index) in enumerate(self._nav_items):
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setMinimumHeight(46)
            btn.setIconSize(QSize(19, 19))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _c, i=nav_index: self._switch_page(i))
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
        self.sidebar_avatar = QLabel(display_name[0].upper() if display_name else "U")
        self.sidebar_avatar.setObjectName("userAvatar")
        self.sidebar_avatar.setFixedSize(38, 38)
        self.sidebar_avatar.setAlignment(Qt.AlignCenter)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        self.sidebar_name_label = QLabel(display_name)
        self.sidebar_name_label.setObjectName("userName")
        self.sidebar_handle_label = QLabel(f"@{self.current_user.username}")
        self.sidebar_handle_label.setObjectName("userHandle")
        name_col.addWidget(self.sidebar_name_label)
        name_col.addWidget(self.sidebar_handle_label)

        info_row.addWidget(self.sidebar_avatar)
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
            icon_name = self._nav_items[idx][0]
            btn.setIcon(make_icon(icon_name, "#4F46E5" if is_active else "#6B7280", 19))

    def _switch_page(self, nav_index):
        self._update_nav_state(nav_index)
        stack_index = self._nav_items[nav_index][2]
        self.stack.setCurrentIndex(stack_index)
        if stack_index == 2:
            self.profile_page.refresh()
        elif stack_index == 3:
            self.settings_page.refresh()
        elif stack_index == 4:
            self.manage_page.refresh_all()

    def _logout(self):
        if QMessageBox.question(self, "退出登录", "确定退出当前账号？") == QMessageBox.Yes:
            self.want_relogin = True
            self.close()
