"""Visual system for the OmniSense desktop application."""

APP_STYLE = """
QMainWindow, QWidget {
    background: #0b0f14;
    color: #e8edf3;
    font-family: "Segoe UI";
    font-size: 13px;
}
QFrame#sidebar {
    background: #0f141b;
    border-right: 1px solid #202833;
}
QLabel#brand {
    color: #f5f7fa;
    font-size: 19px;
    font-weight: 700;
}
QLabel#brandSub {
    color: #7f8b99;
    font-size: 11px;
}
QPushButton#nav {
    text-align: left;
    padding: 11px 14px;
    border: 0;
    border-radius: 7px;
    color: #9aa6b2;
    background: transparent;
}
QPushButton#nav:hover {
    background: #171e27;
    color: #e8edf3;
}
QPushButton#nav:checked {
    background: #1b2632;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primary {
    background: #2f81f7;
    color: white;
    border: 0;
    border-radius: 7px;
    padding: 10px 16px;
    font-weight: 600;
}
QPushButton#primary:hover { background: #3b8df8; }
QPushButton#secondary {
    background: #171e27;
    color: #d7dee7;
    border: 1px solid #29333f;
    border-radius: 7px;
    padding: 9px 14px;
}
QPushButton#secondary:hover { background: #1d2630; }
QFrame#card {
    background: #111820;
    border: 1px solid #202a35;
    border-radius: 10px;
}
QLabel#pageTitle {
    font-size: 25px;
    font-weight: 700;
    color: #f5f7fa;
}
QLabel#pageSub {
    color: #7f8b99;
    font-size: 12px;
}
QLabel#metric {
    font-size: 25px;
    font-weight: 700;
    color: #f5f7fa;
}
QLabel#metricLabel {
    color: #7f8b99;
    font-size: 11px;
}
QLabel#section {
    font-size: 14px;
    font-weight: 650;
    color: #e8edf3;
}
QLabel#muted {
    color: #7f8b99;
}
QLabel#status {
    color: #52d273;
    font-weight: 600;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background: #0d131a;
    border: 1px solid #29333f;
    border-radius: 7px;
    padding: 9px;
    color: #e8edf3;
    selection-background-color: #2f81f7;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #2f81f7;
}
QScrollArea {
    border: 0;
    background: transparent;
}
QCheckBox { color: #c9d1da; spacing: 8px; }
QProgressBar {
    background: #171e27;
    border: 0;
    border-radius: 4px;
    height: 7px;
    text-align: center;
}
QProgressBar::chunk {
    background: #2f81f7;
    border-radius: 4px;
}
QStatusBar {
    background: #0f141b;
    color: #7f8b99;
    border-top: 1px solid #202833;
}
"""
