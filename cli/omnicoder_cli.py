from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - handled via runtime message
    yaml = None

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_CONFIG_PATH = REPO_ROOT / "_data" / "agi_engines.yml"
SESSION_LOG_PATH = REPO_ROOT / "database" / "sessions" / "cli_history.jsonl"
UPGRADE_LOG_PATH = REPO_ROOT / "database" / "training" / "upgrade_requests_cli.jsonl"
UPGRADE_RUNS_DIR = REPO_ROOT / "database" / "training" / "upgrade_runs"

FALLBACK_ENGINES: Dict[str, Dict[str, Any]] = {
    "PlanVoice-G4-G3-203": {
        "quality": 0.9936,
        "domain": "planning",
        "specialty": "Code Architecture",
        "traits": ["Master-Strategist", "Code Architecture Design", "Project Planning"],
    },
    "EvolveChart-G4-G3-171": {
        "quality": 0.9928,
        "domain": "creativity",
        "specialty": "Software Architect",
        "traits": ["Innovative Design", "Pattern Recognition", "Evolution-Based Learning"],
    },
    "ImprovePlan-G4-G3-172": {
        "quality": 0.9935,
        "domain": "self_improvement",
        "specialty": "Code Generator",
        "traits": ["Self-Transcending", "Continuous Learning", "Auto-Optimization"],
    },
    "LinguaChart-G4-G3-192": {
        "quality": 0.9928,
        "domain": "language",
        "specialty": "Documentation",
        "traits": ["Eloquent", "Clear Communication", "Multi-Language"],
    },
    "VirtueArchive-G4-G3-152": {
        "quality": 0.993,
        "domain": "ethics",
        "specialty": "Security Analysis",
        "traits": ["Morally-Aligned", "Security-Focused", "Best Practices"],
    },
    "UniteSee-G4-G3-135": {
        "quality": 0.9928,
        "domain": "integration",
        "specialty": "System Integration",
        "traits": ["Fully-Integrated", "Cross-Platform", "API Mastery"],
    },
    "PerceiveRise-G4-G3-185": {
        "quality": 0.9924,
        "domain": "perception",
        "specialty": "Bug Detection",
        "traits": ["Super-Perceptive", "Error Detection", "Anomaly Recognition"],
    },
    "RetainGood-G4-G3-159": {
        "quality": 0.9927,
        "domain": "memory",
        "specialty": "Code Memory",
        "traits": ["Perfect-Recall", "Context Retention", "Pattern Memory"],
    },
    "WiseJust-G4-G3-119": {
        "quality": 0.9923,
        "domain": "knowledge",
        "specialty": "Knowledge Synthesis",
        "traits": ["Omni-Knowledgeable", "Cross-Domain", "Research Integration"],
    },
    "MuseEthics-G4-G3-142": {
        "quality": 0.9923,
        "domain": "creativity",
        "specialty": "Creative Solutions",
        "traits": ["Visionary", "Innovative Thinking", "Creative Problem Solving"],
    },
}

BOARD_PRESETS: Dict[str, Dict[str, Any]] = {
    "auto": {
        "name": "Auto-Select",
        "description": "Automatically picks engines based on the prompt",
        "engines": [],
    },
    "code-architect": {
        "name": "Code Architecture",
        "description": "High-level design and planning",
        "engines": ["PlanVoice-G4-G3-203", "EvolveChart-G4-G3-171"],
    },
    "code-generator": {
        "name": "Code Generator",
        "description": "Feature implementation and scaffolding",
        "engines": ["ImprovePlan-G4-G3-172", "PlanVoice-G4-G3-203"],
    },
    "code-reviewer": {
        "name": "Code Review",
        "description": "Safety, quality and performance review",
        "engines": ["PerceiveRise-G4-G3-185", "VirtueArchive-G4-G3-152"],
    },
    "bug-detector": {
        "name": "Bug Detection",
        "description": "Regression hunting and diagnostics",
        "engines": ["PerceiveRise-G4-G3-185", "VirtueArchive-G4-G3-152", "RetainGood-G4-G3-159"],
    },
    "unit-testing": {
        "name": "Unit Testing",
        "description": "Test generation and verification",
        "engines": ["PerceiveRise-G4-G3-185", "ImprovePlan-G4-G3-172"],
    },
    "doc-generator": {
        "name": "Documentation",
        "description": "Guides, READMEs and references",
        "engines": ["LinguaChart-G4-G3-192", "WiseJust-G4-G3-119"],
    },
    "security": {
        "name": "Security Analysis",
        "description": "Threat modelling and hardening",
        "engines": ["VirtueArchive-G4-G3-152", "PerceiveRise-G4-G3-185"],
    },
    "optimization": {
        "name": "Optimization",
        "description": "Performance tuning and profiling",
        "engines": ["ImprovePlan-G4-G3-172", "EvolveChart-G4-G3-171"],
    },
    "refactoring": {
        "name": "Refactoring",
        "description": "Code cleanup and structural improvements",
        "engines": ["EvolveChart-G4-G3-171", "PlanVoice-G4-G3-203", "MuseEthics-G4-G3-142"],
    },
}


