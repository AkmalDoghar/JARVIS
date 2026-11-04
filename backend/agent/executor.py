"""
JARVIS Phase 8 Component: Autonomous Agent Executor & Anti-Loop Circuit Breaker
Orchestrates multi-step plan execution, confirmation gates, circuit breaking, and emergency STOP.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from backend.agent.planner import TaskPlan, PlanStep
from backend.agent.memory import AgentContext
from backend.tools.registry import execute_tool
from backend.security.risk import get_tool_risk, RiskLevel


class AgentExecutor:
    """Manages active multi-step autonomous task execution with safety gates and emergency controls."""

    def __init__(self):
        self._current_plan: Optional[TaskPlan] = None
        self._context: Optional[AgentContext] = None
        self._is_stopped: bool = False
        self._lock = threading.Lock()
        self.execution_logs: List[str] = []

    def get_status(self) -> Dict[str, Any]:
        """Return the current execution plan and status."""
        with self._lock:
            if not self._current_plan:
                return {
                    "active": False,
                    "plan": None,
                    "is_stopped": self._is_stopped,
                    "logs": self.execution_logs[-25:],
                }
            return {
                "active": self._current_plan.status in ("executing", "waiting_for_confirmation"),
                "plan": self._current_plan.to_dict(),
                "is_stopped": self._is_stopped,
                "logs": self.execution_logs[-25:],
            }

    def log(self, message: str):
        """Append an executive log message."""
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {message}"
        self.execution_logs.append(entry)
        if self._context:
            self._context.add_log(message)
        print(f"[JARVIS Agent] {entry}")

    def stop_execution(self) -> Dict[str, Any]:
        """Emergency STOP control: Immediately aborts current running task."""
        with self._lock:
            self._is_stopped = True
            if self._current_plan:
                self._current_plan.status = "stopped"
                self._current_plan.completed_at = time.time()
                self._current_plan.summary = "Emergency Abort Triggered by User. Task stopped immediately."
            self.log("EMERGENCY STOP TRIGGERED: Execution aborted by user.")
            return {
                "success": True,
                "status": "stopped",
                "message": "Autonomous task halted immediately."
            }

    def execute_plan(self, plan: TaskPlan, auto_proceed: bool = True, reset_stop: bool = False) -> TaskPlan:
        """
        Execute the steps in a TaskPlan sequentially.
        Respects confirmation gates, anti-loop limits, and emergency aborts.
        """
        with self._lock:
            if not reset_stop and self._is_stopped:
                plan.status = "stopped"
                plan.completed_at = time.time()
                plan.summary = "Emergency Abort: Execution halted by emergency stop."
                self.log("Mission rejected: emergency stop is active.")
                return plan
            self._current_plan = plan
            self._context = AgentContext(task_id=plan.task_id, goal=plan.goal)
            self._is_stopped = False
            plan.status = "executing"
        
        self.log(f"Mission initialized: '{plan.goal}' ({len(plan.steps)} steps planned).")

        while plan.current_step_index < len(plan.steps):
            if self._is_stopped:
                plan.status = "stopped"
                plan.summary = "Execution aborted by emergency stop."
                break

            step = plan.steps[plan.current_step_index]
            step_num = step.step_number

            # Check if this step requires user confirmation / PIN before execution
            if step.requires_confirmation and not step.confirmed:
                step.status = "awaiting_confirmation"
                plan.status = "waiting_for_confirmation"
                self.log(f"Step {step_num} ('{step.title}') is {step.risk_level} risk. Awaiting user approval...")
                return plan

            # Mark step in-progress
            step.status = "in_progress"
            self.log(f"Executing Step {step_num}/{len(plan.steps)}: {step.title} (Tool: {step.tool_name})...")

            # Execute tool
            try:
                res = execute_tool(
                    tool_name=step.tool_name,
                    arguments=step.tool_args,
                    confirmed=step.confirmed,
                    pin=step.pin
                )
                step.executed_at = time.time()
                step.result = res
                
                # Check outcome
                is_success = res.get("success", False) if isinstance(res, dict) else False
                # If tool returned pending confirmation
                if isinstance(res, dict) and res.get("status") == "PENDING_CONFIRMATION":
                    step.status = "awaiting_confirmation"
                    plan.status = "waiting_for_confirmation"
                    step.requires_confirmation = True
                    step.requires_pin = res.get("requires_pin", False)
                    self.log(f"Step {step_num} halted for security confirmation: {res.get('message')}")
                    return plan

                if is_success:
                    step.status = "completed"
                    self._context.record_step_result(step_num, step.tool_name, step.tool_args, res, "completed")
                    self.log(f"Step {step_num} COMPLETED successfully.")
                    plan.current_step_index += 1
                else:
                    err_msg = res.get("error") if isinstance(res, dict) else "Action failed"
                    step.error = str(err_msg)
                    self._handle_step_failure(plan, step, err_msg)
                    if plan.status == "failed":
                        break
            except Exception as e:
                err_msg = str(e)
                step.error = err_msg
                self._handle_step_failure(plan, step, err_msg)
                if plan.status == "failed":
                    break

        # Check final status
        if plan.status not in ("failed", "stopped", "waiting_for_confirmation"):
            if plan.current_step_index >= len(plan.steps):
                plan.status = "completed"
                plan.completed_at = time.time()
                plan.summary = self._generate_final_summary(plan)
                self.log(f"Mission Finished: {plan.summary}")

        return plan

    def _handle_step_failure(self, plan: TaskPlan, step: PlanStep, err_msg: str):
        """Handle step failure and enforce the Anti-Loop Circuit Breaker (Max 3 retries)."""
        step_num = step.step_number
        current_retries = plan.retry_counts.get(step_num, 0) + 1
        plan.retry_counts[step_num] = current_retries

        self.log(f"Step {step_num} failed (Attempt {current_retries}/{plan.max_retries_per_step}): {err_msg}")

        if current_retries >= plan.max_retries_per_step:
            # CIRCUIT BREAKER ACTIVATED
            step.status = "failed"
            plan.status = "failed"
            plan.completed_at = time.time()
            summary = (
                f"CIRCUIT BREAKER TRIGGERED: Step {step_num} ('{step.title}') failed {current_retries} times. "
                f"Execution halted to prevent runaway loops. Error: {err_msg}"
            )
            plan.summary = summary
            self.log(f"CRITICAL: {summary}")
        else:
            # Allow automatic retry
            time.sleep(0.5)

    def confirm_step(self, task_id: str, pin: Optional[str] = None) -> TaskPlan:
        """Confirm a paused/waiting step with optional PIN and resume execution."""
        if not self._current_plan or self._current_plan.task_id != task_id:
            raise ValueError(f"Task plan '{task_id}' is not active or does not exist.")

        plan = self._current_plan
        if plan.current_step_index < len(plan.steps):
            step = plan.steps[plan.current_step_index]
            step.confirmed = True
            step.pin = pin
            self.log(f"Step {step.step_number} confirmed by user. Resuming autonomous execution...")
            return self.execute_plan(plan)
        return plan

    def _generate_final_summary(self, plan: TaskPlan) -> str:
        """Create a crisp, structured post-mission briefing."""
        total = len(plan.steps)
        completed = sum(1 for s in plan.steps if s.status == "completed")
        failed = sum(1 for s in plan.steps if s.status == "failed")
        return f"Autonomous Mission Completed. {completed}/{total} steps executed successfully ({failed} failed)."


# Global singleton executor instance
global_agent_executor = AgentExecutor()
