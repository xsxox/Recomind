# -*- coding: utf-8 -*-
"""
AI 观影助手页
暗色影院对话流 + 本地 NLP/RAG & 可选在线 LLM 双模切换 + 内嵌 5 部无边框海报卡片。
"""
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QFrame,
                             QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QScrollArea, QVBoxLayout, QWidget)

from services.assistant_service import (LLM_PRESETS, AssistantService,
                                        load_llm_config, save_llm_config,
                                        test_llm_connection)
from ui.widgets import FlowContainer, MovieCard, clear_layout, make_icon
from utils.logger import get_logger

logger = get_logger("ui.assistant")


class AssistantWorker(QThread):
    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, assistant_service, query, user_id, parent=None):
        super().__init__(parent)
        self.assistant_service = assistant_service
        self.query = query
        self.user_id = user_id

    def run(self):
        try:
            self.finished_ok.emit(self.assistant_service.chat(self.query, user_id=self.user_id))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class LlmConfigDialog(QDialog):
    """暗色在线 LLM 配置弹窗。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("llmConfigDialog")
        self.setWindowTitle("配置在线语言模型 (LLM API)")
        self.setFixedSize(520, 530)
        self.cfg = load_llm_config()
        self._build()

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #CBD5E1; font-size: 13px; font-weight: bold;")
        return lbl

    def _build(self):
        self.setStyleSheet("QDialog#llmConfigDialog { background-color: #10131D; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(12)

        title = QLabel("在线大模型接入配置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        sub = QLabel("关闭或留空时将默认使用本地 NLP+RAG 引擎，零费用离线秒响应。")
        sub.setObjectName("subText")
        sub.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(sub)

        self.enable_cb = QCheckBox("启用在线大模型生成（OpenAI 兼容接口）")
        self.enable_cb.setChecked(bool(self.cfg.get("enabled")))
        self.enable_cb.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.enable_cb)

        layout.addWidget(self._label("模型服务商预设"))
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumHeight(40)
        self.provider_combo.addItems(list(LLM_PRESETS.keys()))
        if self.cfg.get("provider") in LLM_PRESETS:
            self.provider_combo.setCurrentText(self.cfg["provider"])
        self.provider_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addWidget(self.provider_combo)

        layout.addWidget(self._label("API Base URL"))
        self.base_edit = QLineEdit(self.cfg.get("api_base") or "")
        self.base_edit.setMinimumHeight(40)
        self.base_edit.setPlaceholderText("例如：https://api.deepseek.com/v1")
        layout.addWidget(self.base_edit)

        layout.addWidget(self._label("模型名称 (Model)"))
        self.model_edit = QLineEdit(self.cfg.get("model") or "")
        self.model_edit.setMinimumHeight(40)
        self.model_edit.setPlaceholderText("例如：deepseek-chat / qwen-plus")
        layout.addWidget(self.model_edit)

        layout.addWidget(self._label("API Key"))
        self.key_edit = QLineEdit(self.cfg.get("api_key") or "")
        self.key_edit.setMinimumHeight(40)
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("sk-...")
        layout.addWidget(self.key_edit)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        test_btn = QPushButton("测试连接")
        test_btn.setObjectName("secondaryBtn")
        test_btn.setMinimumHeight(40)
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.clicked.connect(self._test)

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("保存配置")
        save_btn.setMinimumHeight(40)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(test_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_preset_changed(self, name):
        base, model = LLM_PRESETS.get(name, ("", ""))
        if base:
            self.base_edit.setText(base)
        if model:
            self.model_edit.setText(model)

    def _current_cfg(self):
        return {
            "enabled": self.enable_cb.isChecked(),
            "provider": self.provider_combo.currentText(),
            "api_base": self.base_edit.text().strip(),
            "api_key": self.key_edit.text().strip(),
            "model": self.model_edit.text().strip(),
        }

    def _test(self):
        ok, msg = test_llm_connection(self._current_cfg())
        if ok:
            QMessageBox.information(self, "测试成功", msg)
        else:
            QMessageBox.warning(self, "连接失败", msg)

    def _save(self):
        save_llm_config(self._current_cfg())
        self.accept()


class AssistantPage(QWidget):
    """AI 观影助手页面。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.assistant_service = AssistantService(main.recommend_service)
        self._worker = None
        self._loading_widget = None
        self._build()
        self._add_welcome()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 26, 36, 22)
        root.setSpacing(14)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("AI 观影助手")
        title.setObjectName("pageTitle")
        subtitle = QLabel("直接用自然语言描述想看的电影，自动理解需求并精选 5 部真实片单")
        subtitle.setObjectName("subText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch()

        self.mode_badge = QLabel()
        self.mode_badge.setObjectName("scoreBadge")
        top.addWidget(self.mode_badge)

        cfg_btn = QPushButton("模型配置")
        cfg_btn.setObjectName("secondaryBtn")
        cfg_btn.setMinimumHeight(38)
        cfg_btn.setCursor(Qt.PointingHandCursor)
        cfg_btn.clicked.connect(self._open_config)
        top.addWidget(cfg_btn)

        clear_btn = QPushButton("清空对话")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.setMinimumHeight(38)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_chat)
        top.addWidget(clear_btn)
        root.addLayout(top)

        self._refresh_mode_badge()

        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(8)
        p_lbl = QLabel("快速体验：")
        p_lbl.setObjectName("subText")
        prompt_row.addWidget(p_lbl)
        for text in [
            "我想看一个经典的科幻电影",
            "推荐5部轻松搞笑的高分动画",
            "最近想看烧脑反转的悬疑犯罪片",
            "类似星际穿越的太空硬科幻",
        ]:
            chip = QPushButton(text)
            chip.setObjectName("chipBtn")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _c, t=text: self._send_text(t))
            prompt_row.addWidget(chip)
        prompt_row.addStretch()
        root.addLayout(prompt_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        chat_body = QWidget()
        chat_body.setObjectName("assistantChatBody")
        chat_body.setStyleSheet("QWidget#assistantChatBody { background: transparent; }")
        self.chat_layout = QVBoxLayout(chat_body)
        self.chat_layout.setContentsMargins(2, 6, 8, 12)
        self.chat_layout.setSpacing(16)
        self.chat_layout.addStretch()
        self.scroll.setWidget(chat_body)
        root.addWidget(self.scroll, 1)

        dock = QFrame()
        dock.setObjectName("spotlightBar")
        dock_layout = QHBoxLayout(dock)
        dock_layout.setContentsMargins(16, 7, 8, 7)
        dock_layout.setSpacing(10)

        bot_icon = QLabel()
        bot_icon.setPixmap(make_icon("bot", "#818CF8", 20).pixmap(20, 20))
        dock_layout.addWidget(bot_icon)

        self.input_edit = QLineEdit()
        self.input_edit.setObjectName("spotlightInput")
        self.input_edit.setMinimumHeight(40)
        self.input_edit.setPlaceholderText("告诉我你想看什么类型的电影、心情、年代或参考片名...")
        self.input_edit.returnPressed.connect(self._on_send)
        dock_layout.addWidget(self.input_edit, 1)

        self.send_btn = QPushButton("发送推荐")
        self.send_btn.setMinimumHeight(40)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send)
        dock_layout.addWidget(self.send_btn)
        root.addWidget(dock)

    def _refresh_mode_badge(self):
        cfg = load_llm_config()
        if cfg.get("enabled") and (cfg.get("api_key") or "").strip():
            self.mode_badge.setText(f"在线 LLM · {cfg.get('model') or 'API'}")
        else:
            self.mode_badge.setText("本地 NLP+RAG 引擎")

    def _open_config(self):
        dlg = LlmConfigDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_mode_badge()

    def _clear_chat(self):
        self.assistant_service.reset_session()
        clear_layout(self.chat_layout)
        self.chat_layout.addStretch()
        self._add_welcome()

    def _add_welcome(self):
        card = QFrame()
        card.setObjectName("panel")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 18, 22, 18)
        cl.setSpacing(8)

        head = QLabel("你好！我是 Recomind AI 观影助手")
        head.setStyleSheet("font-size: 16px; font-weight: bold; color: #A5B4FC;")
        body = QLabel(
            "你可以像跟朋友聊天一样告诉我需求：\n"
            "• 题材与情绪：「我想看一个经典的科幻电影」「最近心情不好，想看轻松搞笑的高分喜剧」\n"
            "• 年代与过滤：「90年代经典动作片」「近几年的动画片，不要恐怖元素」\n"
            "• 参考相似电影：「推荐5部类似《星际穿越》的太空科幻片」"
        )
        body.setWordWrap(True)
        body.setStyleSheet("color: #CBD5E1; font-size: 14px;")
        cl.addWidget(head)
        cl.addWidget(body)
        self._insert_chat_widget(card)

    def _insert_chat_widget(self, widget):
        idx = max(0, self.chat_layout.count() - 1)
        self.chat_layout.insertWidget(idx, widget)
        QTimer.singleShot(40, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _add_user_bubble(self, text):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(100, 0, 0, 0)
        rl.addStretch()

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setStyleSheet(
            "background-color: #2DD4BF; color: #06211B; font-size: 15px; font-weight: 500;"
            "padding: 12px 18px; border-radius: 16px;"
        )
        rl.addWidget(bubble)
        self._insert_chat_widget(row)

    def _add_loading_bubble(self):
        lbl = QLabel("正在解析自然语言意图并检索全库电影…")
        lbl.setObjectName("panel")
        lbl.setStyleSheet(
            "QLabel#panel { background-color: #101521; border: 1px solid rgba(148, 163, 184, 0.12);"
            "border-radius: 14px; padding: 14px 18px; color: #94A3B8; font-size: 14px; }"
        )
        self._loading_widget = lbl
        self._insert_chat_widget(lbl)

    def _remove_loading_bubble(self):
        if self._loading_widget is not None:
            self._loading_widget.setParent(None)
            self._loading_widget.deleteLater()
            self._loading_widget = None

    def _add_assistant_card(self, res):
        card = QFrame()
        card.setObjectName("panel")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 18, 22, 20)
        cl.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        badge = QLabel(res.get("model_name") or "AI 推荐")
        badge.setStyleSheet(
            "background-color: rgba(14, 165, 233, 0.16); color: #38BDF8; border-radius: 6px;"
            "padding: 3px 10px; font-size: 12px; font-weight: bold;"
        )
        top_row.addWidget(badge)

        for tag in (res.get("intent_tags") or []):
            t_lbl = QLabel(tag)
            t_lbl.setStyleSheet(
                "background-color: #141B2A; color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.12); border-radius: 6px;"
                "padding: 3px 9px; font-size: 12px;"
            )
            top_row.addWidget(t_lbl)
        top_row.addStretch()
        cl.addLayout(top_row)

        reply_lbl = QLabel(res.get("reply") or "")
        reply_lbl.setWordWrap(True)
        reply_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reply_lbl.setStyleSheet("color: #E2E8F0; font-size: 15px;")
        cl.addWidget(reply_lbl)

        movies = res.get("movies") or []
        if movies:
            flow_wrap = FlowContainer(h_spacing=16, v_spacing=16, margin=0)
            for movie, score in movies:
                mcard = MovieCard(movie, score=score, compact=True)
                mcard.clicked.connect(self.main.open_detail)
                flow_wrap.flow.addWidget(mcard)
            cl.addWidget(flow_wrap)

            # 底部操作栏：提供一键“换一批”快捷动作
            action_row = QHBoxLayout()
            action_row.setContentsMargins(0, 4, 0, 0)
            action_row.setSpacing(10)

            refresh_rec_btn = QPushButton("↻ 换一批推荐")
            refresh_rec_btn.setObjectName("chipBtn")
            refresh_rec_btn.setCursor(Qt.PointingHandCursor)
            refresh_rec_btn.clicked.connect(lambda: self._send_text("换一批"))
            action_row.addWidget(refresh_rec_btn)

            more_hint = QLabel("💡 提示：可继续输入“只要90年代的”、“不要太老的”、“再加点搞笑”等追加条件")
            more_hint.setStyleSheet("color: #64748B; font-size: 12px;")
            action_row.addWidget(more_hint)
            action_row.addStretch()
            cl.addLayout(action_row)

        self._insert_chat_widget(card)

    def _send_text(self, text):
        self.input_edit.setText(text)
        self._on_send()

    def _on_send(self):
        if self._worker is not None and self._worker.isRunning():
            return
        query = self.input_edit.text().strip()
        if not query:
            return
        self.input_edit.clear()
        self._add_user_bubble(query)
        self._add_loading_bubble()
        self.send_btn.setEnabled(False)
        self.send_btn.setText("分析中…")

        user = self.main.get_user()
        uid = user.id if user else None
        self._worker = AssistantWorker(self.assistant_service, query, uid, self)
        self._worker.finished_ok.connect(self._on_reply)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_reply(self, res):
        self._remove_loading_bubble()
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送推荐")
        self._add_assistant_card(res)

    def _on_failed(self, err):
        self._remove_loading_bubble()
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送推荐")
        QMessageBox.critical(self, "推荐出错", f"分析失败：{err}")