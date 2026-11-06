# Autonomous 7-Agent AI Software Engineering Workflow

A production-grade, multi-agent AI system designed by a Senior AI/ML Engineer. The architecture follows a strict, verification-driven pipeline with bi-directional feedback loops between Strict QA and Lead Coder, supervised intent gating, and dual-mode client interfaces (Terminal CLI and Web Browser UI).

---

## 🏛️ System Architecture

```text
[ Your Browser UI / Python Terminal ]
         │
         ▼
 ┌──────────────────────────────────────────────┐
 │ Agent 1: Interface & Medium                  │ ◄── Takes your prompt & relays progress
 └──────┬───────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │ Agents 2 & 3: Interpreter & Architect Debater│ ◄── Analyzes intent & debates tech trade-offs
 └──────┬───────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │ Agent 4: Lead Coder                          │ ◄── Writes clean, complete code
 └──────┬───────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │ Agent 5: Strict QA & Bug Tester              │ ◄── Audits code for errors & loops back to Coder
 └──────┬───────────────────────────────────────┘
        │ (Passed QA)
        ▼
 ┌──────────────────────────────────────────────┐
 │ Agent 6: Supervisor                          │ ◄── Final review against your original intent
 └──────┬───────────────────────────────────────┘
        │ (Approved)
        ▼
 [ Agent 7 delivers final code package to you ]
```

---

## 🤖 The 7 Specialized Agents

| Agent | Name | Role & Responsibility |
|---|---|---|
| **Agent 1** | **Interface & Medium** | Ingests prompt, parses domain complexity, normalizes constraints, establishes real-time telemetry streaming to UI. |
| **Agent 2** | **Requirement Interpreter** | Deconstructs user prompt into strict functional requirements, data contracts, and failure boundary conditions. |
| **Agent 3** | **Architect Debater** | Debates tech trade-offs (concurrency, O(1) complexity, memory bounds, locking) against Agent 2, synthesizing the Technical Consensus Spec. |
| **Agent 4** | **Lead Coder** | Writes complete, modular, PEP 8 compliant, type-annotated code and unit test suites; surgically refactors code when receiving QA feedback. |
| **Agent 5** | **Strict QA & Bug Tester** | Audits code via static AST parsing and isolated dynamic unit test execution in a sandbox. Triggers **circular loopback** to Agent 4 on defects. |
| **Agent 6** | **Supervisor** | Conducts executive audit against original prompt intent. Grades alignment (0–100%) and authorizes release. |
| **Agent 7** | **Delivery Specialist** | Generates verified deliverables (`src/`, `tests/`, `README.md`, `run.py`), compiles portable `.zip` bundle, and emits completion notice. |

---

## 🚀 Quickstart & Usage

The entire workflow is built to run **100% out-of-the-box using the Python 3.11+ Standard Library** (zero mandatory third-party pip dependencies required).

### 1. Interactive Python Terminal CLI
Launch the interactive terminal interface:
```bash
python main.py
```

Run directly with a prompt:
```bash
python main.py --prompt "Build a high-performance thread-safe LRU Cache with TTL and statistics"
```

### 2. Demonstrate Strict QA Self-Healing Loopback
Simulates a bug on Pass 1, triggering Agent 5 to catch the failure and route back to Agent 4 for autonomous refactoring before passing on Pass 2:
```bash
python main.py --prompt "Build a high-performance thread-safe LRU Cache with TTL and statistics" --demo-loopback
```

### 3. Modern Browser UI Dashboard
Launch the web server:
```bash
python main.py --web --port 8080
```
Open **`http://127.0.0.1:8080`** in your browser to interact with:
- **Live SVG Pipeline DAG**: Highlights active agents with glowing rings and pulse animations.
- **Debate Arena**: Real-time transcript of Agent 2 & Agent 3 debating concurrency and architectural trade-offs.
- **Code Studio**: Live file viewer with copy-to-clipboard functionality.
- **Strict QA Console**: Test runner execution logs and loopback counter.
- **Supervisor Seal**: Real-time alignment scorecard and verification checklist.
- **Delivery Drawer**: Instant one-click ZIP archive download and quickstart commands.

---

## 🧪 Running the Test Suite

Run the comprehensive unit test suite:
```bash
python -m unittest discover -s tests -v
```

---

## 📦 Directory Structure

```text
ai_agent_workflow/
├── core/
│   ├── models.py            # Dataclass state models (WorkflowState, DebateTurn, QAReport, etc.)
│   ├── event_bus.py         # Thread-safe telemetry event bus for CLI & Browser SSE
│   ├── llm_provider.py      # Senior Cognitive Simulator & OpenAI-compatible client
│   └── orchestrator.py      # State machine coordinator managing agents & loopbacks
├── agents/
│   ├── base.py              # BaseAgent abstract class
│   ├── agent1_interface.py  # Agent 1: Interface & Medium
│   ├── agent2_3_debate.py   # Agents 2 & 3: Interpreter & Architect Debater
│   ├── agent4_coder.py      # Agent 4: Lead Coder
│   ├── agent5_qa.py         # Agent 5: Strict QA & Bug Tester (Dynamic sandbox & Loopback)
│   ├── agent6_supervisor.py # Agent 6: Supervisor (Alignment & Intent Auditor)
│   └── agent7_delivery.py   # Agent 7: Delivery Specialist (ZIP packager & docs)
├── ui/
│   ├── terminal.py          # Formatted ANSI terminal runner
│   ├── web_server.py        # Multi-threaded HTTP/SSE server
│   └── static/
│       ├── index.html       # Glassmorphism browser dashboard
│       ├── app.js           # Reactive SSE client & DAG state controller
│       └── style.css        # Responsive dark theme styling
├── tests/
│   └── test_workflow.py     # 8 comprehensive unit tests
├── output/                  # Delivered code packages and ZIP archives
├── main.py                  # Unified CLI / Web launcher
└── README.md                # System documentation
```
