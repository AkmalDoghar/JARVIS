"""
JARVIS Phase 8 Component: Autonomous Task Planner & Plan Generation
Decomposes complex natural language goals into structured multi-step execution plans.
Strictly maps steps to allowlisted tools and enforces risk levels and confirmation gates.
"""

import os
import re
import json
import uuid
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from backend.security.risk import get_tool_risk, RiskLevel
from backend.tools.registry import TOOL_HANDLERS, JARVIS_TOOLS_SCHEMA

load_dotenv()


class PlanStep:
    def __init__(
        self,
        step_number: int,
        title: str,
        description: str,
        tool_name: str,
        tool_args: Optional[Dict[str, Any]] = None,
        risk_level: Optional[str] = None,
        requires_confirmation: bool = False,
        requires_pin: bool = False,
    ):
        self.step_number = step_number
        self.title = title
        self.description = description
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        
        # Calculate risk level dynamically if not provided
        if not risk_level:
            calculated_risk = get_tool_risk(tool_name, self.tool_args)
            self.risk_level = calculated_risk.value if hasattr(calculated_risk, "value") else str(calculated_risk)
        else:
            self.risk_level = risk_level.upper()

        self.requires_confirmation = requires_confirmation or (self.risk_level in ("MEDIUM", "HIGH"))
        self.requires_pin = requires_pin or (self.risk_level == "HIGH")
        self.confirmed = False
        self.pin: Optional[str] = None
        self.status = "pending"  # pending | in_progress | completed | failed | skipped | awaiting_confirmation
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.executed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "title": self.title,
            "description": self.description,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation,
            "requires_pin": self.requires_pin,
            "confirmed": self.confirmed,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "executed_at": self.executed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        step = cls(
            step_number=data["step_number"],
            title=data["title"],
            description=data["description"],
            tool_name=data["tool_name"],
            tool_args=data.get("tool_args", {}),
            risk_level=data.get("risk_level"),
            requires_confirmation=data.get("requires_confirmation", False),
            requires_pin=data.get("requires_pin", False),
        )
        step.confirmed = data.get("confirmed", False)
        step.status = data.get("status", "pending")
        step.result = data.get("result")
        step.error = data.get("error")
        step.executed_at = data.get("executed_at")
        return step


