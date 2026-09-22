"""Smoke tests for the optional OmniSense UI layer."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6", reason="UI dependencies are optional")

# Offscreen mode keeps CI/headless test runs deterministic.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from omnisense_ai.ui.app import OmniSenseWindow  # noqa: E402


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_window_builds(qt_app):
    window = OmniSenseWindow()
    assert window.windowTitle() == "OmniSense AI"
    assert window.minimumWidth() >= 1100
    assert len(window._pages) == 7
    window.close()


def test_navigation(qt_app):
    window = OmniSenseWindow()
    window.show_page("safety")
    assert window.stack.currentWidget() is window._pages["safety"]
    window.show_page("assistant")
    assert window.stack.currentWidget() is window._pages["assistant"]
    window.close()
