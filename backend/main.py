import os
import sys
import time
import json
import asyncio
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import subprocess
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse as StarletteStreamingResponse

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import (
    ChatRequest, ChatResponse, HealthResponse, 
    SessionHistoryResponse, ChatMessage, ErrorResponse,
    WorkflowTraceResponse, WorkflowStep,
    WorkflowDiagramResponse
)

from backend.session_manager import manager
from fastapi.responses import StreamingResponse
import io
from graphviz import Digraph

# Setup logging
logger.add("logs/backend.log", rotation="500 MB", level="INFO")

app = FastAPI(
    title="Property Insurance AI Copilot API",
    description="Backend API for the RAG-based Assistant with Persistent Memory",
    version="1.0.0"
)

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Proxy Middleware for Single-Port Deployment ──
class StreamlitProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if (request.url.path.startswith("/chat") or 
            request.url.path.startswith("/session") or 
            request.url.path.startswith("/health") or 
            request.url.path.startswith("/dev-console") or
            request.url.path.startswith("/static")):
            return await call_next(request)
        
        target_url = f"http://localhost:8501{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
            
        async with httpx.AsyncClient() as client:
            try:
                proxy_req = client.build_request(
                    request.method,
                    target_url,
                    headers=request.headers.raw,
                    content=await request.body()
                )
                proxy_res = await client.send(proxy_req, stream=True)
                return StarletteStreamingResponse(
                    proxy_res.aiter_raw(),
                    status_code=proxy_res.status_code,
                    headers=proxy_res.headers
                )
            except Exception as e:
                logger.error(f"Proxy error: {str(e)}")
                return await call_next(request)

app.add_middleware(StreamlitProxyMiddleware)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing pipeline on startup...")
    logger.info("Starting Streamlit frontend sidecar...")
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py", 
        "--server.port", "8501", 
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ])
    logger.info("Backend and Frontend sidecar are fully ready.")

_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")

@app.get("/dev-console")
async def dev_console():
    html_path = os.path.join(_frontend_dir, "dev_console.html")
    return FileResponse(html_path, media_type="text/html")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    components = {
        "openai_api": "ok" if os.getenv("OPENAI_API_KEY") else "error",
        "vector_store": "ok", 
        "knowledge_graph": "ok"
    }
    status = "healthy" if not any(v == "error" for v in components.values()) else "degraded"
    return HealthResponse(
        status=status,
        timestamp=datetime.now().isoformat(),
        components=components,
        active_sessions=manager.get_active_session_count()
    )

@app.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def chat(request: ChatRequest):
    try:
        orch = manager.get_orchestrator(request.session_id)
        start_time = time.time()
        result = orch.ask_detailed(request.query, image_base64=request.image_base64)
        manager.save_orchestrator_state(request.session_id, orch)
        duration = time.time() - start_time
        
        return ChatResponse(
            session_id=request.session_id,
            query=request.query,
            answer=result["answer"],
            intent=result["intent"],
            steps_log=result["steps_log"],
            memory=result["memory"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=ErrorResponse(error="Internal Server Error", detail=str(e), session_id=request.session_id).dict()
        )

@app.get("/chat/stream")
async def chat_stream(session_id: str, query: str):
    orch = manager.get_orchestrator(session_id)

    async def event_generator():
        def emit(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        yield emit({"type": "node_start", "node": "user", "msg": query})
        await asyncio.sleep(0.1)

        prev_steps: list[str] = []
        final_answer = ""
        last_intent  = ""

        try:
            for event in orch.stream_detailed(query):
                node  = event["node"]
                state = event["state"]
                current_steps = state.get("steps_log", [])
                new_steps     = current_steps[len(prev_steps):]
                intent        = state.get("intent", last_intent)
                last_intent   = intent

                yield emit({"type": "node_start", "node": node, "intent": intent, "msg": f"Node '{node}' executing…"})
                await asyncio.sleep(0.1)

                for step in new_steps:
                    yield emit({"type": "substep", "node": node, "intent": intent, "step": step, "all_steps": current_steps})
                    await asyncio.sleep(0.1)

                final_answer = state.get("answer", "")
                
                # Send the updated memory state
                memory_dict = orch.memory.dict() if hasattr(orch.memory, 'dict') else {}
                
                yield emit({
                    "type":   "node_done",
                    "node":   node,
                    "intent": intent,
                    "steps":  current_steps,
                    "answer": final_answer,
                    "memory": memory_dict
                })

                if node == "guardrail_check":
                    if len(orch.chat_history) == 0 or orch.chat_history[-1] != ("ai", final_answer):
                        orch.chat_history.append(("human", query))
                        orch.chat_history.append(("ai",    final_answer))
                    orch.last_detailed_result = {
                        "query":             query,
                        "answer":            final_answer,
                        "intent":            intent,
                        "steps_log":         current_steps,
                        "retrieved_context": state.get("retrieved_context", ""),
                        "memory":            orch.memory
                    }
                    manager.save_orchestrator_state(session_id, orch)

                prev_steps = current_steps
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in chat_stream: {str(e)}")
            yield emit({"type": "error", "msg": f"Backend Error: {str(e)}"})

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/sessions")
async def get_all_sessions():
    try:
        return {"sessions": manager.get_all_sessions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_history(session_id: str):
    try:
        orch = manager.get_orchestrator(session_id)
        history = []
        for role, content in orch.chat_history:
            history.append(ChatMessage(role=role, content=content))
        
        memory_dict = orch.memory.dict() if hasattr(orch.memory, 'dict') else {}
        return SessionHistoryResponse(
            session_id=session_id, history=history, message_count=len(history), memory=memory_dict
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    manager.clear_session(session_id)
    return {"status": "success", "message": f"Session {session_id} cleared"}

def _steps_to_mermaid(query: str, intent: str, steps: list[str]) -> str:
    lines = ["graph LR"]
    lines.append('    A[Memory Extraction] --> B[Intent Classification]')
    lines.append('    B --> C[Tool Dispatch]')
    lines.append('    C --> D[Synthesis Agent]')
    lines.append('    D --> E[Guardrail Check]')
    return "\\n".join(lines)

@app.get("/session/{session_id}/diagram", response_model=WorkflowDiagramResponse)
async def get_diagram(session_id: str):
    try:
        orch = manager.get_orchestrator(session_id)
        result = orch.last_detailed_result
        if not result:
            raise HTTPException(status_code=404, detail="No trace found.")
        diagram = _steps_to_mermaid(
            query=result.get("query", ""),
            intent=result.get("intent", ""),
            steps=result.get("steps_log", []),
        )
        return WorkflowDiagramResponse(
            session_id=session_id, query=result.get("query", ""), intent=result.get("intent", ""),
            diagram=diagram, steps_log=result.get("steps_log", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/session/{session_id}/trace", response_model=WorkflowTraceResponse)
async def get_trace(session_id: str):
    try:
        orch = manager.get_orchestrator(session_id)
        if not orch.last_detailed_result:
            raise HTTPException(status_code=404, detail="No trace found.")
            
        res = orch.last_detailed_result
        steps = [WorkflowStep(step_id=f"step_{i+1}", name="Step", description=s) for i, s in enumerate(res["steps_log"])]
            
        return WorkflowTraceResponse(
            session_id=session_id, query=res["query"], intent=res["intent"],
            steps=steps, full_trace=res["steps_log"],
            retrieved_context_preview=res["retrieved_context"][:500] + "..." if len(res["retrieved_context"]) > 500 else res["retrieved_context"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
