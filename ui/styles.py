# -*- coding: utf-8 -*-
"""
界面样式模块 (v3.0 极夜冷青圆润流媒体风格 · 参考 MOVIEGO 设计语言)
==================================================================
设计精髓：
  - 极夜墨黑背景 (#080B0C) + 大圆角浮动玻璃面板 (#101518, radius 20px)
  - 冰川薄荷青冷色系 (#5EEAD4 / #2DD4BF / #34D399) + 冰蓝辅助 (#38BDF8)
  - 实心圆角药丸导航 + 全圆角胶囊按钮 + 柔和微光描边
"""

STYLE_SHEET = """
* {
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #E2E8F0;
}

QMainWindow, QDialog {
    background-color: #080B0C;
}

/* ---------- 左侧浮动大圆角边栏 ---------- */
QFrame#sideBar {
    background-color: #0F1416;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 22px;
}

QLabel#brandTitle {
    color: #F8FAFC;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 1.2px;
}

QLabel#brandTag {
    background-color: rgba(94, 234, 212, 0.14);
    color: #5EEAD4;
    border: 1px solid rgba(94, 234, 212, 0.30);
    border-radius: 6px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.6px;
}

QLabel#navGroupLabel {
    color: #526068;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1.0px;
    padding-left: 12px;
}

QPushButton#sideNavBtn {
    background-color: transparent;
    color: #8B9AA2;
    border: none;
    border-radius: 14px;
    padding: 11px 16px;
    font-size: 14px;
    font-weight: 500;
    text-align: left;
    outline: none;
}

QPushButton#sideNavBtn:hover {
    color: #F8FAFC;
    background-color: rgba(255, 255, 255, 0.05);
}

QPushButton#sideNavBtn:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6EE7B7, stop:1 #2DD4BF);
    color: #06211B;
    font-weight: bold;
}

QFrame#engineStatusCard {
    background-color: rgba(45, 212, 191, 0.07);
    border: 1px solid rgba(94, 234, 212, 0.16);
    border-radius: 14px;
}

QFrame#sideUserCard {
    background-color: #141B1E;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
}

QLabel#userAvatar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5EEAD4, stop:1 #0EA5E9);
    color: #06211B;
    font-size: 14px;
    font-weight: bold;
    border-radius: 17px;
}

QLabel#userName {
    color: #F8FAFC;
    font-size: 13px;
    font-weight: bold;
}

QPushButton#logoutBtn {
    background-color: #1A2226;
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 5px 8px;
    font-size: 12px;
    outline: none;
}

QPushButton#logoutBtn:hover {
    background-color: rgba(248, 113, 113, 0.18);
    color: #FCA5A5;
    border-color: rgba(248, 113, 113, 0.45);
}

/* ---------- 排版层级 ---------- */
QLabel#pageTitle {
    font-size: 25px;
    font-weight: bold;
    color: #F8FAFC;
    letter-spacing: -0.2px;
}

QLabel#sectionTitle {
    font-size: 17px;
    font-weight: bold;
    color: #F1F5F9;
}

QLabel#subText {
    font-size: 13px;
    color: #6B7C85;
}

QLabel#cardTitle {
    font-size: 14px;
    font-weight: bold;
    color: #F1F5F9;
}

QLabel#cardMeta {
    font-size: 12px;
    color: #6B7C85;
}

QLabel#cardInfo {
    font-size: 14px;
    color: #94A3B8;
}

QLabel#scoreBadge {
    background-color: rgba(94, 234, 212, 0.12);
    color: #5EEAD4;
    border: 1px solid rgba(94, 234, 212, 0.25);
    border-radius: 12px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: bold;
}

/* ---------- 大圆角玻璃面板与容器 ---------- */
QFrame#panel {
    background-color: #101518;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 20px;
}

QFrame#subPanel {
    background-color: #151C20;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

QFrame#spotlightBar {
    background-color: #101518;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 22px;
}

QFrame#movieCard {
    background-color: transparent;
    border: none;
}

QFrame#statCard {
    background-color: #101518;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 18px;
}

QLabel#statNumber {
    font-size: 26px;
    font-weight: bold;
    color: #F8FAFC;
}

QLabel#statLabel {
    font-size: 13px;
    color: #6B7C85;
}

/* ---------- 全圆角胶囊按钮 ---------- */
QPushButton {
    background-color: #2DD4BF;
    color: #06211B;
    border: none;
    border-radius: 16px;
    padding: 9px 20px;
    font-size: 14px;
    font-weight: bold;
    outline: none;
}

QPushButton:hover {
    background-color: #5EEAD4;
}

QPushButton:pressed {
    background-color: #14B8A6;
}

QPushButton#secondaryBtn {
    background-color: #151C20;
    color: #E2E8F0;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    font-weight: 500;
}

QPushButton#secondaryBtn:hover {
    background-color: #1C252A;
    border-color: rgba(94, 234, 212, 0.40);
    color: #FFFFFF;
}

QPushButton#dangerBtn {
    background-color: rgba(248, 113, 113, 0.14);
    color: #FCA5A5;
    border: 1px solid rgba(248, 113, 113, 0.35);
    border-radius: 16px;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background-color: #EF4444;
    color: #FFFFFF;
    border-color: #EF4444;
}

QPushButton#chipBtn {
    background-color: #11171A;
    color: #CBD5E1;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 17px;
    padding: 6px 15px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#chipBtn:hover {
    background-color: rgba(94, 234, 212, 0.12);
    color: #FFFFFF;
    border-color: rgba(94, 234, 212, 0.45);
}

QPushButton#chipBtn:checked {
    background-color: #2DD4BF;
    color: #06211B;
    border-color: #5EEAD4;
    font-weight: bold;
}

QPushButton#genreChip {
    background-color: #13191D;
    color: #CBD5E1;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 18px;
    padding: 8px 18px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#genreChip:hover {
    background-color: #1B2429;
    color: #FFFFFF;
}

QPushButton#genreChip:checked {
    background-color: rgba(45, 212, 191, 0.20);
    color: #99F6E4;
    border: 1.5px solid #2DD4BF;
    font-weight: bold;
}

/* ---------- 分段切换器 ---------- */
QFrame#segmentBox {
    background-color: #080B0C;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 14px;
}

QPushButton#segmentBtn {
    background-color: transparent;
    color: #6B7C85;
    border: none;
    border-radius: 10px;
    padding: 7px 16px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#segmentBtn:hover {
    color: #F8FAFC;
}

QPushButton#segmentBtn:checked {
    background-color: #172024;
    color: #FFFFFF;
    font-weight: bold;
}

/* ---------- 暗色圆角输入控件 ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #0E1316;
    border: 1.5px solid rgba(255, 255, 255, 0.09);
    border-radius: 14px;
    padding: 8px 14px;
    font-size: 14px;
    color: #F8FAFC;
    selection-background-color: #2DD4BF;
    selection-color: #06211B;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    background-color: #12191D;
    border: 1.5px solid #5EEAD4;
}

QLineEdit#spotlightInput {
    background-color: transparent;
    border: none;
    padding: 8px 6px;
    font-size: 14px;
    color: #F8FAFC;
}

QLineEdit#spotlightInput:focus {
    background-color: transparent;
    border: none;
}

QComboBox::drop-down {
    border: none;
    width: 26px;
}

QComboBox QAbstractItemView {
    background-color: #101518;
    border: 1px solid rgba(94, 234, 212, 0.25);
    border-radius: 14px;
    padding: 4px;
    color: #F1F5F9;
    selection-background-color: rgba(45, 212, 191, 0.28);
    selection-color: #FFFFFF;
    font-size: 14px;
    outline: 0;
}

QComboBox QAbstractItemView::item {
    min-height: 34px;
    padding: 4px 10px;
    border-radius: 8px;
}

QCheckBox {
    spacing: 10px;
    font-size: 14px;
    font-weight: 500;
    color: #F1F5F9;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 7px;
    border: 1.5px solid #334149;
    background-color: #0C1012;
}

QCheckBox::indicator:hover {
    border-color: #5EEAD4;
}

QCheckBox::indicator:checked {
    border: 5px solid #2DD4BF;
    background-color: #FFFFFF;
}

/* ---------- 暗色现代数据表 ---------- */
QTableWidget {
    background-color: #101518;
    alternate-background-color: #131A1E;
    border: none;
    font-size: 14px;
    color: #E2E8F0;
    selection-background-color: rgba(45, 212, 191, 0.20);
    selection-color: #FFFFFF;
    outline: 0;
}

QTableWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

QHeaderView::section {
    background-color: #101518;
    color: #6B7C85;
    padding: 12px 12px;
    border: none;
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.08);
    font-size: 13px;
    font-weight: bold;
}

/* ---------- 滚动条 & 弹窗 ---------- */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 4px 0;
}

QScrollBar::handle:vertical {
    background: #1F2A30;
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #2F3E46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMessageBox {
    background-color: #101518;
}

QMessageBox QLabel {
    font-size: 14px;
    color: #F8FAFC;
}
"""


def genre_color(genre):
    """根据类型返回海报颜色（兜底默认色）。"""
    from data.sample_data import CATEGORY_COLORS, DEFAULT_COLOR
    return CATEGORY_COLORS.get(genre, DEFAULT_COLOR)