class TaskPlan:
    def __init__(
        self,
        goal: str,
        steps: Optional[List[PlanStep]] = None,
        task_id: Optional[str] = None,
        max_retries_per_step: int = 3,
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.goal = goal
        self.steps = steps or []
        self.status = "planned"  # planned | executing | waiting_for_confirmation | completed | failed | stopped
        self.current_step_index = 0
        self.max_retries_per_step = max_retries_per_step
        self.retry_counts: Dict[int, int] = {}
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "max_retries_per_step": self.max_retries_per_step,
            "retry_counts": self.retry_counts,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "summary": self.summary,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskPlan":
        plan = cls(
            goal=data["goal"],
            task_id=data.get("task_id"),
            max_retries_per_step=data.get("max_retries_per_step", 3),
        )
        plan.status = data.get("status", "planned")
        plan.current_step_index = data.get("current_step_index", 0)
        plan.retry_counts = {int(k): v for k, v in data.get("retry_counts", {}).items()}
        plan.created_at = data.get("created_at", time.time())
        plan.completed_at = data.get("completed_at")
        plan.summary = data.get("summary")
        plan.steps = [PlanStep.from_dict(s) for s in data.get("steps", [])]
        return plan


# ─────────────────────────────────────────────
# Pre-defined Core Autonomous Templates
# ─────────────────────────────────────────────
TEMPLATES = {
    "deployment_prep": {
        "title": "Prepare Project for Deployment",
        "description": "Inspect project structure, verify git status, run production build/tests, check hardware resources, and report readiness.",
        "steps": [
            {
                "title": "Inspect Frontend Package & Structure",
                "description": "Examine package.json and project files in the frontend workspace.",
                "tool_name": "inspect_project",
                "tool_args": {"folder_path": "frontend"}
            },
            {
                "title": "Audit Git Status & Clean Tree",
                "description": "Check current Git branch, modified files, and uncommitted changes.",
                "tool_name": "run_git_status",
                "tool_args": {}
            },
            {
                "title": "Run Development Test Verification",
                "description": "Verify code compilation and run unit test command.",
                "tool_name": "run_dev_tests",
                "tool_args": {"command": "npm run build -- --no-lint"}
            },
            {
                "title": "Inspect Hardware & System Capacity",
                "description": "Ensure CPU, RAM, and disk have adequate capacity for deployment.",
                "tool_name": "get_system_status",
                "tool_args": {}
            }
        ]
    },
    "bug_diagnosis": {
        "title": "Scan, Diagnose & Fix Code Errors",
        "description": "Run dev tests to identify compilation or lint errors, search offending files, and verify fixes.",
        "steps": [
            {
                "title": "Execute Dev Tests to Isolate Error",
                "description": "Run npm build/test command to surface failing lines or modules.",
                "tool_name": "run_dev_tests",
                "tool_args": {"command": "npm run build"}
            },
            {
                "title": "Search Codebase for Error Signatures",
                "description": "Locate problem tokens and component references across the repo.",
                "tool_name": "search_codebase",
                "tool_args": {"query": "error", "folder_path": "frontend/src"}
            },
            {
                "title": "Review Recent File Differences",
                "description": "Inspect recent git modifications that may have introduced the regression.",
                "tool_name": "run_git_diff",
                "tool_args": {}
            }
        ]
    },
    "workspace_audit": {
        "title": "Full Developer Workspace Audit",
        "description": "Inspect git status, open development windows, system telemetry, and creator profile.",
        "steps": [
            {
                "title": "Check Active Git Status",
                "description": "Inspect branch status and working directory changes.",
                "tool_name": "run_git_status",
                "tool_args": {}
            },
            {
                "title": "Inspect Open Desktop Windows",
                "description": "List visible application windows to verify active development tools.",
                "tool_name": "get_open_windows",
                "tool_args": {}
            },
            {
                "title": "Retrieve Hardware Telemetry",
                "description": "Query live CPU, RAM, and battery levels.",
                "tool_name": "get_system_status",
                "tool_args": {}
            },
            {
                "title": "Sync Creator Focus & Goals",
                "description": "Review daily priority tasks and connected accounts.",
                "tool_name": "get_today_focus",
                "tool_args": {}
            }
        ]
    }
}


def _match_template_by_goal(goal: str) -> Optional[str]:
    """Detect if the user's goal matches one of the pre-optimized engineering workflows."""
    g = goal.lower().strip()
    if any(k in g for k in ("deploy", "deployment", "production", "prepare project", "tayyar karo")):
        return "deployment_prep"
    if any(k in g for k in ("diagnose", "fix error", "fix bug", "find error", "error theek", "bug fix")):
        return "bug_diagnosis"
    if any(k in g for k in ("audit", "workspace", "system audit", "check everything", "status check")):
        return "workspace_audit"
    return None


def generate_plan(goal: str, template_key: Optional[str] = None, context: Optional[str] = None) -> TaskPlan:
    """
    Generate an autonomous multi-step execution plan for the specified goal.
    Uses pre-optimized deterministic templates when applicable, or calls LLM for dynamic goals.
    """
    # 1. Check template match
    chosen_key = template_key or _match_template_by_goal(goal)
    if chosen_key and chosen_key in TEMPLATES:
        t_data = TEMPLATES[chosen_key]
        steps: List[PlanStep] = []
        for i, s in enumerate(t_data["steps"], 1):
            tool = s["tool_name"]
            # Validate tool exists
            if tool in TOOL_HANDLERS:
                steps.append(PlanStep(
                    step_number=i,
                    title=s["title"],
                    description=s["description"],
                    tool_name=tool,
                    tool_args=s.get("tool_args", {})
                ))
        if steps:
            return TaskPlan(goal=goal, steps=steps)

    # 2. Dynamic Plan Generation via OpenRouter / OpenAI
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
        
        if api_key:
            client = OpenAI(api_key=api_key, base_url=base_url)
            model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
            
            allowed_tool_names = list(TOOL_HANDLERS.keys())
            system_prompt = (
                "You are the JARVIS Autonomous Mission Planner. "
                "Break down the user's objective into a structured sequence of 2 to 5 actionable steps. "
                "CRITICAL: You may ONLY use the following allowlisted tool names:\n"
                f"{json.dumps(allowed_tool_names)}\n\n"
                "Return ONLY a valid JSON object matching this schema:\n"
                "{\n"
                '  "steps": [\n'
                '    {\n'
                '      "title": "Short title",\n'
                '      "description": "What this step does",\n'
                '      "tool_name": "one_of_allowed_tool_names",\n'
                '      "tool_args": {"arg_key": "arg_value"}\n'
                '    }\n'
                '  ]\n'
                "}"
            )
            
            user_msg = f"User Goal: {goal}"
            if context:
                user_msg += f"\nAdditional Context: {context}"

            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            raw_content = resp.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            
            steps: List[PlanStep] = []
            for i, raw_step in enumerate(parsed.get("steps", []), 1):
                t_name = raw_step.get("tool_name", "")
                if t_name in TOOL_HANDLERS:
                    steps.append(PlanStep(
                        step_number=i,
                        title=raw_step.get("title", f"Step {i}"),
                        description=raw_step.get("description", ""),
                        tool_name=t_name,
                        tool_args=raw_step.get("tool_args", {})
                    ))
            
            if steps:
                return TaskPlan(goal=goal, steps=steps)
    except Exception as e:
        print(f"[JARVIS Planner] Dynamic planning fallback triggered: {e}")

    # 3. Fallback General Plan if offline or LLM fails
    fallback_steps = [
        PlanStep(
            step_number=1,
            title="Inspect System Telemetry",
            description="Query live CPU, RAM, and hardware health.",
            tool_name="get_system_status",
            tool_args={}
        ),
        PlanStep(
            step_number=2,
            title="Audit Workspace Git State",
            description="Examine modified files and pending working tree changes.",
            tool_name="run_git_status",
            tool_args={}
        )
    ]
    return TaskPlan(goal=goal, steps=fallback_steps)
