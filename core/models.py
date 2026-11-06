"""
Data models and state definitions for the 7-Agent AI Workflow.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional


class AgentRole(str, Enum):
    AGENT_1_INTERFACE = "Agent 1: Interface & Medium"
    AGENT_2_INTERPRETER = "Agent 2: Requirement Interpreter"
    AGENT_3_ARCHITECT = "Agent 3: Architect Debater"
    AGENT_4_LEAD_CODER = "Agent 4: Lead Coder"
    AGENT_5_STRICT_QA = "Agent 5: Strict QA & Bug Tester"
    AGENT_6_SUPERVISOR = "Agent 6: Supervisor"
    AGENT_7_DELIVERY = "Agent 7: Delivery Specialist"


class WorkflowStatus(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    DEBATING = "DEBATING"
    CODING = "CODING"
    QA_AUDIT = "QA_AUDIT"
    QA_LOOPBACK = "QA_LOOPBACK"
    SUPERVISOR_REVIEW = "SUPERVISOR_REVIEW"
    PACKAGING = "PACKAGING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class EventMessage:
    agent: str
    event_type: str  # "status", "debate", "code", "qa", "supervisor", "delivery", "log"
    message: str
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DebateTurn:
    round_number: int
    speaker: str  # Agent 2 or Agent 3
    argument_type: str  # "requirements", "challenge", "trade_off", "consensus"
    thesis: str
    trade_offs: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TechnicalSpec:
    system_name: str
    intent_summary: str
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    architectural_patterns: List[str]
    tech_trade_offs_resolved: List[str]
    file_manifest: List[str]
    data_contracts: Dict[str, str] = field(default_factory=dict)
    test_strategy: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SourceFile:
    path: str
    content: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QAFailureDetail:
    failure_type: str  # "SyntaxError", "TestFailure", "LintIssue", "LogicError"
    location: str
    error_message: str
    suggested_fix: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QAReport:
    passed: bool
    loop_iteration: int
    syntax_valid: bool
    tests_executed: int
    tests_passed: int
    tests_failed: int
    execution_stdout: str
    execution_stderr: str
    failures: List[QAFailureDetail] = field(default_factory=list)
    quality_score: float = 100.0  # 0 to 100

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SupervisorReview:
    approved: bool
    alignment_score: float  # 0 to 100
    original_intent_checklist: Dict[str, bool]
    strengths: List[str]
    notes: str
    executive_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeliveryPackage:
    project_slug: str
    target_dir: str
    zip_path: str
    file_count: int
    total_loc: int
    manifest: List[str]
    readme_markdown: str
    quickstart_command: str
    test_command: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_prompt: str = ""
    status: WorkflowStatus = WorkflowStatus.IDLE
    current_agent: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    # Step outputs
    interface_metadata: Dict[str, Any] = field(default_factory=dict)
    debate_transcript: List[DebateTurn] = field(default_factory=list)
    consensus_spec: Optional[TechnicalSpec] = None
    source_files: Dict[str, SourceFile] = field(default_factory=dict)
    qa_history: List[QAReport] = field(default_factory=list)
    supervisor_review: Optional[SupervisorReview] = None
    delivery_package: Optional[DeliveryPackage] = None

    # Event logs
    events: List[EventMessage] = field(default_factory=list)
    qa_loop_count: int = 0
    max_qa_loops: int = 3

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
