"""
Workflow Orchestrator
Controls the state machine, agent sequencing, conditional QA loopback,
and intent supervisor gates according to the architecture specification.
"""

from __future__ import annotations
import time
from typing import Optional
from core.models import WorkflowState, WorkflowStatus
from core.event_bus import EventBus
from core.llm_provider import BaseLLMProvider, get_llm_provider
from agents import (
    InterfaceAndMediumAgent,
    InterpreterAndArchitectDebaterAgent,
    LeadCoderAgent,
    StrictQABugTesterAgent,
    SupervisorAgent,
    DeliverySpecialistAgent,
)


class WorkflowOrchestrator:
    """
    State machine runner executing the 7-Agent Workflow:
    [UI/Terminal] -> Agent 1 -> Agents 2&3 -> Agent 4 -> Agent 5 (QA Loopback) -> Agent 6 -> Agent 7
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        event_bus: Optional[EventBus] = None,
        base_output_dir: str = "output",
        demo_qa_loopback: bool = False
    ):
        self.event_bus = event_bus or EventBus()
        self.llm = llm_provider or get_llm_provider(demo_qa_loopback=demo_qa_loopback)
        self.base_output_dir = base_output_dir

        # Initialize the 7 agents
        self.agent1 = InterfaceAndMediumAgent(self.llm)
        self.agent2_3 = InterpreterAndArchitectDebaterAgent(self.llm)
        self.agent4 = LeadCoderAgent(self.llm)
        self.agent5 = StrictQABugTesterAgent(self.llm)
        self.agent6 = SupervisorAgent(self.llm)
        self.agent7 = DeliverySpecialistAgent(self.llm, base_output_dir=self.base_output_dir)

    def execute(self, user_prompt: str, session_id: Optional[str] = None) -> WorkflowState:
        """
        Execute the end-to-end workflow pipeline synchronously.
        """
        state = WorkflowState(user_prompt=user_prompt)
        if session_id:
            state.session_id = session_id

        start_time = time.time()
        self.event_bus.publish(
            agent="Orchestrator",
            event_type="status",
            message=f"Starting AI Agent Workflow for session [{state.session_id}]...",
            payload={"prompt": user_prompt}
        )

        try:
            # ─────────────────────────────────────────────────────────────
            # Stage 1: Agent 1 (Interface & Medium)
            # ─────────────────────────────────────────────────────────────
            state = self.agent1.run(state, self.event_bus)

            # ─────────────────────────────────────────────────────────────
            # Stage 2: Agents 2 & 3 (Interpreter & Architect Debater)
            # ─────────────────────────────────────────────────────────────
            state = self.agent2_3.run(state, self.event_bus)

            # ─────────────────────────────────────────────────────────────
            # Stage 3 & 4: Agent 4 (Lead Coder) <-> Agent 5 (Strict QA) Loop
            # ─────────────────────────────────────────────────────────────
            qa_approved = False
            while not qa_approved:
                # Agent 4 writes or refactors code
                state = self.agent4.run(state, self.event_bus)

                # Agent 5 audits via AST and dynamic sandbox
                state = self.agent5.run(state, self.event_bus)

                last_qa = state.qa_history[-1] if state.qa_history else None
                if last_qa and last_qa.passed:
                    qa_approved = True
                else:
                    if state.qa_loop_count >= state.max_qa_loops:
                        self.event_bus.publish(
                            agent="Orchestrator",
                            event_type="qa",
                            message="Max QA loop limit reached. Proceeding to Supervisor review with warnings."
                        )
                        break
                    # Continue loop back to Agent 4

            # ─────────────────────────────────────────────────────────────
            # Stage 5: Agent 6 (Supervisor - Intent Review)
            # ─────────────────────────────────────────────────────────────
            state = self.agent6.run(state, self.event_bus)

            # ─────────────────────────────────────────────────────────────
            # Stage 6: Agent 7 (Delivery Specialist - Packaging)
            # ─────────────────────────────────────────────────────────────
            state = self.agent7.run(state, self.event_bus)

            state.completed_at = time.time()
            duration = round(state.completed_at - start_time, 2)

            # Relaying final progress confirmation via Agent 1
            self.event_bus.publish(
                agent=self.agent1.name,
                event_type="status",
                message=(
                    f"Workflow successfully completed in {duration}s! "
                    f"Package delivered by Agent 7 to '{state.delivery_package.target_dir}'."
                ),
                payload={"duration_seconds": duration, "package": state.delivery_package.to_dict()}
            )

        except Exception as e:
            state.status = WorkflowStatus.FAILED
            self.event_bus.publish(
                agent="Orchestrator",
                event_type="error",
                message=f"Critical Workflow Failure: {str(e)}",
                payload={"error": str(e)}
            )
            raise

        return state
