"""Visual system for the OmniSense AI desktop application.

The UI uses a restrained, Windows-friendly product aesthetic:
clear hierarchy, light surfaces, strong typography, and minimal decoration.
"""

APP_STYLE = """
QMainWindow {
    background: #f4f6f8;
    color: #17202a;
    font-family: "Segoe UI";
    font-size: 13px;
}
QWidget {
    color: #17202a;
    font-family: "Segoe UI";
    font-size: 13px;
}
QLabel {
    background: transparent;
}
QFrame#sidebar {
    background: #ffffff;
    border-right: 1px solid #dfe4ea;
}
QFrame#topbar {
    background: #ffffff;
    border-bottom: 1px solid #e2e7ec;
}
QFrame#brandMark {
    background: #1769e0;
    border-radius: 8px;
}
QLabel#brand {
    color: #111827;
    font-size: 18px;
    font-weight: 700;
}
QLabel#brandSub {
    color: #7a8794;
    font-size: 11px;
}
QLabel#workspace {
    color: #657382;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#nav {
    text-align: left;
    padding: 10px 12px;
    border: 0;
    border-radius: 7px;
    color: #5d6a78;
    background: transparent;
    font-size: 13px;
}
QPushButton#nav:hover {
    background: #f1f4f7;
    color: #17202a;
}
QPushButton#nav:checked {
    background: #eaf2ff;
    color: #1557b0;
    font-weight: 600;
}
QPushButton#primary {
    background: #1769e0;
    color: white;
    border: 1px solid #1769e0;
    border-radius: 7px;
    padding: 9px 15px;
    font-weight: 600;
}
QPushButton#primary:hover { background: #155fc9; }
QPushButton#secondary {
    background: #ffffff;
    color: #334155;
    border: 1px solid #d7dee6;
    border-radius: 7px;
    padding: 8px 13px;
}
QPushButton#secondary:hover {
    background: #f7f9fb;
    border-color: #c5ced8;
}
QPushButton#iconButton {
    background: transparent;
    border: 0;
    border-radius: 7px;
    color: #64748b;
    padding: 7px;
}
QPushButton#iconButton:hover { background: #f1f4f7; }
QFrame#card {
    background: #ffffff;
    border: 1px solid #e1e6eb;
    border-radius: 9px;
}
QFrame#card:hover { border-color: #d3dae2; }
QFrame#metricCard {
    background: #ffffff;
    border: 1px solid #e1e6eb;
    border-radius: 9px;
}
QLabel#pageTitle {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
}
QLabel#pageSub {
    color: #687787;
    font-size: 12px;
}
QLabel#metric {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
}
QLabel#metricCaption {
    color: #748190;
    font-size: 11px;
}
QLabel#section {
    font-size: 14px;
    font-weight: 650;
    color: #17202a;
}
QLabel#eyebrow {
    color: #1769e0;
    font-size: 10px;
    font-weight: 700;
}
QLabel#muted {
    color: #73808e;
}
QLabel#value {
    color: #17202a;
    font-weight: 600;
}
QLabel#status {
    color: #138a4b;
    font-weight: 650;
}
QLabel#statusDot {
    color: #1aa260;
    font-size: 15px;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d7dee6;
    border-radius: 7px;
    padding: 9px;
    color: #17202a;
    selection-background-color: #dceaff;
    selection-color: #102a43;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #1769e0;
}
QListWidget {
    background: #ffffff;
    border: 1px solid #e1e6eb;
    border-radius: 8px;
    outline: 0;
}
QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #edf0f3;
}
QListWidget::item:selected {
    background: #eaf2ff;
    color: #1557b0;
}
QCheckBox { color: #334155; spacing: 8px; }
QProgressBar {
    background: #edf1f5;
    border: 0;
    border-radius: 4px;
    height: 7px;
    text-align: center;
}
QProgressBar::chunk {
    background: #1769e0;
    border-radius: 4px;
}
QScrollArea {
    border: 0;
    background: transparent;
}
QStatusBar {
    background: #ffffff;
    color: #718096;
    border-top: 1px solid #e2e7ec;
}
QToolTip {
    background: #17202a;
    color: #ffffff;
    border: 0;
    padding: 5px 7px;
}
"""

