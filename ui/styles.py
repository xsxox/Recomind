# -*- coding: utf-8 -*-
"""
界面样式模块 (v2.2 极夜冰川冷色系 · Arctic Obsidian)
===================================================
参考现代 AI 产品与极简流媒体客户端（Linear / Plex / Apple TV+）：
  - 极夜深海黑画布 (#07090E) + 深海石板面板 (#101521)
  - 冰川天青主强调色 (#0284C7 / #0EA5E9 / #38BDF8) + 极光青 (#22D3EE)
  - 细腻 1px 冷色玻璃描边，沉稳耐看、极具科技感
"""

STYLE_SHEET = """
* {
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #E2E8F0;
}

QMainWindow, QDialog {
    background-color: #07090E;
}

/* ---------- 左侧沉浸式冷色边栏 ---------- */
QFrame#sideBar {
    background-color: #0B0E16;
    border-right: 1px solid rgba(148, 163, 184, 0.09);
}

QLabel#brandTitle {
    color: #F8FAFC;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 1.2px;
}

QLabel#brandTag {
    background-color: rgba(14, 165, 233, 0.16);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 5px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.6px;
}

QLabel#navGroupLabel {
    color: #475569;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.8px;
    padding-left: 10px;
}

QPushButton#sideNavBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 9px;
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 500;
    text-align: left;
    outline: none;
}

QPushButton#sideNavBtn:hover {
    color: #F8FAFC;
    background-color: rgba(56, 189, 248, 0.07);
}

QPushButton#sideNavBtn:checked {
    background-color: rgba(14, 165, 233, 0.14);
    color: #FFFFFF;
    border-left: 3px solid #38BDF8;
    font-weight: bold;
}

QFrame#engineStatusCard {
    background-color: rgba(14, 165, 233, 0.06);
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 10px;
}

QFrame#sideUserCard {
    background-color: #101521;
    border: 1px solid rgba(148, 163, 184, 0.10);
    border-radius: 12px;
}

QLabel#userAvatar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38BDF8, stop:1 #0284C7);
    color: #FFFFFF;
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
    background-color: #151C2C;
    color: #94A3B8;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 12px;
    outline: none;
}

QPushButton#logoutBtn:hover {
    background-color: rgba(239, 68, 68, 0.18);
    color: #FCA5A5;
    border-color: rgba(239, 68, 68, 0.45);
}

/* ---------- 排版层级 ---------- */
QLabel#pageTitle {
    font-size: 26px;
    font-weight: bold;
    color: #F8FAFC;
    letter-spacing: -0.3px;
}

QLabel#sectionTitle {
    font-size: 18px;
    font-weight: bold;
    color: #F1F5F9;
}

QLabel#subText {
    font-size: 13px;
    color: #64748B;
}

QLabel#cardTitle {
    font-size: 14px;
    font-weight: bold;
    color: #F1F5F9;
}

QLabel#cardMeta {
    font-size: 12px;
    color: #64748B;
}

QLabel#cardInfo {
    font-size: 14px;
    color: #94A3B8;
}

QLabel#scoreBadge {
    background-color: #101726;
    color: #7DD3FC;
    border: 1px solid rgba(56, 189, 248, 0.28);
    border-radius: 9px;
    padding: 6px 13px;
    font-size: 13px;
    font-weight: bold;
}

/* ---------- 玻璃拟态面板与容器 ---------- */
QFrame#panel {
    background-color: #101521;
    border: 1px solid rgba(148, 163, 184, 0.09);
    border-radius: 16px;
}

QFrame#subPanel {
    background-color: #141B2A;
    border: 1px solid rgba(148, 163, 184, 0.10);
    border-radius: 14px;
}

QFrame#spotlightBar {
    background-color: #0F1420;
    border: 1px solid rgba(56, 189, 248, 0.16);
    border-radius: 22px;
}

QFrame#movieCard {
    background-color: transparent;
    border: none;
}

QFrame#statCard {
    background-color: #101521;
    border: 1px solid rgba(148, 163, 184, 0.09);
    border-radius: 16px;
}

QLabel#statNumber {
    font-size: 28px;
    font-weight: bold;
    color: #F8FAFC;
}

QLabel#statLabel {
    font-size: 13px;
    color: #64748B;
}

/* ---------- 现代冷色按钮 ---------- */
QPushButton {
    background-color: #0284C7;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 9px 18px;
    font-size: 14px;
    font-weight: bold;
    outline: none;
}

QPushButton:hover {
    background-color: #0EA5E9;
}

QPushButton:pressed {
    background-color: #0369A1;
}

QPushButton#secondaryBtn {
    background-color: #131A29;
    color: #E2E8F0;
    border: 1px solid rgba(148, 163, 184, 0.14);
    font-weight: 500;
}

QPushButton#secondaryBtn:hover {
    background-color: #1B2438;
    border-color: rgba(56, 189, 248, 0.35);
    color: #FFFFFF;
}

QPushButton#dangerBtn {
    background-color: rgba(220, 38, 38, 0.14);
    color: #FCA5A5;
    border: 1px solid rgba(239, 68, 68, 0.35);
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background-color: #DC2626;
    color: #FFFFFF;
    border-color: #DC2626;
}

QPushButton#chipBtn {
    background-color: #101521;
    color: #CBD5E1;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 16px;
    padding: 6px 15px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#chipBtn:hover {
    background-color: rgba(14, 165, 233, 0.16);
    color: #FFFFFF;
    border-color: rgba(56, 189, 248, 0.50);
}

QPushButton#chipBtn:checked {
    background-color: #0284C7;
    color: #FFFFFF;
    border-color: #38BDF8;
    font-weight: bold;
}

QPushButton#genreChip {
    background-color: #121826;
    color: #CBD5E1;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 17px;
    padding: 8px 18px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#genreChip:hover {
    background-color: #1A2336;
    color: #FFFFFF;
}

QPushButton#genreChip:checked {
    background-color: rgba(14, 165, 233, 0.20);
    color: #E0F2FE;
    border: 1.5px solid #38BDF8;
    font-weight: bold;
}

/* ---------- 分段切换器 ---------- */
QFrame#segmentBox {
    background-color: #07090E;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 11px;
}

QPushButton#segmentBtn {
    background-color: transparent;
    color: #64748B;
    border: none;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#segmentBtn:hover {
    color: #F8FAFC;
}

QPushButton#segmentBtn:checked {
    background-color: #161F30;
    color: #FFFFFF;
    font-weight: bold;
}

/* ---------- 暗色输入控件 ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #0E131F;
    border: 1.5px solid rgba(148, 163, 184, 0.14);
    border-radius: 10px;
    padding: 8px 13px;
    font-size: 14px;
    color: #F8FAFC;
    selection-background-color: #0284C7;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    background-color: #121826;
    border: 1.5px solid #38BDF8;
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
    background-color: #101521;
    border: 1px solid rgba(56, 189, 248, 0.22);
    border-radius: 10px;
    padding: 4px;
    color: #F1F5F9;
    selection-background-color: rgba(14, 165, 233, 0.30);
    selection-color: #FFFFFF;
    font-size: 14px;
    outline: 0;
}

QComboBox QAbstractItemView::item {
    min-height: 34px;
    padding: 4px 10px;
    border-radius: 6px;
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
    border-radius: 6px;
    border: 1.5px solid #334155;
    background-color: #0B0E16;
}

QCheckBox::indicator:hover {
    border-color: #38BDF8;
}

QCheckBox::indicator:checked {
    border: 5px solid #0284C7;
    background-color: #FFFFFF;
}

/* ---------- 暗色现代数据表 ---------- */
QTableWidget {
    background-color: #101521;
    alternate-background-color: #131927;
    border: none;
    font-size: 14px;
    color: #E2E8F0;
    selection-background-color: rgba(14, 165, 233, 0.22);
    selection-color: #FFFFFF;
    outline: 0;
}

QTableWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.06);
}

QHeaderView::section {
    background-color: #101521;
    color: #64748B;
    padding: 12px 12px;
    border: none;
    border-bottom: 1.5px solid rgba(148, 163, 184, 0.10);
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
    background: #1E293B;
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #334155;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMessageBox {
    background-color: #101521;
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
