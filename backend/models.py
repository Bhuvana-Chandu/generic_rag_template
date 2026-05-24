"""
Pydantic request/response models for the AI Copilot API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ── Request Models ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier (UUID)")
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    image_base64: Optional[str] = Field(None, description="Optional base64 encoded image for vision processing")

class ClearSessionRequest(BaseModel):
    session_id: str

# ── Response Models ────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str           # "human" or "ai"
    content: str
    timestamp: Optional[str] = None

class MemoryContext(BaseModel):
    property_type: Optional[str] = None
    property_size: Optional[str] = None
    damage_type: Optional[str] = None
    peril_category: Optional[str] = None
    policy_tier: Optional[str] = None
    claim_id: Optional[str] = None
    postcode: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    intent: str
    steps_log: List[str]
    memory: MemoryContext
    timestamp: str

class SessionHistoryResponse(BaseModel):
    session_id: str
    history: List[ChatMessage]
    message_count: int
    memory: Optional[Dict[str, Any]] = None

class ComponentHealth(BaseModel):
    status: str         # "ok" | "error" | "not_checked"
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str         # "healthy" | "degraded" | "unhealthy"
    timestamp: str
    version: str = "1.0.0"
    components: dict
    active_sessions: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    session_id: Optional[str] = None

# ── Workflow / Trace Models ──────────────────────────────────────────────────

class WorkflowStep(BaseModel):
    step_id: str
    name: str
    description: str
    status: str = "completed"
    output_summary: Optional[str] = None

class WorkflowTraceResponse(BaseModel):
    session_id: str
    query: str
    intent: str
    steps: List[WorkflowStep]
    full_trace: List[str]
    retrieved_context_preview: str

class WorkflowDiagramResponse(BaseModel):
    session_id: str
    query: str
    intent: str
    diagram: str
    steps_log: List[str] | None = None
