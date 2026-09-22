"""Professional OmniSense AI desktop window.

The UI is intentionally a presentation/application layer. It does not bypass
the existing safety, permission, automation, or verification boundaries.
"""

from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from ..app import health_check
from ..config import load_config
from .styles import APP_STYLE


class OmniSenseWindow(QMainWindow):
    """Main OmniSense desktop shell with navigation and product surfaces."""

    NAV = [
        ("Overview", "overview"),
        ("Assistant", "assistant"),
        ("Live Context", "context"),
        ("Action Center", "actions"),
        ("Safety", "safety"),
        ("Diagnostics", "diagnostics"),
        ("Settings", "settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("OmniSense AI")
        self.setMinimumSize(1180, 720)
        self.resize(1360, 820)
        self.setStyleSheet(APP_STYLE)
        self._nav_buttons: list[QPushButton] = []
        self._pages: dict[str, QWidget] = {}
        self._build_window()
        self._refresh_health()

    def _build_window(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 22, 18, 18)
        side.setSpacing(4)

        brand = QLabel("OmniSense")
        brand.setObjectName("brand")
        side.addWidget(brand)
        sub = QLabel("Desktop Intelligence")
        sub.setObjectName("brandSub")
        side.addWidget(sub)
        side.addSpacing(24)

        for label, key in self.NAV:
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            self._nav_buttons.append(button)
            side.addWidget(button)

        side.addStretch()

        mode = QLabel("LOCAL • SAFE MODE")
        mode.setObjectName("status")
        side.addWidget(mode)
        version = QLabel("OmniSense AI 0.1.0")
        version.setObjectName("brandSub")
        side.addWidget(version)

        self.stack = QStackedWidget()
        for key, page in self._make_pages().items():
            self._pages[key] = page
            self.stack.addWidget(page)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready • Automation is disabled by default")
        self.show_page("overview")

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

    def _page(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(34, 30, 34, 28)
        outer.setSpacing(20)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        outer.addWidget(title_label)
        sub = QLabel(subtitle)
        sub.setObjectName("pageSub")
        outer.addWidget(sub)
        return page, outer

    def _card(self, title: str, body: str, metric: str | None = None) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)
        heading = QLabel(title)
        heading.setObjectName("section")
        layout.addWidget(heading)
        if metric is not None:
            value = QLabel(metric)
            value.setObjectName("metric")
            layout.addWidget(value)
        text = QLabel(body)
        text.setObjectName("muted")
        text.setWordWrap(True)
        layout.addWidget(text)
        return card

    def _overview_page(self) -> QWidget:
        page, outer = self._page(
            "Overview",
            "A focused command center for perception, reasoning and safe action.",
        )
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        metrics.addWidget(self._card("System", "Core runtime", "Healthy"))
        metrics.addWidget(self._card("Automation", "Execution authority", "Disabled"))
        metrics.addWidget(self._card("Security", "Boundary enforcement", "Active"))
        metrics.addWidget(self._card("Verification", "Post-action checks", "Ready"))
        outer.addLayout(metrics)

        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(self._card(
            "What OmniSense sees",
            "No live capture is started by opening the UI. Capture remains an explicit opt-in capability.",
        ), 2)
        row.addWidget(self._card(
            "Control model",
            "AI output never executes directly. Actions pass through planning, safety, automation and verification.",
        ), 1)
        outer.addLayout(row)

        card = QFrame()
        card.setObjectName("card")
        c = QVBoxLayout(card)
        c.setContentsMargins(18, 16, 18, 16)
        h = QLabel("Quick actions")
        h.setObjectName("section")
        c.addWidget(h)
        buttons = QHBoxLayout()
        for label, target in [
            ("Open Assistant", "assistant"),
            ("Review Safety", "safety"),
            ("Run Diagnostics", "diagnostics"),
        ]:
            b = QPushButton(label)
            b.setObjectName("secondary")
            b.clicked.connect(lambda checked=False, k=target: self.show_page(k))
            buttons.addWidget(b)
        buttons.addStretch()
        c.addLayout(buttons)
        outer.addWidget(card)
        outer.addStretch()
        return page

    def _assistant_page(self) -> QWidget:
        page, outer = self._page(
            "Assistant",
            "Ask OmniSense to understand your current desktop context.",
        )
        chat = QFrame()
        chat.setObjectName("card")
        layout = QVBoxLayout(chat)
        layout.setContentsMargins(18, 18, 18, 18)
        history = QPlainTextEdit()
        history.setReadOnly(True)
        history.setPlainText(
            "OmniSense AI\n\n"
            "Ready. Desktop automation is disabled until explicitly configured.\n"
            "Ask a question or describe a task below."
        )
        layout.addWidget(history, 1)
        composer = QHBoxLayout()
        input_box = QLineEdit()
        input_box.setPlaceholderText("Ask OmniSense…")
        send = QPushButton("Send")
        send.setObjectName("primary")
        def submit() -> None:
            text = input_box.text().strip()
            if not text:
                return
            history.appendPlainText(f"\nYou  ·  {text}")
            history.appendPlainText(
                "OmniSense  ·  Request received. Planning and safety checks are required before any action."
            )
            input_box.clear()
        send.clicked.connect(submit)
        input_box.returnPressed.connect(submit)
        composer.addWidget(input_box, 1)
        composer.addWidget(send)
        layout.addLayout(composer)
        outer.addWidget(chat, 1)
        return page

    def _context_page(self) -> QWidget:
        page, outer = self._page(
            "Live Context",
            "Structured desktop evidence exposed to the intelligence layer.",
        )
        grid = QHBoxLayout()
        grid.setSpacing(14)
        grid.addWidget(self._card("Active application", "No live capture session", "—"))
        grid.addWidget(self._card("Window", "Waiting for capture", "—"))
        grid.addWidget(self._card("Context freshness", "No snapshot available", "Idle"))
        outer.addLayout(grid)

        evidence = QFrame()
        evidence.setObjectName("card")
        layout = QVBoxLayout(evidence)
        layout.setContentsMargins(18, 16, 18, 16)
        h = QLabel("Evidence")
        h.setObjectName("section")
        layout.addWidget(h)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            "Visible text\n—\n\n"
            "UI elements\n—\n\n"
            "Facts\n—\n\n"
            "Source\nNo capture source attached"
        )
        layout.addWidget(text)
        outer.addWidget(evidence, 1)
        return page

    def _actions_page(self) -> QWidget:
        page, outer = self._page(
            "Action Center",
            "Review planned actions before they can reach desktop automation.",
        )
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QLabel("Action queue")
        heading.setObjectName("section")
        layout.addWidget(heading)
        queue = QListWidget()
        queue.addItem(QListWidgetItem("No pending actions"))
        layout.addWidget(queue)
        note = QLabel(
            "Every executable action must carry valid context, pass permission checks, "
            "and produce verification evidence."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        outer.addWidget(card, 1)
        return page

    def _safety_page(self) -> QWidget:
        page, outer = self._page(
            "Safety Center",
            "Authority stays explicit, bounded and observable.",
        )
        items = [
            ("Automation", "Disabled by default"),
            ("Confirmation", "Required for medium/high-risk actions"),
            ("High-consequence actions", "Blocked"),
            ("Context freshness", "Bounded by safety policy"),
            ("Verification", "Required after execution"),
        ]
        for title, detail in items:
            card = self._card(title, detail, "ENFORCED")
            outer.addWidget(card)
        outer.addStretch()
        return page

    def _diagnostics_page(self) -> QWidget:
        page, outer = self._page(
            "Diagnostics",
            "Fast health checks for the local OmniSense runtime.",
        )
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        self._diagnostic_text = QPlainTextEdit()
        self._diagnostic_text.setReadOnly(True)
        layout.addWidget(self._diagnostic_text)
        refresh = QPushButton("Refresh diagnostics")
        refresh.setObjectName("primary")
        refresh.clicked.connect(self._refresh_health)
        layout.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(card, 1)
        return page

    def _settings_page(self) -> QWidget:
        page, outer = self._page(
            "Settings",
            "Local configuration. Sensitive credentials are never stored by the UI.",
        )
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        for label, checked in [
            ("Enable screen capture", False),
            ("Allow desktop automation", False),
            ("Require confirmation for risky actions", True),
        ]:
            check = QCheckBox(label)
            check.setChecked(checked)
            layout.addWidget(check)
        note = QLabel(
            "These controls are intentionally presented as policy settings. "
            "They do not grant unrestricted authority to the AI."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        save = QPushButton("Save configuration")
        save.setObjectName("primary")
        save.clicked.connect(lambda: self.statusBar().showMessage("Configuration changes require runtime configuration integration."))
        layout.addWidget(save, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(card)
        outer.addStretch()
        return page

    def show_page(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        for button, (_, button_key) in zip(self._nav_buttons, self.NAV):
            button.setChecked(button_key == key)

    def _refresh_health(self) -> None:
        try:
            status = health_check(load_config())
            message = (
                f"Status: {status.status}\n"
                f"Environment: {status.environment}\n"
                f"Runtime state: {status.runtime_state}\n"
                f"Generation: {status.generation}\n\n"
                "UI process: healthy\n"
                "Automation authority: disabled by default"
            )
        except Exception as exc:
            message = f"Diagnostics error: {type(exc).__name__}: {exc}"
        if hasattr(self, "_diagnostic_text"):
            self._diagnostic_text.setPlainText(message)
        self.statusBar().showMessage("Diagnostics refreshed")


def run_ui() -> int:
    """Launch the OmniSense desktop UI."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("OmniSense AI")
    app.setApplicationDisplayName("OmniSense AI")
    app.setStyle("Fusion")
    window = OmniSenseWindow()
    window.show()
    return app.exec()
