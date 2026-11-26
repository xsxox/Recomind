# -*- coding: utf-8 -*-
"""
登录 / 注册对话框
暗夜影院极光视觉分栏 + 极简表单。
"""
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (QColor, QLinearGradient, QPainter, QPen,
                         QRadialGradient)
from PyQt5.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSpinBox,
                             QStackedWidget, QVBoxLayout, QWidget)

from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger("ui.login")


class HeroArtworkPanel(QFrame):
    """左侧影院极光艺术画布。"""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor("#07090E"))
        bg.setColorAt(1.0, QColor("#0B1626"))
        p.fillRect(rect, bg)

        g1 = QRadialGradient(QPointF(w * 0.22, h * 0.22), w * 0.72)
        g1.setColorAt(0.0, QColor(14, 165, 233, 125))
        g1.setColorAt(1.0, QColor(14, 165, 233, 0))
        p.fillRect(rect, g1)

        g2 = QRadialGradient(QPointF(w * 0.85, h * 0.82), w * 0.65)
        g2.setColorAt(0.0, QColor(6, 182, 212, 70))
        g2.setColorAt(1.0, QColor(6, 182, 212, 0))
        p.fillRect(rect, g2)

        p.setPen(QPen(QColor(255, 255, 255, 20), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(w * 0.84, h * 0.18), 110, 110)
        p.drawEllipse(QPointF(w * 0.84, h * 0.18), 170, 170)
        p.end()


class LoginDialog(QDialog):
    """登录与注册对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_service = UserService()
        self.logged_user = None
        self.setWindowTitle("登录 - Recomind 智能影库")
        self.resize(900, 580)
        self.setMinimumSize(820, 540)
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_hero(), 5)
        root.addWidget(self._build_form_side(), 6)

    def _build_hero(self):
        hero = HeroArtworkPanel()
        layout = QVBoxLayout(hero)
        layout.setContentsMargins(40, 44, 36, 36)
        layout.setSpacing(16)

        pill = QLabel("CINEMA · NLP & ML")
        pill.setStyleSheet(
            "background-color: rgba(255,255,255,0.10); color: #C7D2FE;"
            "font-size: 11px; font-weight: bold; letter-spacing: 1px;"
            "padding: 6px 12px; border-radius: 12px;"
        )
        layout.addWidget(pill, 0, Qt.AlignLeft)

        layout.addSpacing(8)
        title = QLabel("Recomind\n私人智能影库")
        title.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold; background: transparent;")
        layout.addWidget(title)

        desc = QLabel(
            "融合 TMDB 全片库、影评 NLP 语义分析、协同过滤与 RAG 对话助手，"
            "每一晚都为你精准挑选值得细品的好电影。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 14px; background: transparent;")
        layout.addWidget(desc)

        layout.addStretch()

        demo_lbl = QLabel("一键体验演示账号（密码均为 123456）")
        demo_lbl.setStyleSheet("color: #CBD5E1; font-size: 13px; background: transparent;")
        layout.addWidget(demo_lbl)

        demo_row = QHBoxLayout()
        demo_row.setSpacing(8)
        for uname, tag in [("alice", "科幻"), ("carol", "剧情"), ("erin", "动作"), ("admin", "管理")]:
            btn = QPushButton(f"{uname}·{tag}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: rgba(255,255,255,0.08); color: #F8FAFC;"
                "border: 1px solid rgba(255,255,255,0.16); border-radius: 8px;"
                "padding: 8px 8px; font-size: 12px; font-weight: 500; }"
                "QPushButton:hover { background-color: rgba(14,165,233,0.45); border-color: #38BDF8; }"
            )
            btn.clicked.connect(lambda _c, u=uname: self._fill_demo(u))
            demo_row.addWidget(btn)
        layout.addLayout(demo_row)
        return hero

    def _build_form_side(self):
        panel = QWidget()
        panel.setObjectName("loginFormPanel")
        panel.setStyleSheet("QWidget#loginFormPanel { background-color: #0B0E16; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(46, 36, 46, 34)
        layout.setSpacing(18)

        seg = QFrame()
        seg.setObjectName("segmentBox")
        seg_layout = QHBoxLayout(seg)
        seg_layout.setContentsMargins(4, 4, 4, 4)
        seg_layout.setSpacing(4)

        self.login_tab_btn = QPushButton("登录账号")
        self.reg_tab_btn = QPushButton("注册新账号")
        for btn in (self.login_tab_btn, self.reg_tab_btn):
            btn.setObjectName("segmentBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
        self.login_tab_btn.setChecked(True)

        self.login_tab_btn.clicked.connect(lambda: self._switch_tab(0))
        self.reg_tab_btn.clicked.connect(lambda: self._switch_tab(1))

        seg_layout.addWidget(self.login_tab_btn)
        seg_layout.addWidget(self.reg_tab_btn)
        layout.addWidget(seg)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_tab())
        self.stack.addWidget(self._build_register_tab())
        layout.addWidget(self.stack, 1)
        return panel

    def _switch_tab(self, index):
        self.login_tab_btn.setChecked(index == 0)
        self.reg_tab_btn.setChecked(index == 1)
        self.stack.setCurrentIndex(index)

    def _fill_demo(self, username):
        self._switch_tab(0)
        self.login_username.setText(username)
        self.login_password.setText("123456")

    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #CBD5E1; font-size: 13px; font-weight: bold;")
        return lbl

    def _build_login_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 14, 0, 0)
        layout.setSpacing(8)

        heading = QLabel("欢迎回来")
        heading.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        sub = QLabel("输入账号信息开启你的私人观影推荐")
        sub.setObjectName("subText")
        layout.addWidget(heading)
        layout.addWidget(sub)
        layout.addSpacing(14)

        layout.addWidget(self._field_label("用户名"))
        self.login_username = QLineEdit()
        self.login_username.setMinimumHeight(46)
        self.login_username.setPlaceholderText("请输入用户名")
        layout.addWidget(self.login_username)
        layout.addSpacing(8)

        layout.addWidget(self._field_label("密码"))
        self.login_password = QLineEdit()
        self.login_password.setMinimumHeight(46)
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("请输入密码")
        self.login_password.returnPressed.connect(self._do_login)
        layout.addWidget(self.login_password)

        layout.addSpacing(20)
        self.login_btn = QPushButton("进入影库")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setDefault(True)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(
            "QPushButton { background-color: #6366F1; color: #FFFFFF; border: none;"
            "border-radius: 10px; font-size: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #4F46E5; }"
        )
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)
        layout.addStretch()
        return w

    def _build_register_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._field_label("用户名"))
        self.reg_username = QLineEdit()
        self.reg_username.setMinimumHeight(42)
        self.reg_username.setPlaceholderText("设置登录用户名")
        layout.addWidget(self.reg_username)

        pw_row = QHBoxLayout()
        pw_row.setSpacing(10)
        col1, col2 = QVBoxLayout(), QVBoxLayout()
        col1.setSpacing(4)
        col2.setSpacing(4)
        col1.addWidget(self._field_label("密码"))
        self.reg_password = QLineEdit()
        self.reg_password.setMinimumHeight(42)
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setPlaceholderText("设置密码")
        col1.addWidget(self.reg_password)

        col2.addWidget(self._field_label("确认密码"))
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setMinimumHeight(42)
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_confirm.setPlaceholderText("再次输入")
        col2.addWidget(self.reg_confirm)
        pw_row.addLayout(col1)
        pw_row.addLayout(col2)
        layout.addLayout(pw_row)

        layout.addWidget(self._field_label("昵称（选填）"))
        self.reg_nickname = QLineEdit()
        self.reg_nickname.setMinimumHeight(42)
        self.reg_nickname.setPlaceholderText("希望系统如何称呼你")
        layout.addWidget(self.reg_nickname)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)
        g_col, a_col = QVBoxLayout(), QVBoxLayout()
        g_col.setSpacing(4)
        a_col.setSpacing(4)
        g_col.addWidget(self._field_label("性别"))
        self.reg_gender = QComboBox()
        self.reg_gender.setMinimumHeight(42)
        self.reg_gender.addItems(["男", "女", "其他"])
        g_col.addWidget(self.reg_gender)

        a_col.addWidget(self._field_label("年龄"))
        self.reg_age = QSpinBox()
        self.reg_age.setMinimumHeight(42)
        self.reg_age.setRange(1, 120)
        self.reg_age.setValue(20)
        a_col.addWidget(self.reg_age)
        meta_row.addLayout(g_col)
        meta_row.addLayout(a_col)
        layout.addLayout(meta_row)

        layout.addSpacing(12)
        self.register_btn = QPushButton("创建账号")
        self.register_btn.setMinimumHeight(46)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setStyleSheet(
            "QPushButton { background-color: #6366F1; color: #FFFFFF; border: none;"
            "border-radius: 10px; font-size: 15px; font-weight: bold; }"
            "QPushButton:hover { background-color: #4F46E5; }"
        )
        self.register_btn.clicked.connect(self._do_register)
        layout.addWidget(self.register_btn)
        layout.addStretch()
        return w

    def _do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        user, error = self.user_service.login(username, password)
        if error:
            QMessageBox.warning(self, "登录失败", error)
            return
        self.logged_user = user
        self.accept()

    def _do_register(self):
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        if password != confirm:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return
        user_id, error = self.user_service.register(
            username, password,
            nickname=self.reg_nickname.text().strip(),
            gender=self.reg_gender.currentText(),
            age=self.reg_age.value(),
        )
        if error:
            QMessageBox.warning(self, "注册失败", error)
            return
        QMessageBox.information(self, "成功", "注册成功，请登录")
        self.login_username.setText(username)
        self.login_password.clear()
        self._switch_tab(0)