UTC = dt.timezone.utc


def iso_now() -> str:
    return dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp_slug() -> str:
    return dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


class HistoryLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"timestamp": iso_now(), **entry}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        return payload

    def tail(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries


class AGIEngineCLI:
    def __init__(self, config_path: Path = ENGINE_CONFIG_PATH) -> None:
        self.config_path = config_path
        self.engines = self._load_engines()
        self.boards = BOARD_PRESETS
        self.training_queue: List[Dict[str, Any]] = []
        self.current_quality = 0.9927
        self.quality_target = 1.0

    def _load_engines(self) -> Dict[str, Dict[str, Any]]:
        engines = {name: spec.copy() for name, spec in FALLBACK_ENGINES.items()}
        if yaml is None:
            return engines
        if not self.config_path.exists():
            return engines
        try:
            data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            print(f"[warn] Failed to read {self.config_path}: {exc}", file=sys.stderr)
            return engines
        for item in data.get("primary_engines", []):
            name = item.get("name")
            if not name:
                continue
            engines[name] = {
                "quality": float(item.get("quality", 0.99)),
                "domain": item.get("domain", "general"),
                "specialty": item.get("specialty", "Generalist"),
                "traits": item.get("traits", []),
            }
        return engines

    def process_request(
        self,
        message: str,
        *,
        board: str = "auto",
        multi_agent: bool = False,
        agent_count: int = 1,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        board_key = board or "auto"
        selected_engines = self.select_engines(message, board_key)
        analysis = self.analyze_request(message, context)
        analysis["board"] = board_key
        analysis["agent_count"] = agent_count
        response = self.generate_response(
            message,
            analysis,
            selected_engines,
            multi_agent or agent_count > 1,
        )
        self.track_for_learning(message, response, selected_engines)
        return {
            "analysis": analysis,
            "response": response["message"],
            "engines": selected_engines,
            "multi_agent": multi_agent or agent_count > 1,
            "agent_count": agent_count,
            "statistics": self.get_statistics(),
            "work_output": response.get("work_output"),
        }

    def select_engines(self, message: str, board: str) -> List[str]:
        if board and board != "auto":
            preset = self.boards.get(board)
            if not preset:
                raise ValueError(f"Unknown board: {board}")
            return preset["engines"]

        keywords = message.lower()
        selected: List[str] = []

        def add(*names: str) -> None:
            for name in names:
                if name in self.engines:
                    selected.append(name)

        if any(k in keywords for k in ("bug", "error", "fix")):
            add("PerceiveRise-G4-G3-185", "VirtueArchive-G4-G3-152")
        if any(k in keywords for k in ("create", "build", "generate", "implement")):
            add("ImprovePlan-G4-G3-172", "PlanVoice-G4-G3-203")
        if any(k in keywords for k in ("document", "comment", "explain")):
            add("LinguaChart-G4-G3-192", "WiseJust-G4-G3-119")
        if any(k in keywords for k in ("architecture", "design", "structure")):
            add("PlanVoice-G4-G3-203", "EvolveChart-G4-G3-171")
        if any(k in keywords for k in ("security", "safe", "vulnerability")):
            add("VirtueArchive-G4-G3-152", "PerceiveRise-G4-G3-185")
        if any(k in keywords for k in ("optimize", "improve", "performance")):
            add("ImprovePlan-G4-G3-172", "EvolveChart-G4-G3-171")
        if any(k in keywords for k in ("test", "verify", "qa")):
            add("PerceiveRise-G4-G3-185", "VirtueArchive-G4-G3-152")
        if any(k in keywords for k in ("refactor", "clean")):
            add("EvolveChart-G4-G3-171", "MuseEthics-G4-G3-142")
        if any(k in keywords for k in ("integrate", "api", "connect")):
            add("UniteSee-G4-G3-135", "ImprovePlan-G4-G3-172")

        if not selected:
            add("PlanVoice-G4-G3-203", "ImprovePlan-G4-G3-172", "LinguaChart-G4-G3-192")

        return list(dict.fromkeys(selected))

    def analyze_request(self, message: str, context: Optional[str]) -> Dict[str, Any]:
        return {
            "intent": self.detect_intent(message),
            "complexity": self.assess_complexity(message),
            "domain": self.detect_domain(message),
            "requires_code": self.requires_code_generation(message),
            "requires_test": self.requires_testing(message),
            "context": context,
        }

    @staticmethod
    def detect_intent(message: str) -> str:
        msg = message.lower()
        if any(k in msg for k in ("create", "build", "make", "generate", "implement")):
            return "create"
        if any(k in msg for k in ("fix", "bug", "error", "patch")):
            return "fix"
        if any(k in msg for k in ("explain", "what", "how", "why")):
            return "explain"
        if "review" in msg or "check" in msg:
            return "review"
        if any(k in msg for k in ("optimize", "improve", "speed", "performance")):
            return "optimize"
        if "test" in msg or "verify" in msg:
            return "test"
        if "document" in msg or "doc" in msg:
            return "document"
        if "refactor" in msg:
            return "refactor"
        return "general"

    @staticmethod
    def assess_complexity(message: str) -> str:
        words = message.split()
        has_code = "```" in message
        multiple_tasks = " and " in message.lower() or "," in message
        if len(words) > 100 or multiple_tasks:
            return "high"
        if len(words) > 30 or has_code:
            return "medium"
        return "low"

    @staticmethod
    def detect_domain(message: str) -> str:
        msg = message.lower()
        if any(k in msg for k in ("frontend", "ui", "react", "css", "html")):
            return "frontend"
        if any(k in msg for k in ("backend", "api", "server", "database", "sql")):
            return "backend"
        if any(k in msg for k in ("devops", "deploy", "docker", "ci/cd", "kubernetes")):
            return "devops"
        if any(k in msg for k in ("security", "auth", "vulnerability", "compliance")):
            return "security"
        if "test" in msg:
            return "testing"
        return "general"

    @staticmethod
    def requires_code_generation(message: str) -> bool:
        keywords = ["create", "build", "generate", "write", "implement", "add", "make"]
        return any(k in message.lower() for k in keywords)

    @staticmethod
    def requires_testing(message: str) -> bool:
        keywords = ["test", "verify", "check", "validate", "ensure"]
        return any(k in message.lower() for k in keywords)

    def generate_response(
        self,
        message: str,
        analysis: Dict[str, Any],
        engines: List[str],
        multi_agent: bool,
    ) -> Dict[str, Any]:
        intent = analysis["intent"]
        handler_map = {
            "create": self.handle_create_intent,
            "fix": self.handle_fix_intent,
            "explain": self.handle_explain_intent,
            "review": self.handle_review_intent,
            "optimize": self.handle_optimize_intent,
            "test": self.handle_test_intent,
            "document": self.handle_document_intent,
            "refactor": self.handle_refactor_intent,
        }
        handler = handler_map.get(intent, self.handle_general_intent)
        base_response = handler(message, analysis, engines)
        work_output = self.simulate_work_output(message, analysis, engines)
        base_response["work_output"] = work_output
        if multi_agent:
            base_response["message"] += (
                f"\n\n---\n**Multi-Agent Analysis**: {len(engines)} engines collaborated "
                "to produce consensus output."
            )
        return base_response

    def simulate_work_output(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        seed = int(hashlib.sha1(message.encode("utf-8")).hexdigest(), 16)
        randomizer = random.Random(seed)
        lines_changed = randomizer.randint(18, 120)
        files_touched = randomizer.randint(1, min(6, max(2, len(engines))))
        tests_planned = randomizer.randint(0, 5) if analysis["requires_test"] else randomizer.randint(0, 2)
        avg_quality = sum(self.engines[e]["quality"] for e in engines) / len(engines)
        return {
            "lines_changed": lines_changed,
            "files_touched": files_touched,
            "tests_planned": tests_planned,
            "confidence": round(avg_quality * 100, 2),
            "next_steps": [
                "Review generated changes",
                "Run project test suite",
                "Commit and push if satisfied",
            ],
        }

    def handle_create_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "🏗️ **Creating based on your request**\n\n"
                f"Using **{', '.join(engines)}** for optimal generation.\n\n"
                f"**Analysis:**\n- Complexity: {analysis['complexity']}\n"
                f"- Domain: {analysis['domain']}\n\n"
                "*Code scaffolding prepared; ready for integration.*"
            )
        }

    def handle_fix_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "🔧 **Bug Fix Analysis**\n\n"
                f"Using **{', '.join(engines)}** to detect and patch issues.\n\n"
                "1. Analyze failure signals\n2. Identify root cause\n3. Generate fix\n4. Verify regression safety\n\n"
                "*Diagnostics queued; applying simulated patch.*"
            )
        }

    def handle_explain_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "📚 **Explanation Request**\n\n"
                f"Engines: **{', '.join(engines)}**.\n\n"
                "Delivering structured explanation with examples and follow-up pointers."
            )
        }

    def handle_review_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "🔍 **Code Review**\n\n"
                f"Using **{', '.join(engines)}** for comprehensive review.\n\n"
                "Checklist: quality, best practices, security, performance, docs.\n"
                "Any blocking findings will be highlighted."
            )
        }

    def handle_optimize_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "⚡ **Optimization Analysis**\n\n"
                f"Engines engaged: **{', '.join(engines)}**.\n\n"
                "Focus areas: algorithmic efficiency, memory footprint, bundle size."
            )
        }

    def handle_test_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "🧪 **Test Generation**\n\n"
                f"Using **{', '.join(engines)}** for verification suite design."
            )
        }

    def handle_document_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "📝 **Documentation Pipeline**\n\n"
                f"Leveraging **{', '.join(engines)}** for API docs, guides, and samples."
            )
        }

    def handle_refactor_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "♻️ **Refactoring Plan**\n\n"
                f"Engines collaborating: **{', '.join(engines)}**.\n"
                "Assessing structure, SOLID alignment, and duplication."
            )
        }

    def handle_general_intent(
        self, message: str, analysis: Dict[str, Any], engines: List[str]
    ) -> Dict[str, Any]:
        return {
            "message": (
                "🤖 **General Assistance**\n\n"
                f"Engines active: **{', '.join(engines)}**.\n"
                "Preparing an adaptive response for your request."
            )
        }

    def track_for_learning(
        self, message: str, response: Dict[str, Any], engines: List[str]
    ) -> None:
        self.training_queue.append(
            {
                "timestamp": iso_now(),
                "message": message,
                "engines": engines,
                "response": response["message"],
                "quality": round(self.current_quality, 4),
            }
        )
        if self.current_quality < self.quality_target:
            self.current_quality = min(self.quality_target, self.current_quality + 0.0001)

    def get_statistics(self) -> Dict[str, Any]:
        total_engines = len(self.engines)
        avg_quality = (
            sum(engine["quality"] for engine in self.engines.values()) / total_engines
        )
        return {
            "total_engines": total_engines,
            "average_quality": round(avg_quality, 4),
            "training_queue_size": len(self.training_queue),
            "current_quality": round(self.current_quality, 4),
            "target_quality": self.quality_target,
        }


