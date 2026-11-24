# -*- coding: utf-8 -*-
"""界面模块包。"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

if QApplication.instance() is None:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)