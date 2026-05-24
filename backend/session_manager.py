import json
import os
import sys
from typing import List, Tuple
from dotenv import load_dotenv

import redis

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.orchestrator import Orchestrator
from backend.models import MemoryContext

load_dotenv()

class SessionManager:
    """
    Manages session persistence using Redis for chat history.
    The orchestrator itself is kept stateless here.
    """
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            print("WARNING: Could not connect to Redis. Ensure it is running at", redis_url)
            self.redis_client = None

    def get_chat_history(self, session_id: str) -> List[Tuple[str, str]]:
        """Fetch chat history from Redis."""
        if not self.redis_client:
            return []
        
        history_key = f"session:{session_id}:history"
        raw_history = self.redis_client.get(history_key)
        if raw_history:
            return json.loads(raw_history)
        return []

    def save_chat_history(self, session_id: str, history: List[Tuple[str, str]]):
        """Save chat history to Redis with a TTL of 24 hours."""
        if not self.redis_client:
            return
            
        history_key = f"session:{session_id}:history"
        self.redis_client.setex(history_key, 86400, json.dumps(history)) # 24 hour TTL
        
        # Save metadata if it doesn't exist
        meta_key = f"session:{session_id}:meta"
        raw_meta = self.redis_client.get(meta_key)
        if not raw_meta:
            import datetime
            meta = {
                "session_id": session_id,
                "created_at": datetime.datetime.now().isoformat(),
                "preview": history[0][1][:40] + "..." if history else "New Session"
            }
            self.redis_client.setex(meta_key, 86400, json.dumps(meta))
        else:
            # Update preview if needed
            if history:
                meta = json.loads(raw_meta)
                if meta.get("preview") == "New Session":
                    meta["preview"] = history[0][1][:40] + "..."
                    self.redis_client.setex(meta_key, 86400, json.dumps(meta))

    def get_orchestrator(self, session_id: str) -> Orchestrator:
        """Returns a stateless Orchestrator hydrated with Redis chat history."""
        chat_history = self.get_chat_history(session_id)
        orch = Orchestrator(session_id=session_id)
        orch.chat_history = chat_history
        
        # Load structured memory if it exists
        if self.redis_client:
            raw_mem = self.redis_client.get(f"session:{session_id}:memory")
            if raw_mem:
                try:
                    orch.memory = MemoryContext.parse_raw(raw_mem)
                except Exception:
                    pass
        return orch

    def save_orchestrator_state(self, session_id: str, orch: Orchestrator):
        """Save the updated chat history and memory back to Redis."""
        self.save_chat_history(session_id, orch.chat_history)
        if self.redis_client:
            self.redis_client.setex(f"session:{session_id}:memory", 86400, orch.memory.json())

    def clear_session(self, session_id: str):
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}:history")
            self.redis_client.delete(f"session:{session_id}:meta")
            self.redis_client.delete(f"session:{session_id}:memory")

    def get_all_sessions(self) -> List[dict]:
        """Fetch all session metadata from Redis."""
        if not self.redis_client:
            return []
        
        keys = self.redis_client.keys("session:*:meta")
        sessions = []
        for key in keys:
            raw = self.redis_client.get(key)
            if raw:
                try:
                    data = json.loads(raw)
                    sessions.append(data)
                except:
                    pass
        # Sort by newest first
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def get_active_session_count(self) -> int:
        if self.redis_client:
            return len(self.redis_client.keys("session:*:history"))
        return 0

# Global singleton
manager = SessionManager()