class UpgradeManager:
    def __init__(
        self,
        engine: AGIEngineCLI,
        queue_logger: HistoryLogger,
        runs_dir: Path = UPGRADE_RUNS_DIR,
    ) -> None:
        self.engine = engine
        self.queue_logger = queue_logger
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def handle_request(
        self,
        description: str,
        *,
        mode: str = "self",
        auto_execute: bool = False,
    ) -> Dict[str, Any]:
        plan = self.build_plan(description, mode)
        log_entry = self.queue_logger.append(
            {
                "type": "upgrade",
                "mode": mode,
                "focus": plan["focus"],
                "summary": plan["summary"],
                "status": "queued",
            }
        )
        result = {
            "plan": plan,
            "status": "queued",
            "log_entry": log_entry,
        }
        if auto_execute:
            execution = self.execute_plan(plan)
            result["status"] = "executed"
            result["execution"] = execution
        return result

    def build_plan(self, description: str, mode: str) -> Dict[str, Any]:
        focus = self.engine.detect_domain(description)
        severity = self._score_severity(description)
        board_hint = self._board_for_focus(focus)

        steps = [
            {
                "name": "Analyze Current Implementation",
                "board": board_hint or "code-architect",
                "agents": 2,
                "prompt": "Audit existing OmniCoder subsystems touched by the request.",
                "deliverable": "Gap analysis & current limitations",
            },
            {
                "name": "Design Upgrade Blueprint",
                "board": "code-architect",
                "agents": 2,
                "prompt": "Draft architecture and component interactions for the upgrade.",
                "deliverable": "Architecture notes + acceptance criteria",
            },
            {
                "name": "Implement & Wire Changes",
                "board": "code-generator",
                "agents": 3,
                "prompt": "Generate code updates, configs, and automation hooks.",
                "deliverable": "Patch set ready for review",
            },
            {
                "name": "Test & Verify",
                "board": "unit-testing",
                "agents": 2,
                "prompt": "Plan regression tests, run linters, and summarize coverage.",
                "deliverable": "Verification report",
            },
            {
                "name": "Deploy & Document",
                "board": "doc-generator",
                "agents": 1,
                "prompt": "Update docs, changelog, and deployment notes.",
                "deliverable": "Docs + rollout checklist",
            },
        ]

        summary = textwrap.shorten(description, width=160, placeholder="…")
        return {
            "summary": summary,
            "mode": mode,
            "focus": focus,
            "severity": severity,
            "steps": steps,
            "requested_at": iso_now(),
        }

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        transcripts: List[Dict[str, Any]] = []
        for step in plan["steps"]:
            prompt = f"{plan['summary']} :: {step['prompt']}"
            response = self.engine.process_request(
                prompt,
                board=step["board"],
                multi_agent=True,
                agent_count=step["agents"],
                context=None,
            )
            transcripts.append(
                {
                    "step": step["name"],
                    "board": step["board"],
                    "agents": step["agents"],
                    "analysis": response["analysis"],
                    "summary": response["response"],
                    "engines": response["engines"],
                }
            )

        run_payload = {
            "plan": plan,
            "transcripts": transcripts,
            "completed_at": iso_now(),
        }
        filename = f"upgrade_{timestamp_slug()}.json"
        run_path = self.runs_dir / filename
        run_path.write_text(json.dumps(run_payload, indent=2), encoding="utf-8")
        return {"run_path": str(run_path), "steps_executed": len(transcripts)}

    @staticmethod
    def _score_severity(description: str) -> str:
        desc = description.lower()
        if any(k in desc for k in ("crash", "outage", "critical", "security", "broken")):
            return "high"
        if any(k in desc for k in ("slow", "optimize", "enhance", "improve")):
            return "medium"
        return "low"

    @staticmethod
    def _board_for_focus(focus: str) -> str:
        mapping = {
            "frontend": "doc-generator",
            "backend": "code-generator",
            "devops": "optimization",
            "security": "security",
            "testing": "unit-testing",
        }
        return mapping.get(focus, "auto")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OmniCoder-AGI CLI — run agents, plan upgrades, and inspect stats.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Execute an agent request in CLI form",
    )
    run_parser.add_argument("message", help="Task description or prompt")
    run_parser.add_argument(
        "--board",
        default="auto",
        choices=sorted(BOARD_PRESETS.keys()),
        help="Force a specific AGI board (default: auto)",
    )
    run_parser.add_argument(
        "--agents",
        type=int,
        default=1,
        help="Number of cooperating agents (multi-agent when >1)",
    )
    run_parser.add_argument(
        "--multi",
        action="store_true",
        help="Force multi-agent analysis even if agents=1",
    )
    run_parser.add_argument(
        "--context",
        help="Inline context or notes to pass with the request",
    )
    run_parser.add_argument(
        "--context-file",
        type=Path,
        help="Path to a file whose contents should be used as context",
    )
    run_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    run_parser.add_argument(
        "--notes",
        help="Optional note saved in the session log entry",
    )

    upgrade_parser = subparsers.add_parser(
        "upgrade", help="Queue or execute a self-upgrade workflow",
    )
    upgrade_parser.add_argument("description", help="Describe the upgrade or improvement you need")
    upgrade_parser.add_argument(
        "--mode",
        default="self",
        choices=["self", "feature", "bugfix"],
        help="Upgrade type (self = platform improvements)",
    )
    upgrade_parser.add_argument(
        "--auto-execute",
        action="store_true",
        help="Immediately run the upgrade playbook with multi-agent calls",
    )
    upgrade_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    stats_parser = subparsers.add_parser("stats", help="Show engine quality statistics")
    stats_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    boards_parser = subparsers.add_parser("boards", help="List available agent boards")
    boards_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    history_parser = subparsers.add_parser("history", help="Show recent CLI activity")
    history_parser.add_argument(
        "--target",
        choices=["sessions", "upgrades"],
        default="sessions",
        help="Which log to inspect",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of entries to display",
    )
    history_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    return parser


