# -*- coding: utf-8 -*-
"""
Recomind 智能推荐系统 —— 程序入口
启动流程：初始化数据库与示例数据 -> 登录 -> 主界面。
"""
import os
import sys

# 若项目内存在 vendor 目录（依赖安装到此处），优先加载其中的第三方包
_VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(_VENDOR_DIR) and _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

import config
from ui.styles import STYLE_SHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setStyleSheet(STYLE_SHEET)

    # 初始化数据库与示例数据（幂等操作）
    try:
        from data.seed_data import seed
        from db.init_db import init_database
        init_database()
        seed(force=False)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(
            None,
            "初始化失败",
            "数据库初始化失败，请检查：\n"
            "1. MySQL 服务是否已启动；\n"
            "2. config.py 中数据库密码是否正确。\n\n"
            f"错误信息：{exc}",
        )
        return 1

    from ui.login_dialog import LoginDialog
    from ui.main_window import MainWindow

    # 登录 -> 主界面 -> 退出登录后回到登录界面
    while True:
        login = LoginDialog()
        if login.exec_() != QDialog.Accepted:
            break

        window = MainWindow(login.logged_user)
        window.show()
        app.exec_()

        if not window.want_relogin:
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
