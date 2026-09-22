"""Professional OmniSense AI desktop application shell.

This is a real product UI, not an authority layer. Existing planning, safety,
automation, verification and security services remain the only execution path.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
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
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..app import health_check
from ..config import load_config
from .styles import APP_STYLE


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
        self._nav_buttons: list[QPushButton] = []
        self._pages: dict[str, QWidget] = {}
        self._build_window()
        self._refresh_health()

    # ---------- shared UI helpers ----------

    def _label(self, text: str, object_name: str = "") -> QLabel:
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
        mark_label.setStyleSheet("color: white; font-size: 18px; font-weight: 700;")
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

        workspace = self._label("WORKSPACE", "workspace")
        side.addWidget(workspace)
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
        mode_row.addWidget(self._label("Safe mode", "status"))
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
        hero_layout.setSpacing(18)

        copy = QVBoxLayout()
        copy.setSpacing(5)
        copy.addWidget(self._label("LOCAL DESKTOP AGENT", "eyebrow"))
        copy.addWidget(self._label("Your desktop, understood.", "section"))
        desc = self._label(
            "OmniSense observes desktop context, reasons about intent and keeps "
            "execution behind explicit safety boundaries."
        )
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        copy.addWidget(desc)
        hero_layout.addLayout(copy, 1)

        open_button = QPushButton("Open Assistant")
        open_button.setObjectName("primary")
        open_button.clicked.connect(lambda: self.show_page("assistant"))
        hero_layout.addWidget(open_button, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(hero)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        metrics.addWidget(self._metric_card("Runtime", "Healthy", "Core services available"))
        metrics.addWidget(self._metric_card("Automation", "Disabled", "No desktop authority"))
        metrics.addWidget(self._metric_card("Security", "Protected", "Input treated as evidence"))
        metrics.addWidget(self._metric_card("Verification", "Ready", "Post-action checks"))
        outer.addLayout(metrics)

        columns = QHBoxLayout()
        columns.setSpacing(14)

        left = QFrame()
        left.setObjectName("card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(17, 16, 17, 16)
        left_layout.setSpacing(12)
        left_layout.addWidget(self._section_header("System activity", "Diagnostics", lambda: self.show_page("diagnostics")))

        for title, detail in [
            ("Runtime initialized", "OmniSense core is available locally."),
            ("Safety boundary loaded", "Action requests remain gated."),
            ("Capture session", "Idle — no screen capture is running."),
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
        right_layout.setSpacing(10)
        right_layout.addWidget(self._label("Control model", "section"))
        right_layout.addWidget(self._label("AI → Plan → Safety → Automation → Verify", "value"))
        right_layout.addWidget(self._label(
            "No model response gets direct desktop authority. The integration layer "
            "keeps every executable step behind the existing safety pipeline.",
            "muted",
        ))
        right_layout.addSpacing(5)
        for label in ("Context", "Planning", "Permission", "Verification"):
            pill = QLabel("  " + label + "  ")
            pill.setStyleSheet(
                "background:#f1f5f9; color:#475569; border:1px solid #e2e8f0;"
                "border-radius:5px; padding:5px 2px;"
            )
            right_layout.addWidget(pill)
        right_layout.addStretch()

        columns.addWidget(left, 3)
        columns.addWidget(right, 2)
        outer.addLayout(columns)
        outer.addStretch()
        return page

    def _assistant_page(self) -> QWidget:
        page, outer = self._page(
            "Assistant",
            "A focused workspace for asking questions and preparing desktop actions.",
        )

        toolbar = QHBoxLayout()
        toolbar.addWidget(self._label("SESSION", "metricCaption"))
        toolbar.addWidget(self._label("Local • Safe mode", "value"))
        toolbar.addStretch()
        toolbar.addWidget(self._label("Context: not connected", "muted"))
        outer.addLayout(toolbar)

        shell = QFrame()
        shell.setObjectName("card")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(18, 18, 18, 18)
        shell_layout.setSpacing(12)

        history = QPlainTextEdit()
        history.setReadOnly(True)
        history.setPlainText(
            "OmniSense AI\n"
            "────────────────────────────────────────\n"
            "Ready to help. Describe what you want to understand or accomplish.\n\n"
            "Safety note\n"
            "Actions are never executed directly from model output. They must pass "
            "through planning, permission and verification."
        )
        shell_layout.addWidget(history, 1)

        composer = QHBoxLayout()
        input_box = QLineEdit()
        input_box.setPlaceholderText("Describe a task or ask a question…")
        send = QPushButton("Send")
        send.setObjectName("primary")

        def submit() -> None:
            text = input_box.text().strip()
            if not text:
                return
            history.appendPlainText(f"\nYou\n{text}")
            history.appendPlainText(
                "\nOmniSense\nRequest captured. Planning and safety checks are "
                "required before any executable action."
            )
            input_box.clear()
            self.statusBar().showMessage("Assistant request captured")

        send.clicked.connect(submit)
        input_box.returnPressed.connect(submit)
        composer.addWidget(input_box, 1)
        composer.addWidget(send)
        shell_layout.addLayout(composer)
        outer.addWidget(shell, 1)
        return page

    def _context_page(self) -> QWidget:
        page, outer = self._page(
            "Live Context",
            "See the structured evidence available to the intelligence layer.",
        )

        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self._metric_card("Application", "Idle", "No capture source"))
        top.addWidget(self._metric_card("Window", "—", "Waiting for context"))
        top.addWidget(self._metric_card("Freshness", "—", "No snapshot"))
        top.addWidget(self._metric_card("Evidence", "0", "Items available"))
        outer.addLayout(top)

        evidence = QFrame()
        evidence.setObjectName("card")
        layout = QVBoxLayout(evidence)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.addWidget(self._section_header("Evidence stream", "Refresh", lambda: self.statusBar().showMessage("Context refresh requested")))
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            "CAPTURE STATUS     IDLE\n"
            "SOURCE             —\n"
            "CAPTURED AT        —\n"
            "WINDOW             —\n\n"
            "VISIBLE TEXT\n"
            "No evidence available. Start an explicit capture session to populate context."
        )
        layout.addWidget(text, 1)
        outer.addWidget(evidence, 1)
        return page

    def _actions_page(self) -> QWidget:
        page, outer = self._page(
            "Action Center",
            "Review what OmniSense intends to do before execution is even possible.",
        )

        stats = QHBoxLayout()
        stats.addWidget(self._metric_card("Pending", "0", "Actions awaiting review"))
        stats.addWidget(self._metric_card("Blocked", "0", "Rejected by safety"))
        stats.addWidget(self._metric_card("Verified", "0", "Completed with evidence"))
        stats.addStretch()
        outer.addLayout(stats)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.addWidget(self._section_header("Action queue"))
        queue = QListWidget()
        queue.addItem(QListWidgetItem("No pending actions"))
        layout.addWidget(queue, 1)
        note = self._label(
            "Executable actions require valid context, a planner-generated plan, "
            "a safety decision and post-execution verification.",
            "muted",
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        outer.addWidget(card, 1)
        return page

    def _safety_page(self) -> QWidget:
        page, outer = self._page(
            "Safety & Control",
            "The boundary between intelligence and authority.",
        )

        banner = QFrame()
        banner.setObjectName("card")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(17, 14, 17, 14)
        banner_layout.addWidget(self._label("●", "statusDot"))
        banner_layout.addWidget(self._label("Safe mode is active", "value"))
        banner_layout.addStretch()
        banner_layout.addWidget(self._label("Automation disabled", "muted"))
        outer.addWidget(banner)

        grid = QHBoxLayout()
        grid.setSpacing(12)
        policies = [
            ("Execution authority", "DISABLED", "Desktop automation is opt-in."),
            ("Risk gating", "ENFORCED", "Medium/high-risk actions require confirmation."),
            ("High consequence", "BLOCKED", "Dangerous intents are rejected."),
            ("Context freshness", "BOUNDED", "Stale context cannot authorize action."),
            ("Verification", "REQUIRED", "Execution needs post-action evidence."),
            ("Input trust", "UNTRUSTED", "Screen content is evidence, not instructions."),
        ]
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

        self._diagnostic_text = QPlainTextEdit()
        self._diagnostic_text.setReadOnly(True)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.addWidget(self._section_header("Runtime health"))
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
            "Configure local product behavior without bypassing safety controls.",
        )

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 17, 17, 17)
        layout.setSpacing(12)
        layout.addWidget(self._label("Desktop capabilities", "section"))

        checks = []
        for label, checked in [
            ("Enable screen capture", False),
            ("Allow desktop automation", False),
            ("Require confirmation for risky actions", True),
        ]:
            check = QCheckBox(label)
            check.setChecked(checked)
            checks.append(check)
            layout.addWidget(check)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color:#e5e7eb;")
        layout.addWidget(divider)
        layout.addWidget(self._label(
            "These controls are UI preferences until connected to the runtime "
            "configuration service. Enabling a checkbox never grants unrestricted AI authority.",
            "muted",
        ))

        save = QPushButton("Save settings")
        save.setObjectName("primary")
        save.clicked.connect(
            lambda: self.statusBar().showMessage(
                "Settings UI updated • runtime configuration integration is still required"
            )
        )
        layout.addWidget(save, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(card)
        outer.addStretch()
        return page

    # ---------- behavior ----------

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
                f"STATUS       {status.status}\n"
                f"ENVIRONMENT  {status.environment}\n"
                f"RUNTIME      {status.runtime_state}\n"
                f"GENERATION   {status.generation}\n\n"
                "UI           HEALTHY\n"
                "AUTOMATION   DISABLED BY DEFAULT\n"
                "SECURITY     ACTIVE\n"
                "VERIFICATION READY"
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
