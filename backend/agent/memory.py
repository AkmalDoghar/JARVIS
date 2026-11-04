"""
JARVIS Phase 8 Component: Agent Execution Context & Intermediate Memory
Stores observations, intermediate tool outputs, and variables across multi-step plans.
"""

from typing import Dict, Any, List, Optional
import time


class AgentContext:
    """Accumulates and formats intermediate observations for multi-step agent workflows."""

    def __init__(self, task_id: str, goal: str):
        self.task_id = task_id
        self.goal = goal
        self.variables: Dict[str, Any] = {}
        self.step_history: List[Dict[str, Any]] = []
        self.logs: List[str] = []
        self.created_at = time.time()

    def record_step_result(self, step_number: int, tool_name: str, args: Dict[str, Any], result: Dict[str, Any], status: str):
        """Record the output of a completed or failed step."""
        entry = {
            "step_number": step_number,
            "tool_name": tool_name,
            "arguments": args,
            "status": status,
            "result": result,
            "timestamp": time.time()
        }
        self.step_history.append(entry)
        
        # Extract helpful variables
        if isinstance(result, dict):
            for k, v in result.items():
                if k in ("path", "project_path", "error", "message", "count", "url"):
                    self.variables[f"step{step_number}_{k}"] = v

    def add_log(self, message: str):
        """Append a timestamped log entry."""
        ts = time.strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {message}")

    def get_summary_context(self) -> str:
        """Produce a compact text summary of previous steps for downstream LLM reasoning."""
        if not self.step_history:
            return "No previous steps executed yet."
        
        lines = []
        for s in self.step_history:
            st = s["status"]
            tool = s["tool_name"]
            msg = ""
            if isinstance(s["result"], dict):
                msg = s["result"].get("message") or s["result"].get("error") or str(s["result"])[:100]
            lines.append(f"Step {s['step_number']} ({tool}) -> {st}: {msg}")
        return "\n".join(lines)
