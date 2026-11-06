"""
Agent 5: Strict QA & Bug Tester
Audits code via Static AST analysis and Dynamic Sandbox Unit Testing.
Triggers circular loopback to Agent 4 (Lead Coder) when defects are detected.
"""

from __future__ import annotations
import ast
import os
import sys
import tempfile
import subprocess
from core.models import (
    WorkflowState,
    WorkflowStatus,
    AgentRole,
    QAReport,
    QAFailureDetail
)
from core.event_bus import EventBus
from agents.base import BaseAgent


class StrictQABugTesterAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(AgentRole.AGENT_5_STRICT_QA, llm_provider)

    def run(self, state: WorkflowState, event_bus: EventBus) -> WorkflowState:
        state.current_agent = self.name
        state.status = WorkflowStatus.QA_AUDIT

        iteration = state.qa_loop_count + 1
        self.log(
            event_bus,
            event_type="qa",
            message=f"Agent 5 initiating Strict QA Audit (Pass #{iteration})..."
        )

        # Stage 1: Static AST Parsing
        syntax_errors = []
        for path, file_obj in state.source_files.items():
            if path.endswith(".py"):
                try:
                    ast.parse(file_obj.content, filename=path)
                except SyntaxError as syn_err:
                    syntax_errors.append(
                        QAFailureDetail(
                            failure_type="SyntaxError",
                            location=f"{path}:{syn_err.lineno}:{syn_err.offset}",
                            error_message=str(syn_err.msg),
                            suggested_fix="Fix Python syntax syntax error."
                        )
                    )

        if syntax_errors:
            self.log(
                event_bus,
                event_type="qa",
                message=f"[QA FAILED] Static AST analysis found {len(syntax_errors)} syntax defect(s).",
                payload={"errors": [e.to_dict() for e in syntax_errors]}
            )
            report = QAReport(
                passed=False,
                loop_iteration=iteration,
                syntax_valid=False,
                tests_executed=0,
                tests_passed=0,
                tests_failed=len(syntax_errors),
                execution_stdout="",
                execution_stderr="Syntax errors detected during static analysis.",
                failures=syntax_errors,
                quality_score=40.0
            )
            state.qa_history.append(report)
            return self._handle_loopback(state, event_bus, report)

        # Stage 2: Dynamic Execution in Isolated Sandbox
        test_file_path = None
        for path in state.source_files.keys():
            if "test" in path:
                test_file_path = path
                break

        passed = True
        test_stdout = ""
        test_stderr = ""
        failures = []
        executed_count = 0
        passed_count = 0
        failed_count = 0

        # Execute in temporary sandbox directory
        with tempfile.TemporaryDirectory(prefix="agent_qa_sandbox_") as tmpdir:
            # Write out all files
            for rel_path, file_obj in state.source_files.items():
                full_path = os.path.join(tmpdir, rel_path.replace("/", os.sep))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file_obj.content)

            # Ensure __init__.py exists in src and tests
            for d in ["src", "tests"]:
                init_p = os.path.join(tmpdir, d, "__init__.py")
                if not os.path.exists(init_p):
                    os.makedirs(os.path.dirname(init_p), exist_ok=True)
                    with open(init_p, "w", encoding="utf-8") as f:
                        f.write("")

            # Find test runner target
            target_test = test_file_path if test_file_path else "tests"
            cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                test_stdout = proc.stdout
                test_stderr = proc.stderr

                # Parse unittest output format (e.g., 'Ran 6 tests in 0.05s \n OK' or 'FAILED (failures=1)')
                # In unittest, test run summary is output to stderr
                combined_output = test_stderr + "\n" + test_stdout

                if proc.returncode == 0 and "OK" in combined_output:
                    passed = True
                    # Extract executed count if available
                    for line in combined_output.splitlines():
                        if line.startswith("Ran "):
                            parts = line.split()
                            if len(parts) >= 2 and parts[1].isdigit():
                                executed_count = int(parts[1])
                                passed_count = executed_count
                else:
                    passed = False
                    failed_count = 1
                    failures.append(
                        QAFailureDetail(
                            failure_type="AssertionFailure",
                            location=target_test,
                            error_message=test_stderr[:350] or "Assertion failed during unit test run.",
                            suggested_fix="Align core implementation with test assertions."
                        )
                    )
            except subprocess.TimeoutExpired:
                passed = False
                failed_count = 1
                test_stderr = "Test execution timed out (potential infinite loop or deadlock)."
                failures.append(
                    QAFailureDetail(
                        failure_type="TimeoutError",
                        location=target_test,
                        error_message=test_stderr,
                        suggested_fix="Check for infinite loops or blocking locks."
                    )
                )
            except Exception as ex:
                passed = False
                failed_count = 1
                test_stderr = f"Sandbox execution error: {str(ex)}"
                failures.append(
                    QAFailureDetail(
                        failure_type="ExecutionError",
                        location=target_test,
                        error_message=test_stderr,
                        suggested_fix="Ensure all imports and paths are properly resolved."
                    )
                )

        score = 100.0 if passed else max(0.0, 100.0 - (len(failures) * 35.0))
        report = QAReport(
            passed=passed,
            loop_iteration=iteration,
            syntax_valid=True,
            tests_executed=executed_count,
            tests_passed=passed_count,
            tests_failed=failed_count,
            execution_stdout=test_stdout,
            execution_stderr=test_stderr,
            failures=failures,
            quality_score=score
        )
        state.qa_history.append(report)

        if not passed:
            return self._handle_loopback(state, event_bus, report)

        # If tests passed:
        self.log(
            event_bus,
            event_type="qa",
            message=f"[QA PASSED] All {executed_count} unit tests passed successfully with 100% assertions satisfied.",
            payload=report.to_dict()
        )
        return state

    def _handle_loopback(self, state: WorkflowState, event_bus: EventBus, report: QAReport) -> WorkflowState:
        """Trigger loopback to Agent 4 if retry threshold is not exceeded."""
        if state.qa_loop_count < state.max_qa_loops:
            state.qa_loop_count += 1
            self.log(
                event_bus,
                event_type="qa",
                message=(
                    f"[QA AUDIT DEFECT DETECTED] Triggering circular feedback loop ({state.qa_loop_count}/{state.max_qa_loops}) "
                    f"-> Looping back to Agent 4 (Lead Coder) with bug diagnostic report."
                ),
                payload={"report": report.to_dict(), "next_step": "AGENT_4_LEAD_CODER"}
            )
        else:
            self.log(
                event_bus,
                event_type="qa",
                message=f"[QA WARNING] Maximum loop limit ({state.max_qa_loops}) reached. Escalating to Supervisor."
            )
        return state
