"""CLI entry point for the OmniSense desktop UI."""

from .app import run_ui

if __name__ == "__main__":
    raise SystemExit(run_ui())
