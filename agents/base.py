"""
Base Agent Interface for all 7 specialized agents.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.models import WorkflowState, AgentRole
from core.event_bus import EventBus
from core.llm_provider import BaseLLMProvider


class BaseAgent(ABC):
    def __init__(self, role: AgentRole, llm_provider: BaseLLMProvider):
        self.role = role
        self.llm = llm_provider

    @property
    def name(self) -> str:
        return self.role.value

    def log(self, event_bus: EventBus, event_type: str, message: str, payload: Optional[Dict[str, Any]] = None):
        """Helper to emit structured telemetry into the shared Event Bus."""
        event_bus.publish(
            agent=self.name,
            event_type=event_type,
            message=message,
            payload=payload or {}
        )

    @abstractmethod
    def run(self, state: WorkflowState, event_bus: EventBus) -> WorkflowState:
        """Execute agent workflow step, mutating and returning the state."""
        pass
