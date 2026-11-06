"""
UI package for Terminal and Browser dashboards.
"""

from ui.terminal import run_terminal_session, TerminalUI
from ui.web_server import start_web_server

__all__ = ["run_terminal_session", "TerminalUI", "start_web_server"]
