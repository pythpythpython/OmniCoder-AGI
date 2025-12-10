#!/usr/bin/env python3
"""
Real-time Collaboration Module for OmniCoder-AGI CLI

Provides collaborative features for team coding sessions.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

@dataclass
class CollaboratorInfo:
    """Information about a collaborator."""
    id: str
    name: str
    email: str
    role: str = "contributor"
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class CollaborationSession:
    """A collaborative coding session."""
    session_id: str
    name: str
    created_by: str
    created_at: str
    task: str
    collaborators: List[CollaboratorInfo] = field(default_factory=list)
    messages: List[Dict] = field(default_factory=list)
    changes: List[Dict] = field(default_factory=list)
    status: str = "active"
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['collaborators'] = [c.to_dict() if isinstance(c, CollaboratorInfo) else c for c in self.collaborators]
        return result

class CollaborationManager:
    """Manages real-time collaboration sessions."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, CollaborationSession] = {}
        self.current_session: Optional[str] = None
        self._load_sessions()
        
        # Event callbacks
        self._on_message: Optional[Callable] = None
        self._on_change: Optional[Callable] = None
        self._on_join: Optional[Callable] = None
    
    def _load_sessions(self):
        """Load existing sessions from storage."""
        sessions_file = self.storage_path / "sessions.json"
        if sessions_file.exists():
            try:
                data = json.loads(sessions_file.read_text())
                for session_data in data.get("sessions", []):
                    session = CollaborationSession(
                        session_id=session_data["session_id"],
                        name=session_data["name"],
                        created_by=session_data["created_by"],
                        created_at=session_data["created_at"],
                        task=session_data["task"],
                        status=session_data.get("status", "active")
                    )
                    self.sessions[session.session_id] = session
            except Exception:
                pass
    
    def _save_sessions(self):
        """Save sessions to storage."""
        sessions_file = self.storage_path / "sessions.json"
        data = {
            "sessions": [s.to_dict() for s in self.sessions.values()]
        }
        sessions_file.write_text(json.dumps(data, indent=2))
    
    def create_session(self, name: str, task: str, creator: CollaboratorInfo) -> CollaborationSession:
        """Create a new collaboration session."""
        session = CollaborationSession(
            session_id=str(uuid.uuid4())[:8],
            name=name,
            created_by=creator.id,
            created_at=datetime.utcnow().isoformat(),
            task=task,
            collaborators=[creator]
        )
        
        self.sessions[session.session_id] = session
        self.current_session = session.session_id
        self._save_sessions()
        
        return session
    
    def join_session(self, session_id: str, collaborator: CollaboratorInfo) -> Optional[CollaborationSession]:
        """Join an existing session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check if already in session
        existing = next((c for c in session.collaborators if c.id == collaborator.id), None)
        if not existing:
            session.collaborators.append(collaborator)
            self._save_sessions()
            
            if self._on_join:
                self._on_join(collaborator, session)
        
        self.current_session = session_id
        return session
    
    def leave_session(self, session_id: str, collaborator_id: str):
        """Leave a session."""
        session = self.sessions.get(session_id)
        if session:
            session.collaborators = [c for c in session.collaborators if c.id != collaborator_id]
            self._save_sessions()
    
    def send_message(self, session_id: str, sender_id: str, content: str):
        """Send a message in a session."""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        message = {
            "id": str(uuid.uuid4())[:8],
            "sender_id": sender_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        session.messages.append(message)
        self._save_session_data(session)
        
        if self._on_message:
            self._on_message(message, session)
    
    def broadcast_change(self, session_id: str, change: Dict):
        """Broadcast a code change to all collaborators."""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        change_entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().isoformat(),
            **change
        }
        
        session.changes.append(change_entry)
        self._save_session_data(session)
        
        if self._on_change:
            self._on_change(change_entry, session)
    
    def _save_session_data(self, session: CollaborationSession):
        """Save detailed session data."""
        session_file = self.storage_path / f"session_{session.session_id}.json"
        session_file.write_text(json.dumps(session.to_dict(), indent=2))
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self, status: str = "active") -> List[CollaborationSession]:
        """List sessions by status."""
        return [s for s in self.sessions.values() if s.status == status]
    
    def end_session(self, session_id: str):
        """End a session."""
        session = self.sessions.get(session_id)
        if session:
            session.status = "ended"
            self._save_sessions()
            self._save_session_data(session)
    
    def on_message(self, callback: Callable):
        """Register message callback."""
        self._on_message = callback
    
    def on_change(self, callback: Callable):
        """Register change callback."""
        self._on_change = callback
    
    def on_join(self, callback: Callable):
        """Register join callback."""
        self._on_join = callback


class CollaborationCLI:
    """CLI interface for collaboration features."""
    
    def __init__(self, manager: CollaborationManager, user: CollaboratorInfo):
        self.manager = manager
        self.user = user
    
    def create(self, name: str, task: str) -> str:
        """Create a new session."""
        session = self.manager.create_session(name, task, self.user)
        return f"✅ Created session: {session.name} (ID: {session.session_id})"
    
    def join(self, session_id: str) -> str:
        """Join a session."""
        session = self.manager.join_session(session_id, self.user)
        if session:
            return f"✅ Joined session: {session.name}"
        return f"❌ Session not found: {session_id}"
    
    def leave(self, session_id: str) -> str:
        """Leave a session."""
        self.manager.leave_session(session_id, self.user.id)
        return "✅ Left session"
    
    def message(self, content: str) -> str:
        """Send a message to current session."""
        if not self.manager.current_session:
            return "❌ Not in a session"
        
        self.manager.send_message(
            self.manager.current_session,
            self.user.id,
            content
        )
        return "✅ Message sent"
    
    def list_sessions(self) -> str:
        """List active sessions."""
        sessions = self.manager.list_sessions()
        if not sessions:
            return "No active sessions"
        
        lines = ["Active Sessions:"]
        for s in sessions:
            lines.append(f"  [{s.session_id}] {s.name} - {len(s.collaborators)} collaborators")
        return "\n".join(lines)
    
    def show_session(self, session_id: str) -> str:
        """Show session details."""
        session = self.manager.get_session(session_id)
        if not session:
            return f"❌ Session not found: {session_id}"
        
        lines = [
            f"Session: {session.name}",
            f"ID: {session.session_id}",
            f"Task: {session.task}",
            f"Status: {session.status}",
            f"Created: {session.created_at}",
            f"Collaborators ({len(session.collaborators)}):",
        ]
        
        for c in session.collaborators:
            if isinstance(c, CollaboratorInfo):
                lines.append(f"  - {c.name} ({c.role})")
            else:
                lines.append(f"  - {c.get('name', 'Unknown')} ({c.get('role', 'contributor')})")
        
        return "\n".join(lines)


def add_collaboration_commands(subparsers):
    """Add collaboration commands to CLI."""
    collab_parser = subparsers.add_parser("collab", help="Collaboration commands")
    collab_subparsers = collab_parser.add_subparsers(dest="collab_action")
    
    # Create session
    create_parser = collab_subparsers.add_parser("create", help="Create a session")
    create_parser.add_argument("name", help="Session name")
    create_parser.add_argument("--task", required=True, help="Task description")
    
    # Join session
    join_parser = collab_subparsers.add_parser("join", help="Join a session")
    join_parser.add_argument("session_id", help="Session ID")
    
    # Leave session
    leave_parser = collab_subparsers.add_parser("leave", help="Leave current session")
    
    # List sessions
    list_parser = collab_subparsers.add_parser("list", help="List sessions")
    
    # Show session
    show_parser = collab_subparsers.add_parser("show", help="Show session details")
    show_parser.add_argument("session_id", help="Session ID")
    
    # Send message
    msg_parser = collab_subparsers.add_parser("message", help="Send a message")
    msg_parser.add_argument("content", help="Message content")
    
    return collab_parser