def read_context_from_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Failed to read context file {path}: {exc}") from exc


def render_text_run(result: Dict[str, Any]) -> None:
    analysis = result["analysis"]
    print("=== OmniCoder-AGI CLI ===")
    print(f"Intent: {analysis['intent']} | Complexity: {analysis['complexity']} | Domain: {analysis['domain']}")
    print(f"Engines: {', '.join(result['engines'])}")
    print()
    print(result["response"])
    work_output = result.get("work_output") or {}
    if work_output:
        print("\n--- Work Output (simulated) ---")
        print(f"Lines changed : {work_output['lines_changed']}")
        print(f"Files touched : {work_output['files_touched']}")
        print(f"Tests planned : {work_output['tests_planned']}")
        print(f"Confidence    : {work_output['confidence']}%")
        print("Next steps    :")
        for step in work_output["next_steps"]:
            print(f"  - {step}")


def render_text_upgrade(result: Dict[str, Any]) -> None:
    plan = result["plan"]
    print("=== Upgrade Plan ===")
    print(f"Summary : {plan['summary']}")
    print(f"Focus   : {plan['focus']} | Severity: {plan['severity']} | Mode: {plan['mode']}")
    print()
    for idx, step in enumerate(plan["steps"], start=1):
        print(f"{idx}. {step['name']} [{step['board']}] — {step['deliverable']} (agents: {step['agents']})")
    print(f"\nStatus: {result['status']}")
    execution = result.get("execution")
    if execution:
        print(f"Execution saved to: {execution['run_path']}")


