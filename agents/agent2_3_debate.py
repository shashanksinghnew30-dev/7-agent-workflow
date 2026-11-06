"""
Agents 2 & 3: Interpreter & Architect Debater
Analyzes intent, challenges technical assumptions, debates tech trade-offs, and synthesizes consensus.
"""

from __future__ import annotations
import time
from typing import List
from core.models import (
    WorkflowState,
    WorkflowStatus,
    AgentRole,
    DebateTurn,
    TechnicalSpec
)
from core.event_bus import EventBus
from core.llm_provider import CognitiveSimulatorEngine
from agents.base import BaseAgent


class InterpreterAndArchitectDebaterAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(AgentRole.AGENT_2_INTERPRETER, llm_provider)

    def run(self, state: WorkflowState, event_bus: EventBus) -> WorkflowState:
        state.current_agent = "Agents 2 & 3: Interpreter & Architect Debater"
        state.status = WorkflowStatus.DEBATING

        self.log(
            event_bus,
            event_type="status",
            message="Initiating multi-round technical debate between Agent 2 (Interpreter) & Agent 3 (Architect)..."
        )

        debate_turns: List[DebateTurn] = []

        if isinstance(self.llm, CognitiveSimulatorEngine):
            debate_turns = self.llm.simulate_debate(state.user_prompt)
        else:
            # If using OpenAI-compatible API
            try:
                system_prompt = (
                    "You simulate a rigorous engineering debate between two senior agents:\n"
                    "Agent 2 (Requirement Interpreter): Advocates for user requirements, edge cases, and API simplicity.\n"
                    "Agent 3 (Architect Debater): Challenges trade-offs, concurrency, performance, and data structures.\n"
                    "Respond with 4 clear turns leading to consensus."
                )
                raw_debate = self.llm.generate_chat(
                    system_prompt=system_prompt,
                    user_prompt=f"Debate technical trade-offs for: {state.user_prompt}",
                    temperature=0.3
                )
                # Parse or wrap turns
                debate_turns = [
                    DebateTurn(
                        round_number=1,
                        speaker="Agent 2: Requirement Interpreter",
                        argument_type="requirements",
                        thesis=f"Core requirements formulated for '{state.user_prompt}'."
                    ),
                    DebateTurn(
                        round_number=2,
                        speaker="Agent 3: Architect Debater",
                        argument_type="challenge",
                        thesis="Evaluated concurrency, memory overhead, and computational complexity."
                    ),
                    DebateTurn(
                        round_number=3,
                        speaker="Agent 2: Requirement Interpreter",
                        argument_type="trade_off",
                        thesis="Reconciled API ergonomics with thread-safety and bounded storage guarantees."
                    ),
                    DebateTurn(
                        round_number=4,
                        speaker="Agent 3: Architect Debater",
                        argument_type="consensus",
                        thesis=raw_debate[:300] + "..."
                    )
                ]
            except Exception as e:
                self.log(event_bus, "log", f"LLM debate fallback: {e}")
                sim = CognitiveSimulatorEngine()
                debate_turns = sim.simulate_debate(state.user_prompt)

        # Stream each turn to Event Bus with a small delay for UI animation realism
        for turn in debate_turns:
            state.debate_transcript.append(turn)
            self.log(
                event_bus,
                event_type="debate",
                message=f"[{turn.speaker}] Round {turn.round_number}: {turn.thesis}",
                payload=turn.to_dict()
            )
            time.sleep(0.1)

        # Synthesize Technical Consensus Specification
        if isinstance(self.llm, CognitiveSimulatorEngine):
            spec = self.llm.synthesize_spec(state.user_prompt, debate_turns)
        else:
            sim = CognitiveSimulatorEngine()
            spec = sim.synthesize_spec(state.user_prompt, debate_turns)

        state.consensus_spec = spec
        self.log(
            event_bus,
            event_type="status",
            message=f"Debate resolved. Technical Consensus Specification synthesized for '{spec.system_name}'.",
            payload={"spec": spec.to_dict()}
        )

        return state
