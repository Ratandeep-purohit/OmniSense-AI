"""OmniSense AI desktop product UI wired to the real local runtime."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..app import health_check
from ..config import load_config
from ..desktop_product_runtime import DesktopProductRuntime
from ..integration.models import PipelineResult, PipelineStatus
from ..safety_permission.models import PermissionDecision
from .styles import APP_STYLE


class _TaskSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class _RuntimeTask(QRunnable):
    def __init__(self, runtime: DesktopProductRuntime, intent: str) -> None:
        super().__init__()
        self.runtime = runtime
        self.intent = intent
        self.signals = _TaskSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.runtime.run(self.intent))
        except Exception as exc:
            self.signals.failed.emit(f"{type(exc).__name__}: {exc}")


class _SnapshotTask(QRunnable):
    def __init__(self, runtime: DesktopProductRuntime) -> None:
        super().__init__()
        self.runtime = runtime
        self.signals = _TaskSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.runtime.snapshot())
        except Exception as exc:
            self.signals.failed.emit(f"{type(exc).__name__}: {exc}")


class OmniSenseWindow(QMainWindow):
    """Main OmniSense desktop product window."""

    NAV = [
        ("Overview", "overview"),
        ("Assistant", "assistant"),
        ("Live Context", "context"),
        ("Action Center", "actions"),
        ("Safety & Control", "safety"),
        ("Diagnostics", "diagnostics"),
        ("Settings", "settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("OmniSense AI")
        self.setMinimumSize(1180, 720)
        self.resize(1440, 860)
        self.setStyleSheet(APP_STYLE)
        self._pool = QThreadPool.globalInstance()
        self._runtime: DesktopProductRuntime | None = None
        self._last_result: PipelineResult | None = None
        self._nav_buttons: list[QPushButton] = []
        self._pages: dict[str, QWidget] = {}
        self._build_window()
        self._refresh_health()

    # ---------- shared UI helpers ----------

    @staticmethod
    def _label(text: str, object_name: str = "") -> QLabel:
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        return label

    def _card(self, title: str, body: str, metric: str | None = None) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 15, 16, 15)
        layout.setSpacing(6)
        layout.addWidget(self._label(title, "section"))
        if metric is not None:
            layout.addWidget(self._label(metric, "metric"))
        text = self._label(body, "muted")
        text.setWordWrap(True)
        layout.addWidget(text)
        return card

    def _metric_card(self, title: str, value: str, detail: str) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        layout.addWidget(self._label(title.upper(), "metricCaption"))
        layout.addWidget(self._label(value, "metric"))
        layout.addWidget(self._label(detail, "metricCaption"))
        return card

    def _section_header(self, title: str, action_text: str | None = None, action=None) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label(title, "section"))
        layout.addStretch()
        if action_text and action:
            button = QPushButton(action_text)
            button.setObjectName("secondary")
            button.clicked.connect(action)
            layout.addWidget(button)
        return row

    def _page(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(34, 28, 34, 28)
        outer.setSpacing(16)
        outer.addWidget(self._label(title, "pageTitle"))
        outer.addWidget(self._label(subtitle, "pageSub"))
        return page, outer

    # ---------- shell ----------

    def _build_window(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 18, 16, 16)
        side.setSpacing(3)

        brand_row = QHBoxLayout()
        mark = QFrame()
        mark.setObjectName("brandMark")
        mark.setFixedSize(34, 34)
        mark_layout = QVBoxLayout(mark)
        mark_layout.setContentsMargins(0, 0, 0, 0)
        mark_label = self._label("O")
        mark_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark_label.setStyleSheet("color:white; font-size:18px; font-weight:700;")
        mark_layout.addWidget(mark_label)
        brand_row.addWidget(mark)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_text.addWidget(self._label("OmniSense", "brand"))
        brand_text.addWidget(self._label("Desktop Intelligence", "brandSub"))
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        side.addLayout(brand_row)
        side.addSpacing(24)
        side.addWidget(self._label("WORKSPACE", "workspace"))
        side.addSpacing(5)

        for label, key in self.NAV:
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            self._nav_buttons.append(button)
            side.addWidget(button)

        side.addStretch()

        mode_row = QHBoxLayout()
        mode_row.addWidget(self._label("●", "statusDot"))
        self._mode_label = self._label("Safe mode", "status")
        mode_row.addWidget(self._mode_label)
        mode_row.addStretch()
        side.addLayout(mode_row)
        side.addWidget(self._label("OmniSense AI  •  0.1.0", "brandSub"))

        self.stack = QStackedWidget()
        for key, page in self._make_pages().items():
            self._pages[key] = page
            self.stack.addWidget(page)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready  •  Local runtime  •  Automation disabled")
        self.show_page("overview")

    def show_page(self, key: str) -> None:
        """Switch the visible workspace page and keep sidebar state in sync."""
        if key not in self._pages:
            raise KeyError(f"Unknown UI page: {key}")

        self.stack.setCurrentWidget(self._pages[key])
        for button, (_, button_key) in zip(self._nav_buttons, self.NAV):
            button.setChecked(button_key == key)

    def _make_pages(self) -> dict[str, QWidget]:
        return {
            "overview": self._overview_page(),
            "assistant": self._assistant_page(),
            "context": self._context_page(),
            "actions": self._actions_page(),
            "safety": self._safety_page(),
            "diagnostics": self._diagnostics_page(),
            "settings": self._settings_page(),
        }

    # ---------- pages ----------

    def _overview_page(self) -> QWidget:
        page, outer = self._page(
            "Overview",
            "A live control surface for perception, reasoning and safe action.",
        )
        hero = QFrame()
        hero.setObjectName("card")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        copy = QVBoxLayout()
        copy.setSpacing(5)
        copy.addWidget(self._label("LOCAL DESKTOP AGENT", "eyebrow"))
        copy.addWidget(self._label("Your desktop, understood.", "section"))
        copy.addWidget(self._label(
            "Observe context, prepare an action, enforce policy and verify the result.",
            "muted",
        ))
        hero_layout.addLayout(copy, 1)
        open_button = QPushButton("Open Assistant")
        open_button.setObjectName("primary")
        open_button.clicked.connect(lambda: self.show_page("assistant"))
        hero_layout.addWidget(open_button)
        outer.addWidget(hero)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        metrics.addWidget(self._metric_card("Runtime", "Healthy", "Core services available"))
        self._automation_metric = self._metric_card("Automation", "Disabled", "Explicit opt-in")
        metrics.addWidget(self._automation_metric)
        metrics.addWidget(self._metric_card("Security", "Protected", "Observed input is untrusted"))
        metrics.addWidget(self._metric_card("Verification", "Ready", "Post-action checks"))
        outer.addLayout(metrics)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        left = QFrame()
        left.setObjectName("card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(17, 16, 17, 16)
        left_layout.addWidget(self._section_header("System activity", "Refresh", self._refresh_health))
        for title, detail in [
            ("Runtime initialized", "OmniSense core is available locally."),
            ("Safety boundary loaded", "Action requests remain gated."),
            ("Capture session", "Idle — capture starts only for an explicit context request."),
        ]:
            row = QHBoxLayout()
            row.addWidget(self._label("●", "statusDot"))
            text = QVBoxLayout()
            text.setSpacing(1)
            text.addWidget(self._label(title, "value"))
            text.addWidget(self._label(detail, "muted"))
            row.addLayout(text, 1)
            left_layout.addLayout(row)
        left_layout.addStretch()

        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(17, 16, 17, 16)
        right_layout.addWidget(self._label("Control model", "section"))
        right_layout.addWidget(self._label(
            "Context → Security → Plan → Safety → Automation → Verify", "value"
        ))
        right_layout.addWidget(self._label(
            "The UI is only a client. Execution remains inside the existing Phase 17 pipeline.",
            "muted",
        ))
        right_layout.addStretch()
        columns.addWidget(left, 3)
        columns.addWidget(right, 2)
        outer.addLayout(columns)
        outer.addStretch()
        return page

    def _assistant_page(self) -> QWidget:
        page, outer = self._page(
            "Assistant",
            "Describe what you want done. OmniSense will inspect context before planning.",
        )

        toolbar = QHBoxLayout()
        toolbar.addWidget(self._label("SESSION", "metricCaption"))
        self._session_label = self._label("Local • Safe mode", "value")
        toolbar.addWidget(self._session_label)
        toolbar.addStretch()
        self._context_label = self._label("Context: not connected", "muted")
        toolbar.addWidget(self._context_label)
        outer.addLayout(toolbar)

        shell = QFrame()
        shell.setObjectName("card")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(18, 18, 18, 18)
        shell_layout.setSpacing(12)

        self._history = QPlainTextEdit()
        self._history.setReadOnly(True)
        self._history.setPlainText(
            "OmniSense AI\n"
            "────────────────────────────────────────\n"
            "Ready. Try:\n"
            "  • open Microsoft Word\n"
            "  • open Notepad\n"
            "  • open Calculator\n\n"
            "Automation is OFF by default. The first executable request asks for "
            "explicit permission to enable desktop control."
        )
        shell_layout.addWidget(self._history, 1)

        composer = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Describe a task or ask a question…")
        self._send = QPushButton("Run")
        self._send.setObjectName("primary")
        self._send.clicked.connect(self._submit_request)
        self._input.returnPressed.connect(self._submit_request)
        composer.addWidget(self._input, 1)
        composer.addWidget(self._send)
        shell_layout.addLayout(composer)
        outer.addWidget(shell, 1)
        return page

    def _context_page(self) -> QWidget:
        page, outer = self._page(
            "Live Context",
            "Current desktop evidence used by planning and safety.",
        )
        top = QHBoxLayout()
        self._app_metric = self._metric_card("Application", "Idle", "No snapshot")
        self._window_metric = self._metric_card("Window", "—", "No snapshot")
        self._fresh_metric = self._metric_card("Freshness", "—", "No snapshot")
        self._evidence_metric = self._metric_card("Evidence", "0", "Items available")
        for widget in (self._app_metric, self._window_metric, self._fresh_metric, self._evidence_metric):
            top.addWidget(widget)
        outer.addLayout(top)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.addWidget(self._section_header("Evidence stream", "Refresh context", self._request_snapshot))
        self._context_text = QPlainTextEdit()
        self._context_text.setReadOnly(True)
        self._context_text.setPlainText(
            "No context snapshot yet. Click “Refresh context” to inspect the active desktop."
        )
        layout.addWidget(self._context_text, 1)
        outer.addWidget(card, 1)
        return page

    def _actions_page(self) -> QWidget:
        page, outer = self._page(
            "Action Center",
            "Every executable request leaves a trace of planning, policy and verification.",
        )
        stats = QHBoxLayout()
        self._pending_metric = self._metric_card("Last status", "Idle", "No action yet")
        self._plan_metric = self._metric_card("Plan", "—", "Not created")
        self._verify_metric = self._metric_card("Verification", "—", "Not run")
        stats.addWidget(self._pending_metric)
        stats.addWidget(self._plan_metric)
        stats.addWidget(self._verify_metric)
        stats.addStretch()
        outer.addLayout(stats)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.addWidget(self._section_header("Latest action"))
        self._action_text = QPlainTextEdit()
        self._action_text.setReadOnly(True)
        self._action_text.setPlainText("No action has been submitted.")
        layout.addWidget(self._action_text, 1)
        outer.addWidget(card, 1)
        return page

    def _safety_page(self) -> QWidget:
        page, outer = self._page(
            "Safety & Control",
            "The boundary between intelligence and desktop authority.",
        )
        banner = QFrame()
        banner.setObjectName("card")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(17, 14, 17, 14)
        banner_layout.addWidget(self._label("●", "statusDot"))
        self._safety_banner = self._label("Safe mode is active", "value")
        banner_layout.addWidget(self._safety_banner)
        banner_layout.addStretch()
        self._safety_automation = self._label("Automation disabled", "muted")
        banner_layout.addWidget(self._safety_automation)
        outer.addWidget(banner)

        policies = [
            ("Execution authority", "OPT-IN", "Automation starts disabled."),
            ("Risk gating", "ENFORCED", "Medium/high-risk actions require confirmation."),
            ("High consequence", "BLOCKED", "Dangerous intents are rejected."),
            ("Context freshness", "BOUNDED", "Stale context cannot authorize action."),
            ("Verification", "REQUIRED", "Successful execution needs post-action evidence."),
            ("Input trust", "UNTRUSTED", "Screen content is evidence, not instructions."),
        ]
        grid = QHBoxLayout()
        for title, status, detail in policies:
            grid.addWidget(self._card(title, detail, status))
        outer.addLayout(grid)
        outer.addStretch()
        return page

    def _diagnostics_page(self) -> QWidget:
        page, outer = self._page(
            "Diagnostics",
            "Health, runtime configuration and integration checks.",
        )
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.addWidget(self._section_header("Runtime health"))
        self._diagnostic_text = QPlainTextEdit()
        self._diagnostic_text.setReadOnly(True)
        layout.addWidget(self._diagnostic_text, 1)
        refresh = QPushButton("Run diagnostics")
        refresh.setObjectName("primary")
        refresh.clicked.connect(self._refresh_health)
        layout.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(card, 1)
        return page

    def _settings_page(self) -> QWidget:
        page, outer = self._page(
            "Settings",
            "Local product controls. Automation remains explicit and reversible.",
        )
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 17, 17, 17)
        layout.setSpacing(12)
        layout.addWidget(self._label("Desktop capabilities", "section"))

        self._automation_check = QCheckBox("Allow desktop automation for this session")
        self._automation_check.setChecked(False)
        self._automation_check.toggled.connect(self._toggle_automation)
        layout.addWidget(self._automation_check)

        capture = QCheckBox("Allow screen capture for context inspection")
        capture.setChecked(True)
        capture.setEnabled(False)
        layout.addWidget(capture)

        layout.addWidget(self._label(
            "Opening an app, typing, clicking or using hotkeys can affect the desktop. "
            "OmniSense keeps those operations behind the existing safety gate.",
            "muted",
        ))
        outer.addWidget(card)
        outer.addStretch()
        return page

    # ---------- runtime ----------

    def _ensure_runtime(self) -> DesktopProductRuntime:
        if self._runtime is None:
            self._runtime = DesktopProductRuntime()
        return self._runtime

    def _toggle_automation(self, enabled: bool) -> None:
        try:
            runtime = self._ensure_runtime()
            runtime.set_automation_enabled(enabled)
            state = "enabled" if enabled else "disabled"
            self._mode_label.setText("Active mode" if enabled else "Safe mode")
            self._safety_automation.setText(
                "Automation enabled for this session" if enabled else "Automation disabled"
            )
            self._session_label.setText(
                "Local • Automation enabled" if enabled else "Local • Safe mode"
            )
            self.statusBar().showMessage(f"Desktop automation {state}")
        except Exception as exc:
            self._automation_check.blockSignals(True)
            self._automation_check.setChecked(not enabled)
            self._automation_check.blockSignals(False)
            QMessageBox.critical(self, "Automation setup failed", str(exc))

    def _submit_request(self) -> None:
        intent = self._input.text().strip()
        if not intent or self._send.isEnabled() is False:
            return

        runtime = self._ensure_runtime()
        if not runtime.automation_enabled and any(
            phrase in intent.casefold()
            for phrase in ("open ", "launch ", "start ", "click ", "type ", "write ", "press ")
        ):
            choice = QMessageBox.question(
                self,
                "Enable desktop automation?",
                "This request can control the desktop. Enable automation for this session?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice is not QMessageBox.StandardButton.Yes:
                self._append_chat("OmniSense", "Request cancelled. Automation remains disabled.")
                return
            self._automation_check.blockSignals(True)
            self._automation_check.setChecked(True)
            self._automation_check.blockSignals(False)
            runtime.set_automation_enabled(True)
            self._mode_label.setText("Active mode")
            self._session_label.setText("Local • Automation enabled")
            self._safety_automation.setText("Automation enabled for this session")

        self._append_chat("You", intent)
        self._input.clear()
        self._send.setEnabled(False)
        self._send.setText("Working…")
        self.statusBar().showMessage("Capturing context → planning → safety → execution → verification")
        task = _RuntimeTask(runtime, intent)
        task.signals.finished.connect(self._request_finished)
        task.signals.failed.connect(self._request_failed)
        self._pool.start(task)

    def _request_finished(self, result: PipelineResult) -> None:
        self._last_result = result
        self._send.setEnabled(True)
        self._send.setText("Run")
        self._update_action_view(result)

        if result.status is PipelineStatus.COMPLETED:
            message = (
                f"Completed. {result.message}\n"
                f"Verification: {result.verification.status.value if result.verification else 'n/a'}"
            )
        elif result.decision and result.decision.decision is PermissionDecision.REQUIRE_CONFIRMATION:
            message = f"Confirmation required: {result.decision.message}"
        else:
            message = f"{result.status.value.upper()}: {result.message}"

        self._append_chat("OmniSense", message)
        self.statusBar().showMessage(f"Request {result.status.value}")

    def _request_failed(self, message: str) -> None:
        self._send.setEnabled(True)
        self._send.setText("Run")
        self._append_chat("OmniSense", f"Runtime error: {message}")
        self.statusBar().showMessage("Request failed")

    def _append_chat(self, speaker: str, text: str) -> None:
        self._history.appendPlainText(f"\n{speaker}\n{text}")

    def _update_action_view(self, result: PipelineResult) -> None:
        self._pending_metric.findChild(QLabel, "metric")
        self._plan_metric = self._plan_metric
        plan_status = result.plan.status.value if result.plan else "none"
        verification = result.verification.status.value if result.verification else "not run"
        self._plan_metric.layout().itemAt(1).widget().setText(plan_status.title())
        self._verify_metric.layout().itemAt(1).widget().setText(verification.title())
        self._action_text.setPlainText(
            f"INTENT\n{result.intent}\n\n"
            f"STATUS\n{result.status.value}\n\n"
            f"TRACE\n{' → '.join(result.trace.stages)}\n\n"
            f"MESSAGE\n{result.message}\n\n"
            f"PLAN ID\n{result.plan.plan_id if result.plan else '—'}\n"
            f"CONTEXT ID\n{result.context_id}"
        )

    def _request_snapshot(self) -> None:
        runtime = self._ensure_runtime()
        self.statusBar().showMessage("Capturing desktop context…")
        task = _SnapshotTask(runtime)
        task.signals.finished.connect(self._snapshot_finished)
        task.signals.failed.connect(
            lambda message: self.statusBar().showMessage(f"Context error: {message}")
        )
        self._pool.start(task)

    def _snapshot_finished(self, snapshot) -> None:
        c = snapshot.context
        self._context_label.setText(f"Context: {c.app_name or 'unknown'}")
        self._context_text.setPlainText(
            f"CONTEXT ID       {c.context_id}\n"
            f"CAPTURED AT      {c.captured_at.isoformat()}\n"
            f"MONITOR          {c.monitor_id}\n"
            f"FRAME            {c.frame_sequence}\n"
            f"APPLICATION      {c.app_name or 'unknown'}\n"
            f"WINDOW           {c.window_title or 'unknown'}\n"
            f"VISIBLE TEXT     {c.visible_text[:4000] or '—'}\n"
            f"UI ELEMENTS     {c.ui_element_count}\n"
            f"FACTS            {len(c.facts)}"
        )
        self.statusBar().showMessage("Context refreshed")

    def _refresh_health(self) -> None:
        try:
            status = health_check(load_config())
            message = (
                f"STATUS       {status.status}\n"
                f"ENVIRONMENT  {status.environment}\n"
                f"RUNTIME      {status.runtime_state}\n"
                f"GENERATION   {status.generation}\n\n"
                "UI           HEALTHY\n"
                "CAPTURE      AVAILABLE\n"
                "SECURITY     ACTIVE\n"
                "PLANNING     READY\n"
                "VERIFICATION READY\n"
                f"AUTOMATION   {'ENABLED' if self._runtime and self._runtime.automation_enabled else 'DISABLED'}"
            )
        except Exception as exc:
            message = f"Diagnostics error: {type(exc).__name__}: {exc}"
        self._diagnostic_text.setPlainText(message)
        self.statusBar().showMessage("Diagnostics refreshed")

    def closeEvent(self, event) -> None:
        if self._runtime is not None:
            try:
                self._runtime.close()
            except Exception:
                pass
        super().closeEvent(event)


def run_ui() -> int:
    """Launch the OmniSense desktop UI."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("OmniSense AI")
    app.setApplicationDisplayName("OmniSense AI")
    app.setStyle("Fusion")
    window = OmniSenseWindow()
    window.show()
    return app.exec()
