"""
JARVIS Phase 8 Test Suite: Autonomous Multi-Step Agent & Circuit Breaker
Acceptance Tests:
1. Plan Generation: Structured multi-step plan produced for complex user goals.
2. Step-by-Step Status Visibility: Plan tracks pending -> in_progress -> completed transitions.
3. Confirmation Safety Gate: MEDIUM / HIGH risk steps halt execution until confirmed.
4. Anti-Loop Circuit Breaker: Enforces max 3 retries on failure before tripping and stopping execution.
5. Emergency STOP: stop_execution halts active task immediately.
6. Execution Summary: Generates a clear structured post-mission summary of completed vs failed steps.
7. Registry Integration: execute_agent_mission and create_agent_plan are registered and callable.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent.planner import generate_plan, TaskPlan, PlanStep, TEMPLATES
from backend.agent.executor import AgentExecutor
from backend.security.risk import get_tool_risk, RiskLevel
from backend.tools.registry import execute_tool, JARVIS_TOOLS_SCHEMA, TOOL_HANDLERS


class TestPhase8AutonomousAgent(unittest.TestCase):

    def setUp(self):
        self.executor = AgentExecutor()

    def test_01_plan_generation_template(self):
        """Test structured plan generation from deployment prep template."""
        plan = generate_plan(goal="Prepare project for deployment", template_key="deployment_prep")
        self.assertIsInstance(plan, TaskPlan)
        self.assertGreater(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].tool_name, "inspect_project")
        self.assertEqual(plan.status, "planned")
        # Check serialization
        d = plan.to_dict()
        self.assertIn("steps", d)
        self.assertIn("task_id", d)
        self.assertEqual(d["total_steps"], len(plan.steps))
        print("[SUCCESS] Test 1: Plan generated successfully with structured steps.")

    def test_02_step_status_visibility_and_execution(self):
        """Test that safe steps execute sequentially and update status correctly."""
        step1 = PlanStep(
            step_number=1,
            title="Inspect Hardware",
            description="Query CPU and RAM",
            tool_name="get_system_status",
            tool_args={}
        )
        step2 = PlanStep(
            step_number=2,
            title="Check Open Windows",
            description="List active desktop windows",
            tool_name="get_open_windows",
            tool_args={}
        )
        plan = TaskPlan(goal="Quick Diagnostic Audit", steps=[step1, step2])
        res_plan = self.executor.execute_plan(plan)

        self.assertEqual(res_plan.status, "completed")
        self.assertEqual(res_plan.steps[0].status, "completed")
        self.assertEqual(res_plan.steps[1].status, "completed")
        self.assertIsNotNone(res_plan.steps[0].result)
        self.assertIn("Autonomous Mission Completed", res_plan.summary)
        print("[SUCCESS] Test 2: Step-by-step status transitions and completion verified.")

    def test_03_confirmation_gate_for_medium_risk(self):
        """Test that a step with MEDIUM or HIGH risk halts execution for user confirmation."""
        # lock_computer is MEDIUM risk in risk.py
        step1 = PlanStep(
            step_number=1,
            title="Lock Laptop",
            description="Secure desktop screen",
            tool_name="lock_computer",
            tool_args={}
        )
        plan = TaskPlan(goal="Secure Laptop", steps=[step1])
        res_plan = self.executor.execute_plan(plan)

        self.assertEqual(res_plan.status, "waiting_for_confirmation")
        self.assertEqual(res_plan.steps[0].status, "awaiting_confirmation")
        self.assertTrue(res_plan.steps[0].requires_confirmation)
        print("[SUCCESS] Test 3: Safety confirmation gate halted execution for MEDIUM risk step.")

    def test_04_anti_loop_circuit_breaker(self):
        """Test that repeated step failures trip the circuit breaker at max 3 retries."""
        # Use an invalid file path to force a deliberate failure
        step_failing = PlanStep(
            step_number=1,
            title="Read Nonexistent File",
            description="Attempt to read a missing file",
            tool_name="read_file",
            tool_args={"file_path": "non_existent_system_file_12345.xyz"}
        )
        plan = TaskPlan(goal="Test Circuit Breaker", steps=[step_failing], max_retries_per_step=3)
        res_plan = self.executor.execute_plan(plan)

        self.assertEqual(res_plan.status, "failed")
        self.assertEqual(res_plan.steps[0].status, "failed")
        self.assertEqual(res_plan.retry_counts.get(1), 3)
        self.assertIn("CIRCUIT BREAKER TRIGGERED", res_plan.summary)
        print("[SUCCESS] Test 4: Anti-loop circuit breaker tripped after 3 failed attempts.")

    def test_05_emergency_stop(self):
        """Test emergency STOP control halts active execution immediately."""
        step1 = PlanStep(step_number=1, title="Telemetry Check", description="Inspect system", tool_name="get_system_status")
        step2 = PlanStep(step_number=2, title="Git Check", description="Check git", tool_name="run_git_status")
        plan = TaskPlan(goal="Emergency Stop Mission", steps=[step1, step2])
        
        # Trigger stop right away
        self.executor.stop_execution()
        res_plan = self.executor.execute_plan(plan)

        self.assertEqual(res_plan.status, "stopped")
        self.assertIn("Emergency", res_plan.summary)
        print("[SUCCESS] Test 5: Emergency STOP successfully aborted task execution.")

    def test_06_final_mission_summary(self):
        """Test generation of final structured executive summary."""
        step1 = PlanStep(step_number=1, title="Hardware Telemetry", description="Telemetry", tool_name="get_system_status")
        plan = TaskPlan(goal="Mission Summary Test", steps=[step1])
        res_plan = self.executor.execute_plan(plan)

        self.assertEqual(res_plan.status, "completed")
        self.assertIsNotNone(res_plan.summary)
        self.assertIn("1/1 steps executed successfully", res_plan.summary)
        print("[SUCCESS] Test 6: Final mission summary accurately generated.")

    def test_07_registry_integration(self):
        """Test that Phase 8 tools are present in registry and executable."""
        self.assertIn("create_agent_plan", TOOL_HANDLERS)
        self.assertIn("execute_agent_mission", TOOL_HANDLERS)
        self.assertIn("stop_agent_mission", TOOL_HANDLERS)

        # Call create_agent_plan via execute_tool
        res = execute_tool("create_agent_plan", {"goal": "prepare project for deployment"})
        self.assertTrue(res.get("success"))
        self.assertIn("steps", res["result"])
        print("[SUCCESS] Test 7: Registry dispatch integration verified for Phase 8 tools.")


if __name__ == "__main__":
    unittest.main()
