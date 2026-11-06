"""
Agent 1: Interface & Medium
Takes user prompt, parses constraints, initializes state, and relays progress to the user.
"""

import time
from core.models import WorkflowState, WorkflowStatus, AgentRole
from core.event_bus import EventBus
from agents.base import BaseAgent


class InterfaceAndMediumAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(AgentRole.AGENT_1_INTERFACE, llm_provider)

    def run(self, state: WorkflowState, event_bus: EventBus) -> WorkflowState:
        state.current_agent = self.name
        state.status = WorkflowStatus.INITIALIZING

        self.log(
            event_bus,
            event_type="status",
            message=f"Agent 1 connected. Ingesting prompt for Session [{state.session_id}]...",
            payload={"session_id": state.session_id, "prompt": state.user_prompt}
        )

        # Analyze and sanitize prompt
        cleaned_prompt = state.user_prompt.strip()
        if not cleaned_prompt:
            cleaned_prompt = "Build a high-performance thread-safe LRU Cache with TTL and statistics"
            state.user_prompt = cleaned_prompt

        # Estimate complexity & domain classification
        prompt_words = cleaned_prompt.split()
        complexity = "HIGH" if len(prompt_words) > 15 else "STANDARD"
        
        domain = "Concurrency / Systems"
        if any(k in cleaned_prompt.lower() for k in ["api", "rest", "web", "http"]):
            domain = "Web Services & Networking"
        elif any(k in cleaned_prompt.lower() for k in ["data", "ml", "tensor", "model"]):
            domain = "Machine Learning / Analytics"

        metadata = {
            "ingested_at": time.time(),
            "character_count": len(cleaned_prompt),
            "word_count": len(prompt_words),
            "estimated_complexity": complexity,
            "target_domain": domain,
            "client_channel": "Browser UI / Python Terminal"
        }
        state.interface_metadata = metadata

        self.log(
            event_bus,
            event_type="status",
            message=f"Prompt successfully parsed [{domain} | Complexity: {complexity}]. Relaying to Agents 2 & 3.",
            payload=metadata
        )

        return state