def render_text_stats(stats: Dict[str, Any]) -> None:
    print("=== Engine Statistics ===")
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title():<24} {value}")


def render_text_boards() -> None:
    print("=== Available Boards ===")
    for key, board in BOARD_PRESETS.items():
        engines = ", ".join(board["engines"]) or "auto-select"
        print(f"{key:>14}: {board['name']} — {board['description']} [{engines}]")


def render_text_history(entries: List[Dict[str, Any]], target: str) -> None:
    if not entries:
        print("No history entries recorded yet.")
        return
    print(f"=== Last {len(entries)} {target} entries ===")
    for entry in entries:
        ts = entry.get("timestamp")
        summary = entry.get("summary") or entry.get("message")
        print(f"- {ts} :: {entry.get('type', 'session')} :: {summary}")


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    engine = AGIEngineCLI()
    session_logger = HistoryLogger(SESSION_LOG_PATH)
    upgrade_logger = HistoryLogger(UPGRADE_LOG_PATH)
    upgrade_manager = UpgradeManager(engine, queue_logger=upgrade_logger)

    if args.command == "run":
        context_data = args.context or ""
        if args.context_file:
            context_data += "\n" + read_context_from_file(args.context_file)
        result = engine.process_request(
            args.message,
            board=args.board,
            multi_agent=args.multi,
            agent_count=max(1, args.agents),
            context=context_data.strip() or None,
        )
        session_logger.append(
            {
                "type": "session",
                "message": args.message,
                "board": args.board,
                "multi_agent": args.multi or args.agents > 1,
                "agents": max(1, args.agents),
                "engines": result["engines"],
                "notes": args.notes,
            }
        )
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            render_text_run(result)
        return

    if args.command == "upgrade":
        result = upgrade_manager.handle_request(
            args.description,
            mode=args.mode,
            auto_execute=args.auto_execute,
        )
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            render_text_upgrade(result)
        return

    if args.command == "stats":
        stats = engine.get_statistics()
        if args.format == "json":
            print(json.dumps(stats, indent=2))
        else:
            render_text_stats(stats)
        return

    if args.command == "boards":
        if args.format == "json":
            print(json.dumps(BOARD_PRESETS, indent=2))
        else:
            render_text_boards()
        return

    if args.command == "history":
        logger = session_logger if args.target == "sessions" else upgrade_logger
        entries = logger.tail(args.limit)
        if args.format == "json":
            print(json.dumps(entries, indent=2))
        else:
            render_text_history(entries, args.target)
        return

    parser.error("Unknown command")


if __name__ == "__main__":  # pragma: no cover
    main()

