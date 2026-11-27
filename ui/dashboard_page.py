# -*- coding: utf-8 -*-
"""
算法分析仪表盘页面 (Algorithm Analysis Dashboard)
==================================================
毕设核心展示页面，包含：
  1. 实时离线评估（Precision/Recall/NDCG/MRR/Coverage/Diversity）
  2. 多算法对比雷达图（通过 matplotlib 嵌入 PyQt5）
  3. 评分分布直方图
  4. 情感分析分布饼图
  5. 推荐解释性说明

这个页面是区分毕业设计水平的关键！
"""
from __future__ import annotations

import threading
from datetime import datetime

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QScrollArea,
                             QSizePolicy, QSplitter, QVBoxLayout, QWidget,
                             QProgressBar, QTextEdit)

from utils.logger import get_logger

logger = get_logger("ui.dashboard")


# ------------------------------------------------------------------
# matplotlib 嵌入 Qt 辅助函数
# ------------------------------------------------------------------

def _make_figure(figsize=(5, 4)):
    """创建 matplotlib Figure 并嵌入 Qt 画布。"""
    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas  # type: ignore
        from matplotlib.figure import Figure  # type: ignore
        import matplotlib
        matplotlib.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans", "Arial Unicode MS"]
        matplotlib.rcParams["axes.unicode_minus"] = False
        fig = Figure(figsize=figsize, tight_layout=True)
        canvas = Canvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return fig, canvas
    except Exception:
        return None, None


# ------------------------------------------------------------------
# 后台评估线程
# ------------------------------------------------------------------

class EvalThread(QThread):
    finished = pyqtSignal(object)   # EvaluationReport
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, k=10, ratio=0.2, seed=42):
        super().__init__()
        self.k = k
        self.ratio = ratio
        self.seed = seed

    def run(self):
        try:
            self.progress.emit("正在加载数据...")
            from evaluation.dashboard import run_full_evaluation
            self.progress.emit("正在运行算法评估（约 10-30 秒）...")
            report = run_full_evaluation(k=self.k, ratio=self.ratio, seed=self.seed)
            self.finished.emit(report)
        except Exception as exc:
            logger.exception("评估线程异常")
            self.error.emit(str(exc))


# ------------------------------------------------------------------
# 指标卡片
# ------------------------------------------------------------------

class MetricCard(QFrame):
    """单个指标展示卡片。"""
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#6366F1"):
        super().__init__()
        self.setObjectName("panel")
        self.setMinimumWidth(130)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        layout.addWidget(t)

        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(v)

        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet("color: #64748B; font-size: 11px;")
            layout.addWidget(s)


# ------------------------------------------------------------------
# 主仪表盘页
# ------------------------------------------------------------------

