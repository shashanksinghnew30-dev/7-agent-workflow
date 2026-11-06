"""
Agent 4: Lead Coder
Writes clean, complete, type-annotated code and unit test suites based on Technical Consensus Spec,
and addresses QA bug reports when looped back from Agent 5.
"""

from __future__ import annotations
import time
from core.models import WorkflowState, WorkflowStatus, AgentRole
from core.event_bus import EventBus
from core.llm_provider import CognitiveSimulatorEngine
from agents.base import BaseAgent


class LeadCoderAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(AgentRole.AGENT_4_LEAD_CODER, llm_provider)

    def run(self, state: WorkflowState, event_bus: EventBus) -> WorkflowState:
        state.current_agent = self.name
        is_loopback = (state.qa_loop_count > 0)
        state.status = WorkflowStatus.QA_LOOPBACK if is_loopback else WorkflowStatus.CODING

        last_qa_report = state.qa_history[-1] if state.qa_history else None
        latest_failure = last_qa_report.failures[0] if (last_qa_report and last_qa_report.failures) else None

        if is_loopback:
            self.log(
                event_bus,
                event_type="code",
                message=f"[Iteration {state.qa_loop_count}] Agent 4 received QA Bug Report. Commencing refactoring...",
                payload={"failure": latest_failure.to_dict() if latest_failure else {}}
            )
        else:
            self.log(
                event_bus,
                event_type="code",
                message=f"Agent 4 implementing architecture for '{state.consensus_spec.system_name}'..."
            )

        # Generate or refactor code artifacts
        inject_bug = (getattr(self.llm, "demo_qa_loopback", False) and state.qa_loop_count == 0)

        if isinstance(self.llm, CognitiveSimulatorEngine):
            artifacts = self.llm.generate_code_artifacts(
                user_prompt=state.user_prompt,
                spec=state.consensus_spec,
                qa_feedback=latest_failure,
                inject_bug=inject_bug
            )
        else:
            sim = CognitiveSimulatorEngine()
            artifacts = sim.generate_code_artifacts(
                user_prompt=state.user_prompt,
                spec=state.consensus_spec,
                qa_feedback=latest_failure,
                inject_bug=inject_bug
            )

        state.source_files = artifacts

        for path, file_obj in artifacts.items():
            loc = len(file_obj.content.splitlines())
            self.log(
                event_bus,
                event_type="code",
                message=f"Generated '{path}' ({loc} LOC) - {file_obj.description}",
                payload={"path": path, "loc": loc, "content": file_obj.content}
            )
            time.sleep(0.05)

        self.log(
            event_bus,
            event_type="status",
            message=f"Code generation complete ({len(artifacts)} files). Handing over to Agent 5 (Strict QA)..."
        )

        return state
