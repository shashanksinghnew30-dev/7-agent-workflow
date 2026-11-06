"""
Comprehensive Test Suite for 7-Agent AI Workflow.
Verifies all agents, telemetry event bus, AST validation, dynamic testing,
self-healing QA loopback, supervisor review, and packaging.
"""

import os
import unittest
import tempfile
import zipfile
from core.models import (
    WorkflowState,
    WorkflowStatus,
    AgentRole,
    QAReport,
    TechnicalSpec
)
from core.event_bus import EventBus
from core.llm_provider import CognitiveSimulatorEngine
from core.orchestrator import WorkflowOrchestrator
from agents import (
    InterfaceAndMediumAgent,
    InterpreterAndArchitectDebaterAgent,
    LeadCoderAgent,
    StrictQABugTesterAgent,
    SupervisorAgent,
    DeliverySpecialistAgent,
)


class TestAIAgentWorkflow(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.engine = CognitiveSimulatorEngine(demo_qa_loopback=False)

    def test_agent1_interface_ingestion(self):
        agent = InterfaceAndMediumAgent(self.engine)
        state = WorkflowState(user_prompt="Build a high performance LRU Cache")
        state = agent.run(state, self.bus)

        self.assertEqual(state.status, WorkflowStatus.INITIALIZING)
        self.assertIn("target_domain", state.interface_metadata)
        self.assertEqual(state.current_agent, AgentRole.AGENT_1_INTERFACE.value)

    def test_agent2_3_debate_and_spec_synthesis(self):
        agent = InterpreterAndArchitectDebaterAgent(self.engine)
        state = WorkflowState(user_prompt="Build an LRU cache with TTL")
        state = agent.run(state, self.bus)

        self.assertEqual(state.status, WorkflowStatus.DEBATING)
        self.assertGreaterEqual(len(state.debate_transcript), 4)
        self.assertIsNotNone(state.consensus_spec)
        self.assertIsInstance(state.consensus_spec, TechnicalSpec)
        self.assertGreater(len(state.consensus_spec.tech_trade_offs_resolved), 0)

    def test_agent4_lead_coder_generation(self):
        agent2_3 = InterpreterAndArchitectDebaterAgent(self.engine)
        agent4 = LeadCoderAgent(self.engine)

        state = WorkflowState(user_prompt="Build an LRU cache with TTL")
        state = agent2_3.run(state, self.bus)
        state = agent4.run(state, self.bus)

        self.assertEqual(state.status, WorkflowStatus.CODING)
        self.assertIn("src/cache_core.py", state.source_files)
        self.assertIn("tests/test_cache.py", state.source_files)
        self.assertIn("run.py", state.source_files)

    def test_agent5_strict_qa_sandbox_execution(self):
        agent2_3 = InterpreterAndArchitectDebaterAgent(self.engine)
        agent4 = LeadCoderAgent(self.engine)
        agent5 = StrictQABugTesterAgent(self.engine)

        state = WorkflowState(user_prompt="Build an LRU cache with TTL")
        state = agent2_3.run(state, self.bus)
        state = agent4.run(state, self.bus)
        state = agent5.run(state, self.bus)

        self.assertEqual(len(state.qa_history), 1)
        last_qa = state.qa_history[0]
        self.assertTrue(last_qa.passed)
        self.assertTrue(last_qa.syntax_valid)
        self.assertGreater(last_qa.tests_executed, 0)
        self.assertEqual(last_qa.tests_failed, 0)

    def test_agent5_to_agent4_loopback_on_defect(self):
        # Enable demo defect simulation
        engine_with_bug = CognitiveSimulatorEngine(demo_qa_loopback=True)
        agent2_3 = InterpreterAndArchitectDebaterAgent(engine_with_bug)
        agent4 = LeadCoderAgent(engine_with_bug)
        agent5 = StrictQABugTesterAgent(engine_with_bug)

        state = WorkflowState(user_prompt="Build an LRU cache with TTL")
        state = agent2_3.run(state, self.bus)

        # 1st Pass: Agent 4 injects defect
        state = agent4.run(state, self.bus)
        # Agent 5 catches defect and triggers loopback
        state = agent5.run(state, self.bus)

        self.assertEqual(state.qa_loop_count, 1)
        self.assertFalse(state.qa_history[0].passed)

        # 2nd Pass: Agent 4 consumes QA feedback and fixes code
        state = agent4.run(state, self.bus)
        # Agent 5 re-tests and passes
        state = agent5.run(state, self.bus)

        self.assertEqual(len(state.qa_history), 2)
        self.assertTrue(state.qa_history[1].passed)

    def test_agent6_supervisor_evaluation(self):
        agent6 = SupervisorAgent(self.engine)
        state = WorkflowState(user_prompt="Build a thread-safe LRU Cache")
        state.qa_history.append(
            QAReport(
                passed=True,
                loop_iteration=1,
                syntax_valid=True,
                tests_executed=5,
                tests_passed=5,
                tests_failed=0,
                execution_stdout="",
                execution_stderr="",
                quality_score=100.0
            )
        )
        state = agent6.run(state, self.bus)

        self.assertIsNotNone(state.supervisor_review)
        self.assertTrue(state.supervisor_review.approved)
        self.assertGreaterEqual(state.supervisor_review.alignment_score, 85.0)

    def test_agent7_delivery_and_packaging(self):
        with tempfile.TemporaryDirectory() as tmp_output:
            agent2_3 = InterpreterAndArchitectDebaterAgent(self.engine)
            agent4 = LeadCoderAgent(self.engine)
            agent7 = DeliverySpecialistAgent(self.engine, base_output_dir=tmp_output)

            state = WorkflowState(user_prompt="Build an LRU cache with TTL")
            state = agent2_3.run(state, self.bus)
            state = agent4.run(state, self.bus)
            state = agent7.run(state, self.bus)

            self.assertEqual(state.status, WorkflowStatus.COMPLETED)
            self.assertIsNotNone(state.delivery_package)
            self.assertTrue(os.path.exists(state.delivery_package.zip_path))
            self.assertTrue(zipfile.is_zipfile(state.delivery_package.zip_path))

    def test_full_orchestrator_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp_output:
            orchestrator = WorkflowOrchestrator(
                llm_provider=self.engine,
                event_bus=self.bus,
                base_output_dir=tmp_output
            )
            state = orchestrator.execute("Build a thread-safe token bucket rate limiter")

            self.assertEqual(state.status, WorkflowStatus.COMPLETED)
            self.assertIsNotNone(state.delivery_package)
            self.assertTrue(state.supervisor_review.approved)
            self.assertTrue(state.qa_history[-1].passed)


if __name__ == "__main__":
    unittest.main()