class DashboardPage(QWidget):
    """算法评估与数据可视化仪表盘。"""

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self._report = None
        self._eval_thread: EvalThread | None = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        root = QVBoxLayout(body)
        root.setContentsMargins(36, 26, 36, 32)
        root.setSpacing(24)

        # 标题行
        hdr = QHBoxLayout()
        title = QLabel("🔬  算法分析仪表盘")
        title.setObjectName("pageTitle")
        hdr.addWidget(title)
        hdr.addStretch()

        self.run_btn = QPushButton("▶  运行离线评估")
        self.run_btn.setObjectName("primaryBtn")
        self.run_btn.setMinimumHeight(42)
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self._start_eval)
        hdr.addWidget(self.run_btn)
        root.addLayout(hdr)

        # 说明文字
        desc = QLabel(
            "对五种推荐算法进行留一法（Leave-One-Out）离线评估，"
            "评估指标包含 Precision@K、Recall@K、NDCG@K、MRR@K、Coverage 和 Diversity。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        root.addWidget(desc)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #101518; border-radius: 2px; }"
            "QProgressBar::chunk { background: #2DD4BF; border-radius: 2px; }"
        )
        root.addWidget(self.progress_bar)

        self.status_lbl = QLabel("点击「运行离线评估」开始对比各算法性能")
        self.status_lbl.setStyleSheet("color: #64748B; font-size: 13px;")
        root.addWidget(self.status_lbl)

        # 指标卡片区（评估后填充）
        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(12)
        root.addLayout(self.cards_row)

        # 图表区（左：雷达图，右：柱状图）
        self.chart_row = QHBoxLayout()
        self.chart_row.setSpacing(16)
        root.addLayout(self.chart_row)

        # 算法比较文字表
        tbl_title = QLabel("算法性能对比详表")
        tbl_title.setObjectName("sectionTitle")
        root.addWidget(tbl_title)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(220)
        self.result_text.setStyleSheet(
            "QTextEdit { background: #0B0E16; color: #CBD5E1; font-family: 'Consolas', monospace; "
            "font-size: 13px; border: 1px solid rgba(148,163,184,0.10); border-radius: 12px; padding: 14px; }"
        )
        self.result_text.setPlainText("评估结果将在此显示...")
        root.addWidget(self.result_text)

        # 评分分布图
        rating_title = QLabel("用户评分分布")
        rating_title.setObjectName("sectionTitle")
        root.addWidget(rating_title)
        self.rating_chart_frame = QFrame()
        self.rating_chart_frame.setObjectName("panel")
        self.rating_chart_frame.setMinimumHeight(220)
        rc_layout = QVBoxLayout(self.rating_chart_frame)
        self._init_rating_chart(rc_layout)
        root.addWidget(self.rating_chart_frame)

        root.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # 评分分布图（启动时即绘制）
    # ------------------------------------------------------------------

    def _init_rating_chart(self, layout: QVBoxLayout):
        fig, canvas = _make_figure(figsize=(8, 2.5))
        if fig is None:
            lbl = QLabel("需要安装 matplotlib 以显示图表")
            lbl.setStyleSheet("color: #64748B;")
            layout.addWidget(lbl)
            return
        self._rating_fig = fig
        self._rating_canvas = canvas
        layout.addWidget(canvas)
        self._draw_rating_chart()

    def _draw_rating_chart(self):
        try:
            from db.connection import execute_query
            rows = execute_query("SELECT score, COUNT(*) as cnt FROM ratings GROUP BY score ORDER BY score")
            scores = [r["score"] for r in rows]
            counts = [r["cnt"] for r in rows]
        except Exception:
            scores, counts = [], []

        ax = self._rating_fig.add_subplot(111)
        ax.clear()
        ax.set_facecolor("#101521")
        self._rating_fig.patch.set_facecolor("#101521")

        if scores:
            bars = ax.bar(scores, counts, color=["#0369A1", "#0284C7", "#0EA5E9", "#38BDF8", "#22D3EE"],
                         edgecolor="#1E293B", linewidth=0.8, width=0.58)
            for bar, cnt in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        str(cnt), ha="center", va="bottom", color="#E2E8F0", fontsize=10)
        else:
            ax.text(0.5, 0.5, "暂无评分数据", transform=ax.transAxes,
                    ha="center", va="center", color="#64748B", fontsize=12)

        ax.set_xlabel("评分", color="#64748B", fontsize=11)
        ax.set_ylabel("评分次数", color="#64748B", fontsize=11)
        ax.set_title("用户评分分布直方图", color="#F8FAFC", fontsize=13, fontweight="bold")
        ax.tick_params(colors="#64748B")
        ax.spines["bottom"].set_color("#1E293B")
        ax.spines["left"].set_color("#1E293B")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        self._rating_canvas.draw()

    # ------------------------------------------------------------------
    # 运行评估
    # ------------------------------------------------------------------

    def _start_eval(self):
        if self._eval_thread and self._eval_thread.isRunning():
            return
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳  评估中...")
        self.progress_bar.setVisible(True)
        self.status_lbl.setText("正在初始化评估环境...")

        self._eval_thread = EvalThread(k=10, ratio=0.2, seed=42)
        self._eval_thread.finished.connect(self._on_eval_done)
        self._eval_thread.error.connect(self._on_eval_error)
        self._eval_thread.progress.connect(self.status_lbl.setText)
        self._eval_thread.start()

    def _on_eval_done(self, report):
        self._report = report
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  重新评估")
        self.status_lbl.setText(
            f"评估完成 | {report.n_users} 用户 | {report.n_ratings} 评分 | "
            f"最佳算法：{report.best_algorithm().name if report.best_algorithm() else 'N/A'}"
        )
        self._render_results(report)

    def _on_eval_error(self, msg: str):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  运行离线评估")
        self.status_lbl.setText(f"评估失败：{msg}")
        self.result_text.setPlainText(f"错误：{msg}\n\n请确保数据库已启动且有足够评分数据。")

    # ------------------------------------------------------------------
    # 渲染结果
    # ------------------------------------------------------------------

    def _render_results(self, report):
        # 清空旧卡片
        while self.cards_row.count():
            w = self.cards_row.takeAt(0)
            if w.widget():
                w.widget().deleteLater()
        while self.chart_row.count():
            w = self.chart_row.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        # 数据概览卡片
        best = report.best_algorithm()
        cards_data = [
            ("电影总数", str(report.n_movies), "部影片", "#38BDF8"),
            ("参与用户", str(report.n_users), "位测试用户", "#10B981"),
            ("评分总数", str(report.n_ratings), "条评分记录", "#22D3EE"),
            ("最佳 NDCG@10", f"{best.ndcg:.3f}" if best else "N/A", best.name if best else "", "#818CF8"),
            ("最佳 MRR@10", f"{best.mrr:.3f}" if best else "N/A", "平均倒数排名", "#0EA5E9"),
        ]
        for title, value, subtitle, color in cards_data:
            card = MetricCard(title, value, subtitle, color)
            self.cards_row.addWidget(card)
        self.cards_row.addStretch()

        # 雷达图
        self._draw_radar(report)
        # 柱状图对比
        self._draw_bar_comparison(report)

        # 文字表格
        lines = []
        header = f"{'算法':<30} {'Hit@K':>7} {'P@K':>7} {'R@K':>7} {'NDCG@K':>8} {'MRR@K':>7} {'Cov':>6} {'Div':>6} {'ms':>7}"
        lines.append(header)
        lines.append("─" * len(header))
        all_algos = report.algorithms + (
            [report.baseline_popularity, report.baseline_random]
            if report.baseline_popularity else []
        )
        for a in all_algos:
            if a is None:
                continue
            lines.append(
                f"{a.name:<30} {a.hit_rate:>7.3f} {a.precision:>7.3f} {a.recall:>7.3f} "
                f"{a.ndcg:>8.3f} {a.mrr:>7.3f} {a.coverage:>6.3f} {a.diversity:>6.3f} {a.runtime_ms:>7.0f}"
            )
        self.result_text.setPlainText("\n".join(lines))

        # 刷新评分图
        self._draw_rating_chart()

    def _draw_radar(self, report):
        """绘制多算法雷达图。"""
        fig, canvas = _make_figure(figsize=(5, 4))
        if fig is None:
            lbl = QLabel("需安装 matplotlib")
            lbl.setStyleSheet("color: #64748B;")
            self.chart_row.addWidget(lbl)
            return

        import numpy as np
        metrics = ["Precision", "Recall", "NDCG", "MRR", "Coverage", "Diversity"]
        N = len(metrics)
        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        angles += angles[:1]

        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor("#0B0E16")
        fig.patch.set_facecolor("#101521")

        colors = ["#38BDF8", "#10B981", "#22D3EE", "#818CF8", "#60A5FA"]
        for i, algo in enumerate(report.algorithms):
            values = [algo.precision, algo.recall, algo.ndcg, algo.mrr, algo.coverage, algo.diversity]
            values += values[:1]
            ax.plot(angles, values, linewidth=1.5, linestyle="solid",
                    color=colors[i % len(colors)], label=algo.name.split("(")[0].strip())
            ax.fill(angles, values, alpha=0.08, color=colors[i % len(colors)])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, color="#CBD5E1", size=10)
        ax.set_ylim(0, 1)
        ax.tick_params(colors="#64748B")
        ax.spines["polar"].set_color("#1E293B")
        ax.yaxis.set_tick_params(labelleft=False)
        ax.set_title("算法性能雷达图", color="#F8FAFC", pad=15, fontsize=12, fontweight="bold")
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1),
                  fontsize=9, labelcolor="#CBD5E1", framealpha=0,
                  facecolor="#101521")
        canvas.draw()

        frame = QFrame()
        frame.setObjectName("panel")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.addWidget(canvas)
        self.chart_row.addWidget(frame, 1)

    def _draw_bar_comparison(self, report):
        """绘制 NDCG@K 对比柱状图。"""
        fig, canvas = _make_figure(figsize=(5, 4))
        if fig is None:
            return

        import numpy as np

        ax = fig.add_subplot(111)
        ax.set_facecolor("#101521")
        fig.patch.set_facecolor("#101521")

        names = [a.name.split("(")[0].strip()[:10] for a in report.algorithms]
        ndcgs = [a.ndcg for a in report.algorithms]
        colors = ["#38BDF8", "#10B981", "#22D3EE", "#818CF8", "#0EA5E9"]

        x = np.arange(len(names))
        bars = ax.bar(x, ndcgs, color=colors[:len(names)], edgecolor="#1E293B", width=0.55)
        for bar, v in zip(bars, ndcgs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{v:.3f}", ha="center", va="bottom", color="#F8FAFC", fontsize=10)

        # 基线
        if report.baseline_popularity:
            ax.axhline(report.baseline_popularity.ndcg, color="#94A3B8", linestyle="--",
                       linewidth=1, label=f"热门基线 {report.baseline_popularity.ndcg:.3f}")
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=15, ha="right", color="#CBD5E1", fontsize=9)
        ax.set_ylabel("NDCG@K", color="#64748B")
        ax.set_title("各算法 NDCG@K 对比", color="#F8FAFC", fontsize=12, fontweight="bold")
        ax.tick_params(colors="#64748B")
        ax.spines["bottom"].set_color("#1E293B")
        ax.spines["left"].set_color("#1E293B")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if report.baseline_popularity:
            ax.legend(fontsize=9, labelcolor="#94A3B8", framealpha=0)
        canvas.draw()

        frame = QFrame()
        frame.setObjectName("panel")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.addWidget(canvas)
        self.chart_row.addWidget(frame, 1)
