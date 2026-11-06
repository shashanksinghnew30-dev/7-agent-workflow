"""
Main Entry Point for the 7-Agent AI Workflow.
Supports both interactive Python Terminal CLI and Browser UI modes.

Usage:
    python main.py                       # Interactive Terminal CLI
    python main.py --web                 # Launch Browser Web Dashboard
    python main.py --prompt "..."        # Run specific prompt in terminal
    python main.py --demo-loopback       # Demonstrate QA self-healing loopback
"""

from __future__ import annotations
import sys
import argparse
from ui.terminal import run_terminal_session
from ui.web_server import start_web_server
from core.event_bus import EventBus


def parse_args():
    parser = argparse.ArgumentParser(
        description="Autonomous 7-Agent AI Software Engineering Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow Topology:
  [ Browser UI / Python Terminal ]
              │
              ▼
    Agent 1: Interface & Medium
              │
              ▼
    Agents 2 & 3: Interpreter & Architect Debater
              │
              ▼
    Agent 4: Lead Coder
              │
              ▼
    Agent 5: Strict QA & Bug Tester  ◄── (Loops back to Agent 4 on defects)
              │ (Passed QA)
              ▼
    Agent 6: Supervisor              ◄── (Reviews against original intent)
              │ (Approved)
              ▼
    Agent 7: Delivery Specialist     ◄── (Packages & delivers final ZIP)
"""
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the Browser Web UI server (default: http://127.0.0.1:8080)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address for Browser Web server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for Browser Web server"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Software prompt to execute immediately in Terminal CLI"
    )
    parser.add_argument(
        "--demo-loopback",
        action="store_true",
        help="Simulate a defect on pass 1 to demonstrate Agent 5 -> Agent 4 self-healing loop"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.web:
        shared_bus = EventBus()
        start_web_server(
            host=args.host,
            port=args.port,
            event_bus=shared_bus,
            base_output_dir="output"
        )
    else:
        run_terminal_session(
            prompt=args.prompt,
            demo_qa_loopback=args.demo_loopback
        )


if __name__ == "__main__":
    main()
