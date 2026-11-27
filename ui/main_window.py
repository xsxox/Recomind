# -*- coding: utf-8 -*-
"""
主窗口 (v3.0 浮动圆角边栏 + 平滑切页过渡动画)
==============================================
参考 MOVIEGO 极简圆润流媒体桌面端：
  - 外留 14px 边距，左侧为独立大圆角浮动边栏 + 实心药丸导航
  - 右侧切换页面带有 QPropertyAnimation 淡入过渡动画
"""
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt
from PyQt5.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                             QLabel, QMainWindow, QMessageBox, QPushButton,
                             QStackedWidget, QVBoxLayout, QWidget)

import config
from services.history_service import HistoryService
from services.movie_service import MovieService
from services.rating_service import RatingService
from services.recommend_service import RecommendService
from services.setting_service import SettingService
from services.user_service import UserService
from ui.assistant_page import AssistantPage
from ui.dashboard_page import DashboardPage
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
        self._fade_anim = None

        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.resize(1400, 900)
        self.setMinimumSize(1140, 740)
        self._build_ui()

    def get_user(self):
        return self.current_user

    def open_detail(self, movie):
        dialog = DetailDialog(movie, self)
        dialog.exec_()
        self.manage_page.refresh_all()
        self.profile_page.refresh()

    def refresh_user_display(self):
        display = self.current_user.nickname or self.current_user.username
        self.top_avatar.setText(display[0].upper() if display else "U")
        self.top_name_label.setText(display)

    def _build_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.recommend_page = RecommendPage(self)
        self.search_page = SearchPage(self)
        self.assistant_page = AssistantPage(self)
        self.profile_page = ProfilePage(self)
        self.settings_page = SettingsPage(self)
        self.manage_page = ManagePage(self)
        self.dashboard_page = DashboardPage(self)

        for page in (
            self.recommend_page,
            self.search_page,
            self.assistant_page,
            self.profile_page,
            self.settings_page,
            self.manage_page,
            self.dashboard_page,
        ):
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)

        self.setCentralWidget(central)

        self.recommend_page.refresh()
        self.search_page.refresh()

    def _build_sidebar(self):
        bar = QFrame()
        bar.setObjectName("sideBar")
        bar.setFixedWidth(236)

        layout = QVBoxLayout(bar)
        layout.setContentsMargins(14, 22, 14, 16)
        layout.setSpacing(5)

        # 品牌标识区
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(10, 0, 6, 14)
        brand_row.setSpacing(10)
        logo = QLabel("R")
        logo.setFixedSize(32, 32)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6EE7B7, stop:1 #0EA5E9);"
            "color: #06211B; font-size: 16px; font-weight: bold; border-radius: 10px;"
        )
        brand = QLabel("RECOMIND")
        brand.setObjectName("brandTitle")
        tag = QLabel("AI")
        tag.setObjectName("brandTag")
        brand_row.addWidget(logo)
        brand_row.addWidget(brand)
        brand_row.addWidget(tag)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        is_admin = self.user_service.is_admin(self.current_user)
        groups = [
            ("MENU", [
                ("sparkles", "个性推荐", 0, False),
                ("movie", "影片库", 1, False),
                ("bot", "AI 影伴", 2, False),
            ]),
            ("SYSTEM & PROFILE", [
                ("users", "个人空间", 3, False),
                ("chart-bar", "算法分析", 6, False),
                ("settings", "偏好设置", 4, False),
                ("layers", "后台管理", 5, True),
            ]),
        ]

        for group_title, items in groups:
            visible = [(ic, lb, si) for ic, lb, si, admin in items if not admin or is_admin]
            if not visible:
                continue
            g_lbl = QLabel(group_title)
            g_lbl.setObjectName("navGroupLabel")
            layout.addSpacing(8)
            layout.addWidget(g_lbl)
            layout.addSpacing(2)

            for icon_name, label, stack_idx in visible:
                nav_index = len(self._nav_items)
                self._nav_items.append((icon_name, label, stack_idx))
                btn = QPushButton(f"  {label}")
                btn.setObjectName("sideNavBtn")
                btn.setCheckable(True)
                btn.setIconSize(QSize(18, 18))
                btn.setMinimumHeight(42)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda _c, i=nav_index: self._switch_page(i))
                self._nav_buttons.append(btn)
                layout.addWidget(btn)

        layout.addStretch()

        # AI 引擎在线状态指示卡
        engine_card = QFrame()
        engine_card.setObjectName("engineStatusCard")
        ec_layout = QVBoxLayout(engine_card)
        ec_layout.setContentsMargins(12, 10, 12, 10)
        ec_layout.setSpacing(4)
        ec_top = QHBoxLayout()
        ec_top.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet("color: #34D399; font-size: 10px;")
        ec_title = QLabel("混合引擎就绪")
        ec_title.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: bold;")
        ec_top.addWidget(dot)
        ec_top.addWidget(ec_title)
        ec_top.addStretch()
        ec_layout.addLayout(ec_top)
        ec_sub = QLabel("SBERT/LSA · SVD · CF · MMR")
        ec_sub.setStyleSheet("color: #5EEAD4; font-size: 10px; font-weight: 500;")
        ec_layout.addWidget(ec_sub)
        layout.addWidget(engine_card)
        layout.addSpacing(8)

        # 底部当前用户胶囊卡
        user_card = QFrame()
        user_card.setObjectName("sideUserCard")
        uc_layout = QHBoxLayout(user_card)
        uc_layout.setContentsMargins(10, 10, 10, 10)
        uc_layout.setSpacing(10)

        display = self.current_user.nickname or self.current_user.username
        self.top_avatar = QLabel(display[0].upper() if display else "U")
        self.top_avatar.setObjectName("userAvatar")
        self.top_avatar.setFixedSize(34, 34)
        self.top_avatar.setAlignment(Qt.AlignCenter)
        uc_layout.addWidget(self.top_avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        self.top_name_label = QLabel(display)
        self.top_name_label.setObjectName("userName")
        role_lbl = QLabel("管理员" if is_admin else "影迷会员")
        role_lbl.setStyleSheet("color: #6B7C85; font-size: 11px;")
        name_col.addWidget(self.top_name_label)
        name_col.addWidget(role_lbl)
        uc_layout.addLayout(name_col, 1)

        logout_btn = QPushButton()
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setIcon(make_icon("logout", "#94A3B8", 15))
        logout_btn.setIconSize(QSize(15, 15))
        logout_btn.setFixedSize(32, 32)
        logout_btn.setToolTip("退出登录")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        uc_layout.addWidget(logout_btn)

        layout.addWidget(user_card)

        self._update_nav_state(0)
        return bar

    def _update_nav_state(self, active_index):
        for idx, btn in enumerate(self._nav_buttons):
            is_active = (idx == active_index)
            btn.setChecked(is_active)
            icon_name = self._nav_items[idx][0]
            btn.setIcon(make_icon(icon_name, "#06211B" if is_active else "#8B9AA2", 18))

    def _switch_page(self, nav_index):
        self._update_nav_state(nav_index)
        stack_index = self._nav_items[nav_index][2]
        if self.stack.currentIndex() == stack_index:
            return
        self.stack.setCurrentIndex(stack_index)
        target_widget = self.stack.currentWidget()

        # 页面切换平滑淡入动画
        effect = QGraphicsOpacityEffect(target_widget)
        target_widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.35)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: target_widget.setGraphicsEffect(None))
        self._fade_anim = anim
        anim.start()

        if stack_index == 3:
            self.profile_page.refresh()
        elif stack_index == 4:
            self.settings_page.refresh()
        elif stack_index == 5:
            self.manage_page.refresh_all()
        elif stack_index == 6:
            self.dashboard_page._draw_rating_chart()

    def _logout(self):
        if QMessageBox.question(self, "退出登录", "确定退出当前账号？") == QMessageBox.Yes:
            self.want_relogin = True
            self.close()
