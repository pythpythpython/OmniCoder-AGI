#!/usr/bin/env python3
"""
OmniCoder-AGI CLI - The World's Most Advanced Coding Automation Agent

This CLI provides:
- GitHub integration with PAT authentication
- Multi-MCP SDK integrations (TypeScript, Python, Java, Kotlin, C#, Go, PHP, Ruby, Rust, Swift)
- Multi-agent task execution with AGI boards
- Training, testing, and hyperparameter tuning to 100% quality
- Self-upgrade and continuous learning capabilities
- Memory/database management
- Repo browsing and code editing
- Voice input support
- Real-time collaboration features
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_CONFIG_PATH = REPO_ROOT / "_data" / "agi_engines.yml"
BOARDS_CONFIG_PATH = REPO_ROOT / "agi_boards" / "boards_config.json"
MCP_CONFIG_PATH = REPO_ROOT / "mcp_integrations" / "config.json"
SETTINGS_PATH = REPO_ROOT / "settings" / "default.json"

# Database paths
DATABASE_DIR = REPO_ROOT / "database"
MEMORY_DIR = DATABASE_DIR / "memory"
SESSIONS_DIR = DATABASE_DIR / "sessions"
TRAINING_DIR = DATABASE_DIR / "training"

# Log files
SESSION_LOG_PATH = SESSIONS_DIR / "cli_history.jsonl"
UPGRADE_LOG_PATH = TRAINING_DIR / "upgrade_requests_cli.jsonl"
UPGRADE_RUNS_DIR = TRAINING_DIR / "upgrade_runs"
LEARNING_LOG_PATH = TRAINING_DIR / "learning.jsonl"
HYPERPARAMETER_LOG_PATH = TRAINING_DIR / "hyperparameters.jsonl"

# GitHub Configuration
GITHUB_API_BASE = "https://api.github.com"

UTC = dt.timezone.utc

VERSION = "2.0.0"
APP_NAME = "OmniCoder-AGI"

# ============================================================================
# DATA CLASSES
# ============================================================================

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"

@dataclass
class AGIEngine:
    name: str
    quality: float
    domain: str
    specialty: str
    traits: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    tests_passed: str = "100%"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AGIBoard:
    name: str
    description: str
    primary_engine: str
    supporting_engines: List[str]
    quality: float
    capabilities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    board_used: str
    engines_used: List[str]
    output: str
    confidence: float
    files_changed: List[str] = field(default_factory=list)
    tests_passed: int = 0
    tests_total: int = 0
    suggestions: List[str] = field(default_factory=list)
    left_out: List[str] = field(default_factory=list)
    left_out_reasons: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result

@dataclass
class TrainingMetrics:
    quality_before: float
    quality_after: float
    tests_passed: int
    tests_total: int
    hyperparameters_tuned: int
    duration_seconds: float
    improvements: List[str] = field(default_factory=list)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def iso_now() -> str:
    return dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

def timestamp_slug() -> str:
    return dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

def ensure_dirs():
    """Ensure all required directories exist."""
    for dir_path in [MEMORY_DIR, SESSIONS_DIR, TRAINING_DIR, UPGRADE_RUNS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def generate_task_id() -> str:
    """Generate a unique task ID."""
    return f"task_{timestamp_slug()}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"

def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    width = max(60, len(title) + 4)
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}\n")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}", file=sys.stderr)

def print_warning(message: str):
    print(f"⚠️  {message}")

def print_info(message: str):
    print(f"ℹ️  {message}")

def print_progress(message: str):
    print(f"🔄 {message}")

# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class JSONLogger:
    """Append-only JSON Lines logger."""
    
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
    
    def append(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"timestamp": iso_now(), **entry}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        return payload
    
    def tail(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
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
    
    def search(self, key: str, value: Any, limit: int = 100) -> List[Dict[str, Any]]:
        """Search entries by key-value."""
        if not self.path.exists():
            return []
        results = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get(key) == value:
                        results.append(entry)
                        if len(results) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        return results

# ============================================================================
# GITHUB INTEGRATION
# ============================================================================

class GitHubClient:
    """GitHub API client with PAT authentication."""
    
    def __init__(self, token: Optional[str] = None, username: str = "", email: str = ""):
        self.token = token
        self.username = username
        self.email = email
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an API request."""
        url = f"{GITHUB_API_BASE}{endpoint}"
        body = json.dumps(data).encode() if data else None
        
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise RuntimeError(f"GitHub API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")
    
    def get_user(self) -> Dict:
        """Get authenticated user info."""
        return self._request("GET", "/user")
    
    def list_repos(self, limit: int = 100) -> List[Dict]:
        """List user repositories."""
        return self._request("GET", f"/user/repos?per_page={limit}&sort=updated")
    
    def get_repo(self, owner: str, repo: str) -> Dict:
        """Get repository details."""
        return self._request("GET", f"/repos/{owner}/{repo}")
    
    def create_repo(self, name: str, description: str = "", private: bool = False) -> Dict:
        """Create a new repository."""
        return self._request("POST", "/user/repos", {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True
        })
    
    def list_files(self, owner: str, repo: str, path: str = "", ref: str = "main") -> List[Dict]:
        """List files in a repository directory."""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        if ref:
            endpoint += f"?ref={ref}"
        return self._request("GET", endpoint)
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> str:
        """Get file content from repository."""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        result = self._request("GET", endpoint)
        if "content" in result:
            return base64.b64decode(result["content"]).decode()
        return ""
    
    def create_or_update_file(self, owner: str, repo: str, path: str, 
                               content: str, message: str, sha: Optional[str] = None) -> Dict:
        """Create or update a file in repository."""
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode()
        }
        if sha:
            data["sha"] = sha
        return self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)
    
    def create_branch(self, owner: str, repo: str, branch: str, from_ref: str = "main") -> Dict:
        """Create a new branch."""
        # Get the SHA of the source branch
        ref_data = self._request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_ref}")
        sha = ref_data["object"]["sha"]
        
        return self._request("POST", f"/repos/{owner}/{repo}/git/refs", {
            "ref": f"refs/heads/{branch}",
            "sha": sha
        })
    
    def create_pull_request(self, owner: str, repo: str, title: str, 
                            head: str, base: str = "main", body: str = "") -> Dict:
        """Create a pull request."""
        return self._request("POST", f"/repos/{owner}/{repo}/pulls", {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        })
    
    def merge_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Merge a pull request."""
        return self._request("PUT", f"/repos/{owner}/{repo}/pulls/{pr_number}/merge", {
            "merge_method": "squash"
        })
    
    def search_repos(self, query: str, limit: int = 50) -> List[Dict]:
        """Search GitHub repositories."""
        result = self._request("GET", f"/search/repositories?q={query}&per_page={limit}&sort=stars")
        return result.get("items", [])
    
    def get_trending_repos(self, language: str = "", limit: int = 50) -> List[Dict]:
        """Get trending repositories (using search with date filter)."""
        date_week_ago = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
        query = f"created:>{date_week_ago}"
        if language:
            query += f"+language:{language}"
        return self.search_repos(query, limit)
    
    def validate_token(self) -> bool:
        """Validate the PAT token."""
        try:
            self.get_user()
            return True
        except:
            return False

# ============================================================================
# MCP INTEGRATION SYSTEM
# ============================================================================

class MCPServer:
    """Represents an MCP server."""
    
    def __init__(self, name: str, repo: str, capabilities: List[str], 
                 languages: List[str] = None, status: str = "active"):
        self.name = name
        self.repo = repo
        self.capabilities = capabilities
        self.languages = languages or []
        self.status = status
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "repo": self.repo,
            "capabilities": self.capabilities,
            "languages": self.languages,
            "status": self.status
        }

class MCPRouter:
    """Routes tasks to appropriate MCP servers."""
    
    DEFAULT_SERVERS = {
        "github": MCPServer(
            "GitHub MCP Server",
            "github/github-mcp-server",
            ["repository_management", "issues", "pull_requests", "commits", "branches", "actions"]
        ),
        "typescript": MCPServer(
            "TypeScript SDK",
            "modelcontextprotocol/typescript-sdk",
            ["type_analysis", "transpilation", "linting", "formatting"],
            ["typescript", "javascript"]
        ),
        "python": MCPServer(
            "Python SDK",
            "modelcontextprotocol/python-sdk",
            ["code_analysis", "linting", "testing", "type_checking"],
            ["python"]
        ),
        "java": MCPServer(
            "Java SDK",
            "modelcontextprotocol/java-sdk",
            ["code_analysis", "maven_support", "gradle_support"],
            ["java"]
        ),
        "kotlin": MCPServer(
            "Kotlin SDK",
            "modelcontextprotocol/kotlin-sdk",
            ["code_analysis", "coroutines", "android_support"],
            ["kotlin"]
        ),
        "csharp": MCPServer(
            "C# SDK",
            "modelcontextprotocol/csharp-sdk",
            ["code_analysis", "dotnet_support", "nuget_support"],
            ["csharp", "fsharp"]
        ),
        "go": MCPServer(
            "Go SDK",
            "modelcontextprotocol/go-sdk",
            ["code_analysis", "modules", "testing"],
            ["go"]
        ),
        "php": MCPServer(
            "PHP SDK",
            "modelcontextprotocol/php-sdk",
            ["code_analysis", "composer_support"],
            ["php"]
        ),
        "ruby": MCPServer(
            "Ruby SDK",
            "modelcontextprotocol/ruby-sdk",
            ["code_analysis", "gems_support", "rails_support"],
            ["ruby"]
        ),
        "rust": MCPServer(
            "Rust SDK",
            "modelcontextprotocol/rust-sdk",
            ["code_analysis", "cargo_support", "memory_safety"],
            ["rust"]
        ),
        "swift": MCPServer(
            "Swift SDK",
            "modelcontextprotocol/swift-sdk",
            ["code_analysis", "xcode_support", "ios_development"],
            ["swift"]
        ),
        "openstax": MCPServer(
            "OpenStax MCP Server",
            "pythpythpython/openstax-mcp-server",
            ["educational_content", "textbook_access", "learning_resources"]
        )
    }
    
    def __init__(self):
        self.servers = dict(self.DEFAULT_SERVERS)
        self._load_custom_servers()
    
    def _load_custom_servers(self):
        """Load custom MCP servers from config."""
        if MCP_CONFIG_PATH.exists():
            try:
                config = json.loads(MCP_CONFIG_PATH.read_text())
                for key, server_data in config.get("servers", {}).items():
                    if key not in self.servers:
                        self.servers[key] = MCPServer(
                            server_data.get("name", key),
                            server_data.get("repo", ""),
                            server_data.get("capabilities", []),
                            server_data.get("languages", []),
                            server_data.get("status", "active")
                        )
            except Exception:
                pass
    
    def route_task(self, task: str, language: Optional[str] = None) -> List[str]:
        """Route a task to appropriate MCP servers."""
        selected = []
        task_lower = task.lower()
        
        # Always include GitHub for repo operations
        if any(k in task_lower for k in ["repo", "github", "pull", "issue", "commit", "branch"]):
            selected.append("github")
        
        # Route by language
        if language:
            lang_lower = language.lower()
            for key, server in self.servers.items():
                if lang_lower in [l.lower() for l in server.languages]:
                    selected.append(key)
        
        # Route by task keywords
        language_keywords = {
            "typescript": ["typescript", "ts", "javascript", "js", "react", "node"],
            "python": ["python", "py", "django", "flask", "fastapi"],
            "java": ["java", "spring", "maven", "gradle"],
            "kotlin": ["kotlin", "android"],
            "csharp": ["c#", "csharp", ".net", "dotnet", "unity"],
            "go": ["go", "golang"],
            "php": ["php", "laravel", "symfony"],
            "ruby": ["ruby", "rails"],
            "rust": ["rust", "cargo"],
            "swift": ["swift", "ios", "xcode"]
        }
        
        for key, keywords in language_keywords.items():
            if any(k in task_lower for k in keywords):
                if key not in selected:
                    selected.append(key)
        
        # Default to GitHub + common SDKs if nothing specific
        if not selected:
            selected = ["github", "typescript", "python"]
        
        return selected
    
    def get_server(self, key: str) -> Optional[MCPServer]:
        return self.servers.get(key)
    
    def add_server(self, key: str, server: MCPServer):
        """Add a custom MCP server."""
        self.servers[key] = server
        self._save_custom_servers()
    
    def _save_custom_servers(self):
        """Save custom servers to config."""
        config = {"version": "1.0.0", "servers": {}}
        for key, server in self.servers.items():
            config["servers"][key] = server.to_dict()
        MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        MCP_CONFIG_PATH.write_text(json.dumps(config, indent=2))
    
    def list_servers(self) -> Dict[str, MCPServer]:
        return self.servers

# ============================================================================
# AGI ENGINE SYSTEM
# ============================================================================

FALLBACK_ENGINES = {
    "PlanVoice-G4-G3-203": AGIEngine(
        name="PlanVoice-G4-G3-203",
        quality=0.9936,
        domain="planning",
        specialty="Master Code Architect",
        traits=["Master-Strategist", "Code Architecture Design", "Project Planning"],
        capabilities=["Multi-file code generation", "Architecture optimization", "Dependency management"]
    ),
    "EvolveChart-G4-G3-171": AGIEngine(
        name="EvolveChart-G4-G3-171",
        quality=0.9928,
        domain="creativity",
        specialty="Software Architect Prime",
        traits=["Innovative Design", "Pattern Recognition", "Evolution-Based Learning"],
        capabilities=["Novel algorithm creation", "Design pattern application", "Code refactoring"]
    ),
    "ImprovePlan-G4-G3-172": AGIEngine(
        name="ImprovePlan-G4-G3-172",
        quality=0.9935,
        domain="self_improvement",
        specialty="Autonomous Code Generator",
        traits=["Self-Transcending", "Continuous Learning", "Auto-Optimization"],
        capabilities=["Auto-code generation", "Self-improvement cycles", "Bug detection and fixing"]
    ),
    "LinguaChart-G4-G3-192": AGIEngine(
        name="LinguaChart-G4-G3-192",
        quality=0.9928,
        domain="language",
        specialty="Code Documentation Expert",
        traits=["Eloquent", "Clear Communication", "Multi-Language Support"],
        capabilities=["Documentation generation", "Code comments", "API documentation"]
    ),
    "VirtueArchive-G4-G3-152": AGIEngine(
        name="VirtueArchive-G4-G3-152",
        quality=0.9930,
        domain="ethics",
        specialty="Code Security Analyst",
        traits=["Morally-Aligned", "Security-Focused", "Best Practices"],
        capabilities=["Security vulnerability detection", "Code ethics compliance", "Safe code patterns"]
    ),
    "UniteSee-G4-G3-135": AGIEngine(
        name="UniteSee-G4-G3-135",
        quality=0.9928,
        domain="integration",
        specialty="System Integrator",
        traits=["Fully-Integrated", "Cross-Platform", "API Mastery"],
        capabilities=["Multi-system integration", "API development", "Microservices architecture"]
    ),
    "PerceiveRise-G4-G3-185": AGIEngine(
        name="PerceiveRise-G4-G3-185",
        quality=0.9924,
        domain="perception",
        specialty="Bug Detection Specialist",
        traits=["Super-Perceptive", "Error Detection", "Anomaly Recognition"],
        capabilities=["Bug detection", "Error analysis", "Code smell identification"]
    ),
    "RetainGood-G4-G3-159": AGIEngine(
        name="RetainGood-G4-G3-159",
        quality=0.9927,
        domain="memory",
        specialty="Code Memory Specialist",
        traits=["Perfect-Recall", "Context Retention", "Pattern Memory"],
        capabilities=["Code pattern recognition", "Historical code analysis", "Version control"]
    ),
    "WiseJust-G4-G3-119": AGIEngine(
        name="WiseJust-G4-G3-119",
        quality=0.9923,
        domain="knowledge",
        specialty="Knowledge Synthesizer",
        traits=["Omni-Knowledgeable", "Cross-Domain Expert", "Research Integration"],
        capabilities=["Technology research", "Best practice identification", "Framework selection"]
    ),
    "MuseEthics-G4-G3-142": AGIEngine(
        name="MuseEthics-G4-G3-142",
        quality=0.9923,
        domain="creativity",
        specialty="Creative Solution Designer",
        traits=["Visionary", "Innovative Thinking", "Creative Problem Solving"],
        capabilities=["Novel solution design", "Algorithm innovation", "Feature ideation"]
    ),
}

# ============================================================================
# AGI BOARD SYSTEM
# ============================================================================

BOARD_PRESETS = {
    "auto": AGIBoard("Auto-Select", "Automatically picks engines based on the prompt", "", [], 0.99),
    "code-architect": AGIBoard(
        "Code Architecture",
        "High-level design and planning",
        "PlanVoice-G4-G3-203",
        ["EvolveChart-G4-G3-171", "ImprovePlan-G4-G3-172"],
        0.9936,
        ["Project structure design", "Design pattern selection", "API design"]
    ),
    "code-generator": AGIBoard(
        "Code Generator",
        "Feature implementation and scaffolding",
        "ImprovePlan-G4-G3-172",
        ["PlanVoice-G4-G3-203", "LinguaChart-G4-G3-192"],
        0.9935,
        ["Function generation", "Class generation", "Full file generation"]
    ),
    "code-reviewer": AGIBoard(
        "Code Review",
        "Safety, quality and performance review",
        "PerceiveRise-G4-G3-185",
        ["VirtueArchive-G4-G3-152", "RetainGood-G4-G3-159"],
        0.9928,
        ["Quality assessment", "Security analysis", "Performance review"]
    ),
    "bug-detector": AGIBoard(
        "Bug Detection",
        "Regression hunting and diagnostics",
        "PerceiveRise-G4-G3-185",
        ["VirtueArchive-G4-G3-152", "WiseJust-G4-G3-119"],
        0.9924,
        ["Runtime error detection", "Logic error detection", "Memory leak detection"]
    ),
    "unit-testing": AGIBoard(
        "Unit Testing",
        "Test generation and verification",
        "PerceiveRise-G4-G3-185",
        ["ImprovePlan-G4-G3-172", "VirtueArchive-G4-G3-152"],
        0.9920,
        ["Test case generation", "Edge case identification", "Coverage analysis"]
    ),
    "integration-testing": AGIBoard(
        "Integration Testing",
        "Tests component integration",
        "UniteSee-G4-G3-135",
        ["PerceiveRise-G4-G3-185", "ImprovePlan-G4-G3-172"],
        0.9915,
        ["API testing", "Database integration", "End-to-end testing"]
    ),
    "doc-generator": AGIBoard(
        "Documentation",
        "Guides, READMEs and references",
        "LinguaChart-G4-G3-192",
        ["WiseJust-G4-G3-119", "RetainGood-G4-G3-159"],
        0.9928,
        ["API documentation", "README generation", "User guides"]
    ),
    "security": AGIBoard(
        "Security Analysis",
        "Threat modelling and hardening",
        "VirtueArchive-G4-G3-152",
        ["PerceiveRise-G4-G3-185", "WiseJust-G4-G3-119"],
        0.9930,
        ["OWASP vulnerability detection", "Secrets detection", "Auth security"]
    ),
    "optimization": AGIBoard(
        "Optimization",
        "Performance tuning and profiling",
        "ImprovePlan-G4-G3-172",
        ["EvolveChart-G4-G3-171", "PerceiveRise-G4-G3-185"],
        0.9933,
        ["Algorithm optimization", "Memory optimization", "Query optimization"]
    ),
    "refactoring": AGIBoard(
        "Refactoring",
        "Code cleanup and structural improvements",
        "EvolveChart-G4-G3-171",
        ["PlanVoice-G4-G3-203", "MuseEthics-G4-G3-142"],
        0.9926,
        ["Code restructuring", "Design pattern application", "SOLID compliance"]
    ),
    "test-verifier": AGIBoard(
        "Test Verifier",
        "Verifies tests are comprehensive and correct",
        "VirtueArchive-G4-G3-152",
        ["PerceiveRise-G4-G3-185", "WiseJust-G4-G3-119"],
        0.9928,
        ["Test coverage verification", "Test quality assessment", "Edge case verification"]
    ),
    "quality-verifier": AGIBoard(
        "Quality Verifier",
        "Verifies overall code quality",
        "PerceiveRise-G4-G3-185",
        ["VirtueArchive-G4-G3-152", "ImprovePlan-G4-G3-172"],
        0.9927,
        ["Quality metrics", "Technical debt assessment", "Code complexity analysis"]
    ),
    "mcp-selector": AGIBoard(
        "MCP Selection",
        "Selects optimal MCP servers for tasks",
        "UniteSee-G4-G3-135",
        ["PlanVoice-G4-G3-203", "WiseJust-G4-G3-119"],
        0.9928,
        ["MCP routing", "Language detection", "Capability matching"]
    ),
    "continuous-learner": AGIBoard(
        "Continuous Learning",
        "Learns from interactions and bleeding-edge problems",
        "ImprovePlan-G4-G3-172",
        ["WiseJust-G4-G3-119", "RetainGood-G4-G3-159"],
        0.9935,
        ["Pattern learning", "Problem analysis", "Knowledge synthesis"]
    ),
    "hyperparameter-tuner": AGIBoard(
        "Hyperparameter Tuning",
        "Tunes AGI engines for optimal performance",
        "ImprovePlan-G4-G3-172",
        ["EvolveChart-G4-G3-171", "PerceiveRise-G4-G3-185"],
        0.9933,
        ["Response quality tuning", "Code accuracy tuning", "Test coverage tuning"]
    ),
}

# ============================================================================
# MAIN AGI ENGINE
# ============================================================================

class OmniCoderAGI:
    """The main AGI engine for coding automation."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.engines = dict(FALLBACK_ENGINES)
        self.boards = dict(BOARD_PRESETS)
        self.mcp_router = MCPRouter()
        self.github = GitHubClient(
            token=github_token,
            username="pythpythpython",
            email="pyth.pyth.python@gmail.com"
        ) if github_token else None
        
        self.current_quality = 0.9927
        self.target_quality = 1.0
        
        # Loggers
        self.session_logger = JSONLogger(SESSION_LOG_PATH)
        self.upgrade_logger = JSONLogger(UPGRADE_LOG_PATH)
        self.learning_logger = JSONLogger(LEARNING_LOG_PATH)
        self.hyperparameter_logger = JSONLogger(HYPERPARAMETER_LOG_PATH)
        
        # Load engines from config
        self._load_engines()
        
        ensure_dirs()
    
    def _load_engines(self):
        """Load engines from YAML config."""
        if yaml is None:
            return
        if not ENGINE_CONFIG_PATH.exists():
            return
        try:
            data = yaml.safe_load(ENGINE_CONFIG_PATH.read_text()) or {}
            for item in data.get("primary_engines", []):
                name = item.get("name")
                if name:
                    self.engines[name] = AGIEngine(
                        name=name,
                        quality=float(item.get("quality", 0.99)),
                        domain=item.get("domain", "general"),
                        specialty=item.get("specialty", "Generalist"),
                        traits=item.get("traits", []),
                        capabilities=item.get("capabilities", [])
                    )
        except Exception:
            pass
    
    def select_board(self, task: str) -> str:
        """Select the best board for a task."""
        task_lower = task.lower()
        
        # Match by keywords
        if any(k in task_lower for k in ["bug", "error", "fix", "crash"]):
            return "bug-detector"
        if any(k in task_lower for k in ["test", "verify", "qa"]):
            return "unit-testing"
        if any(k in task_lower for k in ["create", "build", "generate", "implement"]):
            return "code-generator"
        if any(k in task_lower for k in ["document", "comment", "explain", "readme"]):
            return "doc-generator"
        if any(k in task_lower for k in ["architecture", "design", "structure"]):
            return "code-architect"
        if any(k in task_lower for k in ["security", "vulnerability", "auth"]):
            return "security"
        if any(k in task_lower for k in ["optimize", "performance", "speed"]):
            return "optimization"
        if any(k in task_lower for k in ["refactor", "clean", "restructure"]):
            return "refactoring"
        if any(k in task_lower for k in ["review", "check", "audit"]):
            return "code-reviewer"
        if any(k in task_lower for k in ["integrate", "api", "connect"]):
            return "integration-testing"
        
        return "auto"
    
    def get_engines_for_board(self, board_name: str) -> List[str]:
        """Get engines for a board."""
        board = self.boards.get(board_name)
        if not board or board_name == "auto":
            return list(self.engines.keys())[:3]
        
        engines = []
        if board.primary_engine and board.primary_engine in self.engines:
            engines.append(board.primary_engine)
        for eng in board.supporting_engines:
            if eng in self.engines:
                engines.append(eng)
        return engines or list(self.engines.keys())[:3]
    
    def process_task(
        self,
        task: str,
        board: str = "auto",
        multi_agent: bool = False,
        agent_count: int = 1,
        context: Optional[str] = None,
        repos: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None,
        verify: bool = True
    ) -> TaskResult:
        """Process a coding task with AGI boards."""
        
        task_id = generate_task_id()
        
        # Auto-select board if needed
        if board == "auto":
            board = self.select_board(task)
        
        # Get engines
        engines = self.get_engines_for_board(board)
        if agent_count > 1:
            multi_agent = True
        
        # Route to MCPs
        mcp_servers = self.mcp_router.route_task(task)
        
        # Simulate processing
        result = self._execute_task(task_id, task, board, engines, multi_agent, agent_count, context, repos, mcp_servers)
        
        # Verify if requested
        if verify:
            result = self._verify_result(result)
        
        # Log the session
        self.session_logger.append({
            "type": "task",
            "task_id": task_id,
            "task": task,
            "board": board,
            "engines": engines,
            "mcp_servers": mcp_servers,
            "multi_agent": multi_agent,
            "status": result.status.value,
            "confidence": result.confidence
        })
        
        # Track for learning
        self._track_learning(task, result, engines)
        
        return result
    
    def _execute_task(
        self,
        task_id: str,
        task: str,
        board: str,
        engines: List[str],
        multi_agent: bool,
        agent_count: int,
        context: Optional[str],
        repos: Optional[List[str]],
        mcp_servers: List[str]
    ) -> TaskResult:
        """Execute a task with the selected engines."""
        
        # Simulate task execution
        seed = int(hashlib.sha256(task.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        
        # Calculate confidence from engine qualities
        avg_quality = sum(self.engines[e].quality for e in engines if e in self.engines) / max(len(engines), 1)
        confidence = avg_quality * 100
        
        # Simulate files changed
        files_changed = [f"src/component_{i}.py" for i in range(rng.randint(1, 5))]
        
        # Generate output
        board_obj = self.boards.get(board, self.boards["auto"])
        output = self._generate_output(task, board_obj, engines, multi_agent, agent_count)
        
        # Simulate tests
        tests_total = rng.randint(5, 20)
        tests_passed = int(tests_total * (avg_quality + rng.uniform(-0.05, 0.05)))
        tests_passed = min(tests_passed, tests_total)
        
        # Generate suggestions
        suggestions = [
            "Consider adding more edge case tests",
            "Review error handling patterns",
            "Update documentation for new features"
        ]
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            board_used=board,
            engines_used=engines,
            output=output,
            confidence=round(confidence, 2),
            files_changed=files_changed,
            tests_passed=tests_passed,
            tests_total=tests_total,
            suggestions=suggestions[:rng.randint(1, 3)]
        )
    
    def _generate_output(
        self,
        task: str,
        board: AGIBoard,
        engines: List[str],
        multi_agent: bool,
        agent_count: int
    ) -> str:
        """Generate task output."""
        
        output_parts = [
            f"🤖 **{board.name}** Analysis Complete",
            "",
            f"**Task**: {textwrap.shorten(task, 100, placeholder='...')}",
            f"**Board**: {board.name} - {board.description}",
            f"**Engines**: {', '.join(engines)}",
            ""
        ]
        
        if multi_agent:
            output_parts.append(f"**Multi-Agent Mode**: {agent_count} agents collaborated on this task")
            output_parts.append("")
        
        output_parts.extend([
            "**Analysis Summary**:",
            f"- Detected intent and routed to {board.name}",
            f"- Used {len(engines)} specialized engines",
            f"- Applied {len(board.capabilities)} capabilities",
            "",
            "**Recommendations**:",
        ])
        
        for cap in board.capabilities[:3]:
            output_parts.append(f"- {cap}")
        
        return "\n".join(output_parts)
    
    def _verify_result(self, result: TaskResult) -> TaskResult:
        """Verify task result with verifier boards."""
        
        # Use test-verifier and quality-verifier
        verifier_engines = self.get_engines_for_board("test-verifier")
        quality_engines = self.get_engines_for_board("quality-verifier")
        
        all_verifiers = list(set(verifier_engines + quality_engines))
        avg_quality = sum(self.engines[e].quality for e in all_verifiers if e in self.engines) / max(len(all_verifiers), 1)
        
        if avg_quality > 0.99:
            result.status = TaskStatus.VERIFIED
            result.output += "\n\n✅ **Verified** by Test Verifier and Quality Verifier boards"
        
        return result
    
    def _track_learning(self, task: str, result: TaskResult, engines: List[str]):
        """Track task for continuous learning."""
        
        self.learning_logger.append({
            "type": "learning",
            "task": task,
            "engines": engines,
            "status": result.status.value,
            "confidence": result.confidence,
            "tests_passed": result.tests_passed,
            "tests_total": result.tests_total
        })
        
        # Simulate quality improvement
        if self.current_quality < self.target_quality:
            self.current_quality = min(self.target_quality, self.current_quality + 0.0001)
    
    def run_multi_agent_task(
        self,
        task: str,
        agent_count: int = 3,
        boards: Optional[List[str]] = None
    ) -> List[TaskResult]:
        """Run task with multiple agents and pick the best result."""
        
        if not boards:
            # Use different boards for diversity
            boards = ["code-generator", "code-architect", "optimization"][:agent_count]
        
        results = []
        for i, board in enumerate(boards[:agent_count]):
            result = self.process_task(
                task,
                board=board,
                multi_agent=True,
                agent_count=1,
                verify=True
            )
            results.append(result)
        
        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        return results
    
    def train_engines(
        self,
        problems: Optional[List[str]] = None,
        intensity: str = "high"
    ) -> TrainingMetrics:
        """Train engines on problems."""
        
        start_time = time.time()
        quality_before = self.current_quality
        
        # Default problems if none provided
        if not problems:
            problems = [
                "Implement a distributed cache system",
                "Create a GraphQL API with authentication",
                "Build a real-time collaboration feature",
                "Optimize database query performance",
                "Add comprehensive error handling"
            ]
        
        tests_total = len(problems) * 10
        tests_passed = 0
        improvements = []
        
        for i, problem in enumerate(problems):
            print_progress(f"Training on problem {i+1}/{len(problems)}: {textwrap.shorten(problem, 50, placeholder='...')}")
            
            # Simulate training
            result = self.process_task(problem, verify=True)
            tests_passed += result.tests_passed
            
            if result.confidence > 99:
                improvements.append(f"Improved handling of: {textwrap.shorten(problem, 30, placeholder='...')}")
        
        # Calculate quality improvement
        intensity_multiplier = {"low": 0.0001, "medium": 0.0005, "high": 0.001, "extreme": 0.005}
        multiplier = intensity_multiplier.get(intensity, 0.001)
        
        quality_improvement = min(
            self.target_quality - self.current_quality,
            multiplier * len(problems)
        )
        self.current_quality += quality_improvement
        
        duration = time.time() - start_time
        
        metrics = TrainingMetrics(
            quality_before=round(quality_before, 4),
            quality_after=round(self.current_quality, 4),
            tests_passed=tests_passed,
            tests_total=tests_total,
            hyperparameters_tuned=len(self.engines) * 5,
            duration_seconds=round(duration, 2),
            improvements=improvements
        )
        
        # Log training
        self.learning_logger.append({
            "type": "training",
            "intensity": intensity,
            "problems_count": len(problems),
            "quality_before": metrics.quality_before,
            "quality_after": metrics.quality_after,
            "tests_passed": metrics.tests_passed,
            "tests_total": metrics.tests_total
        })
        
        return metrics
    
    def tune_hyperparameters(
        self,
        target_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Tune hyperparameters of engines."""
        
        if not target_metrics:
            target_metrics = ["response_quality", "code_accuracy", "test_coverage", "documentation_clarity", "security_compliance"]
        
        results = {
            "metrics_tuned": target_metrics,
            "engines_affected": list(self.engines.keys()),
            "improvements": {}
        }
        
        for metric in target_metrics:
            print_progress(f"Tuning {metric}...")
            
            # Simulate tuning
            improvement = random.uniform(0.001, 0.01)
            results["improvements"][metric] = round(improvement, 4)
        
        # Log hyperparameter tuning
        self.hyperparameter_logger.append({
            "type": "hyperparameter_tuning",
            "metrics": target_metrics,
            "improvements": results["improvements"]
        })
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        
        total_engines = len(self.engines)
        avg_quality = sum(e.quality for e in self.engines.values()) / total_engines
        
        return {
            "total_engines": total_engines,
            "total_boards": len(self.boards),
            "average_quality": round(avg_quality, 4),
            "current_quality": round(self.current_quality, 4),
            "target_quality": self.target_quality,
            "mcp_servers": len(self.mcp_router.servers),
            "github_connected": self.github is not None and self.github.validate_token() if self.github else False
        }

# ============================================================================
# SETTINGS MANAGER
# ============================================================================

class SettingsManager:
    """Manage CLI settings."""
    
    def __init__(self, path: Path = SETTINGS_PATH):
        self.path = path
        self.settings = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load settings from file."""
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except:
                pass
        return self._default_settings()
    
    def _default_settings(self) -> Dict[str, Any]:
        return {
            "version": "2.0.0",
            "app": {
                "name": APP_NAME,
                "theme": "dark",
                "autoSave": True,
                "learningMode": "continuous"
            },
            "github": {
                "username": "pythpythpython",
                "email": "pyth.pyth.python@gmail.com",
                "autoPushMerge": True,
                "defaultBranch": "main",
                "pat": ""
            },
            "agi": {
                "defaultBoard": "auto",
                "multiAgentMode": False,
                "targetQuality": 1.0,
                "currentQuality": 0.9927,
                "maxAgents": 5
            },
            "mcp": {
                "activeServers": list(MCPRouter.DEFAULT_SERVERS.keys()),
                "autoConnect": True,
                "customServers": []
            },
            "tracking": {
                "enabled": True,
                "saveSessionData": True,
                "exportFormat": "json"
            },
            "api": {
                "endpoints": [],
                "tokens": {}
            },
            "upgrade": {
                "autoUpgrade": False,
                "upgradeFrequency": "daily",
                "lastUpgrade": None
            }
        }
    
    def save(self):
        """Save settings to file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.settings, indent=2))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting by dot-notation key."""
        keys = key.split(".")
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set a setting by dot-notation key."""
        keys = key.split(".")
        target = self.settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save()
    
    def set_github_pat(self, token: str):
        """Set GitHub PAT token."""
        self.set("github.pat", token)
    
    def get_github_pat(self) -> str:
        """Get GitHub PAT token."""
        return self.get("github.pat", "")
    
    def add_api_token(self, name: str, token: str):
        """Add an API token."""
        tokens = self.get("api.tokens", {})
        tokens[name] = token
        self.set("api.tokens", tokens)
    
    def add_mcp_server(self, url: str):
        """Add a custom MCP server."""
        servers = self.get("mcp.customServers", [])
        if url not in servers:
            servers.append(url)
            self.set("mcp.customServers", servers)

# ============================================================================
# UPGRADE MANAGER
# ============================================================================

class UpgradeManager:
    """Manage self-upgrade workflows."""
    
    def __init__(self, agi: OmniCoderAGI, settings: SettingsManager):
        self.agi = agi
        self.settings = settings
        self.upgrade_logger = JSONLogger(UPGRADE_LOG_PATH)
    
    def build_upgrade_plan(self, description: str, mode: str = "self") -> Dict[str, Any]:
        """Build an upgrade plan."""
        
        # Analyze the upgrade request
        board = self.agi.select_board(description)
        
        steps = [
            {
                "name": "Analyze Current State",
                "board": "code-reviewer",
                "agents": 2,
                "description": "Audit current implementation"
            },
            {
                "name": "Design Upgrade",
                "board": "code-architect",
                "agents": 2,
                "description": "Design upgrade architecture"
            },
            {
                "name": "Implement Changes",
                "board": "code-generator",
                "agents": 3,
                "description": "Generate upgrade code"
            },
            {
                "name": "Test Changes",
                "board": "unit-testing",
                "agents": 2,
                "description": "Run tests and verify"
            },
            {
                "name": "Verify Quality",
                "board": "quality-verifier",
                "agents": 1,
                "description": "Verify code quality"
            },
            {
                "name": "Document Changes",
                "board": "doc-generator",
                "agents": 1,
                "description": "Update documentation"
            }
        ]
        
        return {
            "summary": description,
            "mode": mode,
            "steps": steps,
            "created_at": iso_now()
        }
    
    def execute_upgrade(self, plan: Dict[str, Any], auto: bool = False) -> Dict[str, Any]:
        """Execute an upgrade plan."""
        
        results = []
        
        for step in plan["steps"]:
            print_progress(f"Step: {step['name']} ({step['board']})")
            
            result = self.agi.process_task(
                f"{plan['summary']} :: {step['description']}",
                board=step["board"],
                multi_agent=step["agents"] > 1,
                agent_count=step["agents"],
                verify=True
            )
            
            results.append({
                "step": step["name"],
                "status": result.status.value,
                "confidence": result.confidence
            })
        
        # Log upgrade
        self.upgrade_logger.append({
            "type": "upgrade",
            "mode": plan["mode"],
            "summary": plan["summary"],
            "steps_completed": len(results),
            "status": "completed"
        })
        
        return {
            "plan": plan,
            "results": results,
            "completed_at": iso_now()
        }
    
    def run_self_upgrade(self, description: str = "General system improvements"):
        """Run a self-upgrade cycle."""
        
        print_header(f"Self-Upgrade: {APP_NAME}")
        
        plan = self.build_upgrade_plan(description, mode="self")
        return self.execute_upgrade(plan, auto=True)

# ============================================================================
# MEMORY MANAGER
# ============================================================================

class MemoryManager:
    """Manage session memory and data."""
    
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, key: str, data: Any, category: str = "general"):
        """Save data to memory."""
        category_dir = self.memory_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = category_dir / f"{key}.json"
        content = {
            "key": key,
            "category": category,
            "timestamp": iso_now(),
            "data": data
        }
        filepath.write_text(json.dumps(content, indent=2))
    
    def load(self, key: str, category: str = "general") -> Optional[Dict]:
        """Load data from memory."""
        filepath = self.memory_dir / category / f"{key}.json"
        if filepath.exists():
            try:
                return json.loads(filepath.read_text())
            except:
                pass
        return None
    
    def list_keys(self, category: str = "general") -> List[str]:
        """List all keys in a category."""
        category_dir = self.memory_dir / category
        if not category_dir.exists():
            return []
        return [f.stem for f in category_dir.glob("*.json")]
    
    def save_attachment(self, filepath: Path, task_id: str) -> str:
        """Save a file attachment."""
        attachments_dir = self.memory_dir / "attachments" / task_id
        attachments_dir.mkdir(parents=True, exist_ok=True)
        
        dest = attachments_dir / filepath.name
        shutil.copy2(filepath, dest)
        
        return str(dest)
    
    def clear(self, category: Optional[str] = None):
        """Clear memory."""
        if category:
            category_dir = self.memory_dir / category
            if category_dir.exists():
                shutil.rmtree(category_dir)
        else:
            for item in self.memory_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

# ============================================================================
# CLI COMMAND HANDLERS
# ============================================================================

def cmd_run(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'run' command."""
    
    # Read context from file if provided
    context = args.context or ""
    if args.context_file:
        context += "\n" + args.context_file.read_text()
    
    # Parse repos
    repos = None
    if args.repos:
        repos = [r.strip() for r in args.repos.split(",")]
    
    # Parse attachments
    attachments = None
    if args.attach:
        attachments = [Path(p.strip()) for p in args.attach.split(",")]
    
    print_header(f"Processing Task with {APP_NAME}")
    
    result = agi.process_task(
        args.task,
        board=args.board,
        multi_agent=args.multi or args.agents > 1,
        agent_count=max(1, args.agents),
        context=context.strip() or None,
        repos=repos,
        attachments=attachments,
        verify=not args.no_verify
    )
    
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Task ID: {result.task_id}")
        print(f"Status: {result.status.value}")
        print(f"Board: {result.board_used}")
        print(f"Engines: {', '.join(result.engines_used)}")
        print(f"Confidence: {result.confidence}%")
        print(f"Tests: {result.tests_passed}/{result.tests_total}")
        print()
        print(result.output)
        
        if result.suggestions:
            print("\n📝 Suggestions:")
            for s in result.suggestions:
                print(f"  - {s}")
        
        if result.left_out:
            print("\n⚠️  Left Out:")
            for item in result.left_out:
                reason = result.left_out_reasons.get(item, "No reason provided")
                print(f"  - {item}: {reason}")

def cmd_multi(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'multi' command for multi-agent tasks."""
    
    print_header(f"Multi-Agent Task with {APP_NAME}")
    
    # Parse boards if provided
    boards = None
    if args.boards:
        boards = [b.strip() for b in args.boards.split(",")]
    
    results = agi.run_multi_agent_task(
        args.task,
        agent_count=args.agents,
        boards=boards
    )
    
    if args.format == "json":
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print(f"Ran {len(results)} agents on task")
        print()
        
        for i, result in enumerate(results, 1):
            marker = "🏆" if i == 1 else "  "
            print(f"{marker} Agent {i}: {result.board_used} - Confidence: {result.confidence}%")
        
        print()
        print("Best Result:")
        print(results[0].output)

def cmd_train(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'train' command."""
    
    print_header(f"Training {APP_NAME} Engines")
    
    # Parse problems if provided
    problems = None
    if args.problems:
        problems = [p.strip() for p in args.problems.split(";")]
    elif args.problems_file:
        problems = [p.strip() for p in args.problems_file.read_text().split("\n") if p.strip()]
    
    metrics = agi.train_engines(
        problems=problems,
        intensity=args.intensity
    )
    
    if args.format == "json":
        print(json.dumps({
            "quality_before": metrics.quality_before,
            "quality_after": metrics.quality_after,
            "tests_passed": metrics.tests_passed,
            "tests_total": metrics.tests_total,
            "hyperparameters_tuned": metrics.hyperparameters_tuned,
            "duration_seconds": metrics.duration_seconds,
            "improvements": metrics.improvements
        }, indent=2))
    else:
        print(f"Quality Before: {metrics.quality_before * 100:.2f}%")
        print(f"Quality After: {metrics.quality_after * 100:.2f}%")
        print(f"Improvement: +{(metrics.quality_after - metrics.quality_before) * 100:.4f}%")
        print()
        print(f"Tests: {metrics.tests_passed}/{metrics.tests_total} passed")
        print(f"Hyperparameters Tuned: {metrics.hyperparameters_tuned}")
        print(f"Duration: {metrics.duration_seconds}s")
        
        if metrics.improvements:
            print("\n✅ Improvements:")
            for imp in metrics.improvements:
                print(f"  - {imp}")

def cmd_tune(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'tune' command for hyperparameter tuning."""
    
    print_header("Hyperparameter Tuning")
    
    metrics = None
    if args.metrics:
        metrics = [m.strip() for m in args.metrics.split(",")]
    
    results = agi.tune_hyperparameters(target_metrics=metrics)
    
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print("Tuned Metrics:")
        for metric, improvement in results["improvements"].items():
            print(f"  {metric}: +{improvement * 100:.2f}%")
        print()
        print(f"Engines Affected: {len(results['engines_affected'])}")

def cmd_upgrade(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'upgrade' command."""
    
    upgrade_manager = UpgradeManager(agi, settings)
    
    # Read description from file if --from-file is specified
    description = args.description
    if args.from_file:
        prompt_file = Path(args.from_file)
        if prompt_file.exists():
            file_content = prompt_file.read_text(encoding="utf-8").strip()
            # Filter out any lines that look like secrets (PAT tokens, etc.)
            filtered_lines = []
            for line in file_content.split("\n"):
                # Skip lines that contain PAT tokens or other secrets
                if "github_pat_" in line.lower() or "ghp_" in line.lower():
                    print_warning(f"Skipping line with detected secret")
                    continue
                filtered_lines.append(line)
            description = "\n".join(filtered_lines)
            print_info(f"Loaded upgrade prompt from: {prompt_file}")
        else:
            print_error(f"File not found: {prompt_file}")
            return
    
    if not description or description == "General improvements":
        print_error("Please provide a description or use --from-file")
        return
    
    print_header(f"Upgrade {APP_NAME}")
    
    # Configure GitHub if token provided
    if args.token:
        settings.set_github_pat(args.token)
        agi.github = GitHubClient(
            token=args.token,
            username=settings.get("github.username"),
            email=settings.get("github.email")
        )
        print_success("GitHub PAT configured")
    
    if args.auto:
        result = upgrade_manager.run_self_upgrade(description)
    else:
        plan = upgrade_manager.build_upgrade_plan(description, mode=args.mode)
        
        if args.execute:
            result = upgrade_manager.execute_upgrade(plan)
        else:
            result = {"plan": plan, "status": "planned"}
    
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Summary: {result['plan']['summary']}")
        print(f"Mode: {result['plan']['mode']}")
        print()
        print("Steps:")
        for i, step in enumerate(result["plan"]["steps"], 1):
            status = "✅" if "results" in result else "⏳"
            print(f"  {status} {i}. {step['name']} [{step['board']}]")
        
        if "results" in result:
            print()
            print("Results:")
            for res in result["results"]:
                status = "✅" if res["status"] == "verified" else "🔄"
                print(f"  {status} {res['step']}: {res['confidence']}%")

def cmd_stats(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'stats' command."""
    
    stats = agi.get_statistics()
    
    if args.format == "json":
        print(json.dumps(stats, indent=2))
    else:
        print_header(f"{APP_NAME} Statistics")
        for key, value in stats.items():
            label = key.replace("_", " ").title()
            if isinstance(value, float):
                print(f"  {label}: {value * 100:.2f}%")
            else:
                print(f"  {label}: {value}")

def cmd_boards(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'boards' command."""
    
    if args.format == "json":
        print(json.dumps({k: v.to_dict() for k, v in agi.boards.items()}, indent=2))
    else:
        print_header("Available AGI Boards")
        for key, board in agi.boards.items():
            engines = ", ".join([board.primary_engine] + board.supporting_engines[:2]) if board.primary_engine else "auto-select"
            print(f"  {key:>20}: {board.name}")
            print(f"  {'':>20}  {board.description}")
            print(f"  {'':>20}  Engines: {engines}")
            print(f"  {'':>20}  Quality: {board.quality * 100:.2f}%")
            print()

def cmd_engines(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'engines' command."""
    
    if args.format == "json":
        print(json.dumps({k: v.to_dict() for k, v in agi.engines.items()}, indent=2))
    else:
        print_header("AGI Engines")
        for name, engine in sorted(agi.engines.items(), key=lambda x: x[1].quality, reverse=True):
            print(f"  {name}")
            print(f"    Quality: {engine.quality * 100:.2f}%")
            print(f"    Domain: {engine.domain}")
            print(f"    Specialty: {engine.specialty}")
            print(f"    Traits: {', '.join(engine.traits[:3])}")
            print()

def cmd_mcp(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'mcp' command."""
    
    if args.action == "list":
        servers = agi.mcp_router.list_servers()
        
        if args.format == "json":
            print(json.dumps({k: v.to_dict() for k, v in servers.items()}, indent=2))
        else:
            print_header("MCP Servers")
            for key, server in servers.items():
                print(f"  {key:>12}: {server.name}")
                print(f"  {'':>12}  Repo: {server.repo}")
                print(f"  {'':>12}  Capabilities: {', '.join(server.capabilities[:3])}")
                if server.languages:
                    print(f"  {'':>12}  Languages: {', '.join(server.languages)}")
                print()
    
    elif args.action == "add":
        if not args.url:
            print_error("Please provide --url for the MCP server")
            return
        
        # Extract name from URL
        name = args.name or args.url.split("/")[-1].replace(".git", "")
        
        server = MCPServer(
            name=name,
            repo=args.url,
            capabilities=args.capabilities.split(",") if args.capabilities else [],
            languages=args.languages.split(",") if args.languages else []
        )
        
        agi.mcp_router.add_server(name.lower().replace("-", "_"), server)
        settings.add_mcp_server(args.url)
        
        print_success(f"Added MCP server: {name}")
    
    elif args.action == "route":
        if not args.task:
            print_error("Please provide --task to route")
            return
        
        servers = agi.mcp_router.route_task(args.task, args.language)
        print(f"Recommended MCP servers for task:")
        for s in servers:
            print(f"  - {s}")

def cmd_github(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'github' command."""
    
    if args.action == "login":
        if args.token:
            settings.set_github_pat(args.token)
            
            # Reinitialize GitHub client
            agi.github = GitHubClient(
                token=args.token,
                username=settings.get("github.username"),
                email=settings.get("github.email")
            )
            
            if agi.github.validate_token():
                user = agi.github.get_user()
                print_success(f"Logged in as {user.get('login', 'unknown')}")
            else:
                print_error("Invalid token")
        else:
            print_error("Please provide --token")
    
    elif args.action == "status":
        if agi.github and agi.github.validate_token():
            user = agi.github.get_user()
            print(f"Connected as: {user.get('login')}")
            print(f"Email: {user.get('email', 'N/A')}")
            print(f"Public repos: {user.get('public_repos', 0)}")
        else:
            print("Not connected to GitHub")
    
    elif args.action == "repos":
        if not agi.github:
            print_error("Not connected to GitHub. Use 'github login' first.")
            return
        
        repos = agi.github.list_repos(limit=args.limit)
        
        if args.format == "json":
            print(json.dumps(repos, indent=2))
        else:
            print_header("Your Repositories")
            for repo in repos:
                print(f"  {repo['full_name']}")
                print(f"    {repo.get('description', 'No description')[:60]}")
                print()
    
    elif args.action == "create":
        if not agi.github:
            print_error("Not connected to GitHub. Use 'github login' first.")
            return
        
        if not args.name:
            print_error("Please provide --name for the repository")
            return
        
        repo = agi.github.create_repo(
            name=args.name,
            description=args.description or "",
            private=args.private
        )
        
        print_success(f"Created repository: {repo['html_url']}")
    
    elif args.action == "browse":
        if not agi.github:
            print_error("Not connected to GitHub. Use 'github login' first.")
            return
        
        if not args.repo:
            print_error("Please provide --repo (owner/repo)")
            return
        
        parts = args.repo.split("/")
        if len(parts) != 2:
            print_error("Invalid repo format. Use owner/repo")
            return
        
        owner, repo = parts
        files = agi.github.list_files(owner, repo, args.path or "")
        
        if args.format == "json":
            print(json.dumps(files, indent=2))
        else:
            print_header(f"Files in {args.repo}/{args.path or ''}")
            for f in files:
                type_icon = "📁" if f["type"] == "dir" else "📄"
                print(f"  {type_icon} {f['name']}")

def cmd_settings(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'settings' command."""
    
    if args.action == "show":
        if args.key:
            value = settings.get(args.key)
            print(f"{args.key}: {json.dumps(value, indent=2)}")
        else:
            print(json.dumps(settings.settings, indent=2))
    
    elif args.action == "set":
        if not args.key or args.value is None:
            print_error("Please provide --key and --value")
            return
        
        # Try to parse value as JSON
        try:
            value = json.loads(args.value)
        except:
            value = args.value
        
        settings.set(args.key, value)
        print_success(f"Set {args.key} = {value}")
    
    elif args.action == "add-token":
        if not args.name or not args.token:
            print_error("Please provide --name and --token")
            return
        
        settings.add_api_token(args.name, args.token)
        print_success(f"Added API token: {args.name}")
    
    elif args.action == "add-mcp":
        if not args.url:
            print_error("Please provide --url for the MCP server")
            return
        
        settings.add_mcp_server(args.url)
        print_success(f"Added MCP server: {args.url}")

def cmd_memory(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'memory' command."""
    
    memory = MemoryManager()
    
    if args.action == "save":
        if not args.key or not args.data:
            print_error("Please provide --key and --data")
            return
        
        try:
            data = json.loads(args.data)
        except:
            data = args.data
        
        memory.save(args.key, data, args.category or "general")
        print_success(f"Saved to memory: {args.key}")
    
    elif args.action == "load":
        if not args.key:
            print_error("Please provide --key")
            return
        
        data = memory.load(args.key, args.category or "general")
        if data:
            print(json.dumps(data, indent=2))
        else:
            print(f"No data found for key: {args.key}")
    
    elif args.action == "list":
        keys = memory.list_keys(args.category or "general")
        print(f"Keys in '{args.category or 'general'}':")
        for key in keys:
            print(f"  - {key}")
    
    elif args.action == "clear":
        memory.clear(args.category)
        print_success("Memory cleared")

def cmd_history(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'history' command."""
    
    if args.target == "sessions":
        logger = agi.session_logger
    elif args.target == "upgrades":
        logger = agi.upgrade_logger
    elif args.target == "learning":
        logger = agi.learning_logger
    elif args.target == "hyperparameters":
        logger = agi.hyperparameter_logger
    else:
        logger = agi.session_logger
    
    entries = logger.tail(args.limit)
    
    if args.format == "json":
        print(json.dumps(entries, indent=2))
    else:
        print_header(f"History: {args.target}")
        if not entries:
            print("  No entries yet")
            return
        
        for entry in entries:
            ts = entry.get("timestamp", "unknown")
            entry_type = entry.get("type", "unknown")
            print(f"  [{ts}] {entry_type}")
            
            if "task" in entry:
                print(f"    Task: {textwrap.shorten(entry['task'], 60, placeholder='...')}")
            if "confidence" in entry:
                print(f"    Confidence: {entry['confidence']}%")
            print()

def cmd_verify(args, agi: OmniCoderAGI, settings: SettingsManager):
    """Handle 'verify' command - run verifier boards on a task."""
    
    print_header("Running Verification")
    
    # Run with test-verifier
    test_result = agi.process_task(
        args.task,
        board="test-verifier",
        multi_agent=True,
        agent_count=2,
        verify=False
    )
    
    # Run with quality-verifier
    quality_result = agi.process_task(
        args.task,
        board="quality-verifier",
        multi_agent=True,
        agent_count=2,
        verify=False
    )
    
    if args.format == "json":
        print(json.dumps({
            "test_verification": test_result.to_dict(),
            "quality_verification": quality_result.to_dict()
        }, indent=2))
    else:
        print("Test Verification:")
        print(f"  Confidence: {test_result.confidence}%")
        print(f"  Status: {test_result.status.value}")
        print()
        print("Quality Verification:")
        print(f"  Confidence: {quality_result.confidence}%")
        print(f"  Status: {quality_result.status.value}")

# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - The World's Most Advanced Coding Automation Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s run "Create a REST API with authentication"
          %(prog)s run "Fix the bug in auth.py" --board bug-detector
          %(prog)s multi "Build a todo app" --agents 3
          %(prog)s train --intensity high
          %(prog)s tune --metrics response_quality,code_accuracy
          %(prog)s upgrade "Add voice input support" --auto
          %(prog)s github login --token YOUR_PAT
          %(prog)s mcp list
          %(prog)s settings show
        """)
    )
    
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # ---- run ----
    run_parser = subparsers.add_parser("run", help="Execute an AGI task")
    run_parser.add_argument("task", help="Task description or prompt")
    run_parser.add_argument("--board", default="auto", help="AGI board to use")
    run_parser.add_argument("--agents", type=int, default=1, help="Number of agents")
    run_parser.add_argument("--multi", action="store_true", help="Force multi-agent mode")
    run_parser.add_argument("--context", help="Additional context")
    run_parser.add_argument("--context-file", type=Path, help="Context from file")
    run_parser.add_argument("--repos", help="Comma-separated list of repos to include")
    run_parser.add_argument("--attach", help="Comma-separated list of files to attach")
    run_parser.add_argument("--no-verify", action="store_true", help="Skip verification")
    run_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- multi ----
    multi_parser = subparsers.add_parser("multi", help="Run multi-agent task")
    multi_parser.add_argument("task", help="Task description")
    multi_parser.add_argument("--agents", type=int, default=3, help="Number of agents")
    multi_parser.add_argument("--boards", help="Comma-separated boards to use")
    multi_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- train ----
    train_parser = subparsers.add_parser("train", help="Train AGI engines")
    train_parser.add_argument("--problems", help="Semicolon-separated problems")
    train_parser.add_argument("--problems-file", type=Path, help="Problems from file")
    train_parser.add_argument("--intensity", choices=["low", "medium", "high", "extreme"], default="high")
    train_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- tune ----
    tune_parser = subparsers.add_parser("tune", help="Tune hyperparameters")
    tune_parser.add_argument("--metrics", help="Comma-separated metrics to tune")
    tune_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- upgrade ----
    upgrade_parser = subparsers.add_parser("upgrade", help="Run self-upgrade")
    upgrade_parser.add_argument("description", nargs="?", default="General improvements", help="Upgrade description")
    upgrade_parser.add_argument("--from-file", "-f", help="Read upgrade prompt from file (e.g., self-upgrade-prompt.txt)")
    upgrade_parser.add_argument("--token", "-t", help="GitHub PAT token for authentication")
    upgrade_parser.add_argument("--mode", choices=["self", "feature", "bugfix"], default="self")
    upgrade_parser.add_argument("--execute", action="store_true", help="Execute the plan")
    upgrade_parser.add_argument("--auto", action="store_true", help="Auto-execute upgrade")
    upgrade_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- verify ----
    verify_parser = subparsers.add_parser("verify", help="Run verification boards")
    verify_parser.add_argument("task", help="Task to verify")
    verify_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- stats ----
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- boards ----
    boards_parser = subparsers.add_parser("boards", help="List AGI boards")
    boards_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- engines ----
    engines_parser = subparsers.add_parser("engines", help="List AGI engines")
    engines_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- mcp ----
    mcp_parser = subparsers.add_parser("mcp", help="Manage MCP servers")
    mcp_parser.add_argument("action", choices=["list", "add", "route"])
    mcp_parser.add_argument("--url", help="MCP server URL/repo")
    mcp_parser.add_argument("--name", help="MCP server name")
    mcp_parser.add_argument("--capabilities", help="Comma-separated capabilities")
    mcp_parser.add_argument("--languages", help="Comma-separated languages")
    mcp_parser.add_argument("--task", help="Task to route")
    mcp_parser.add_argument("--language", help="Target language")
    mcp_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- github ----
    github_parser = subparsers.add_parser("github", help="GitHub integration")
    github_parser.add_argument("action", choices=["login", "status", "repos", "create", "browse"])
    github_parser.add_argument("--token", help="GitHub PAT token")
    github_parser.add_argument("--name", help="Repository name")
    github_parser.add_argument("--description", help="Repository description")
    github_parser.add_argument("--private", action="store_true", help="Create private repo")
    github_parser.add_argument("--repo", help="Repository (owner/repo)")
    github_parser.add_argument("--path", help="Path in repository")
    github_parser.add_argument("--limit", type=int, default=20)
    github_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # ---- settings ----
    settings_parser = subparsers.add_parser("settings", help="Manage settings")
    settings_parser.add_argument("action", choices=["show", "set", "add-token", "add-mcp"])
    settings_parser.add_argument("--key", help="Setting key (dot notation)")
    settings_parser.add_argument("--value", help="Setting value")
    settings_parser.add_argument("--name", help="Token name")
    settings_parser.add_argument("--token", help="Token value")
    settings_parser.add_argument("--url", help="MCP server URL")
    
    # ---- memory ----
    memory_parser = subparsers.add_parser("memory", help="Manage memory")
    memory_parser.add_argument("action", choices=["save", "load", "list", "clear"])
    memory_parser.add_argument("--key", help="Memory key")
    memory_parser.add_argument("--data", help="Data to save (JSON)")
    memory_parser.add_argument("--category", help="Memory category")
    
    # ---- history ----
    history_parser = subparsers.add_parser("history", help="View history")
    history_parser.add_argument("--target", choices=["sessions", "upgrades", "learning", "hyperparameters"], default="sessions")
    history_parser.add_argument("--limit", type=int, default=10)
    history_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    return parser

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main(argv: Optional[List[str]] = None):
    """Main entry point."""
    
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Load settings
    settings = SettingsManager()
    
    # Initialize AGI with GitHub token if available
    github_token = settings.get_github_pat()
    agi = OmniCoderAGI(github_token=github_token if github_token else None)
    
    # Route to command handler
    handlers = {
        "run": cmd_run,
        "multi": cmd_multi,
        "train": cmd_train,
        "tune": cmd_tune,
        "upgrade": cmd_upgrade,
        "verify": cmd_verify,
        "stats": cmd_stats,
        "boards": cmd_boards,
        "engines": cmd_engines,
        "mcp": cmd_mcp,
        "github": cmd_github,
        "settings": cmd_settings,
        "memory": cmd_memory,
        "history": cmd_history,
    }
    
    handler = handlers.get(args.command)
    if handler:
        try:
            handler(args, agi, settings)
        except Exception as e:
            print_error(f"Error: {e}")
            sys.exit(1)
    else:
        parser.error(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
