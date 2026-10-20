"""
MCP Tool Agent — FastAPI backend
Exposes /api/chat and /api/tools for the demo UI.
"""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.tools.registry import ToolRegistry
from app.tools.builtin import register_builtin_tools
from app.services.agent import AgentService

load_dotenv()

app = FastAPI(
    title="MCP Tool Agent",
    description="Demo agent that uses tools via an MCP-inspired registry. Works with OpenAI, Claude, LM Studio, NVIDIA NIM, etc.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = ToolRegistry()
register_builtin_tools(registry)
agent = AgentService(registry)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[Dict[str, Any]]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "tools": [t.name for t in registry.list_tools()],
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
    }


@app.get("/api/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": [p.model_dump() for p in t.parameters],
            }
            for t in registry.list_tools()
        ]
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not os.getenv("LLM_API_KEY") and not os.getenv("LLM_BASE_URL"):
        return _demo_fallback(req.message)
    try:
        result = agent.run(req.message, req.history)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _demo_fallback(message: str) -> ChatResponse:
    lower = message.lower()
    tool_calls = []
    if any(x in lower for x in ["calculate", "math", "+", "*", "sqrt"]):
        expr = message.split(":")[-1].strip() if ":" in message else "2+2"
        result = registry.execute("calculator", {"expression": expr})
        tool_calls.append({"tool": "calculator", "arguments": {"expression": expr}, "result": result})
        reply = f"(Demo mode — no LLM key) Tool result: {result}"
    elif "weather" in lower or "temperature" in lower:
        city = "Abuja"
        for c in ["Lagos", "Abuja", "London", "New York", "Port Harcourt"]:
            if c.lower() in lower:
                city = c
                break
        result = registry.execute("get_weather", {"city": city})
        tool_calls.append({"tool": "get_weather", "arguments": {"city": city}, "result": result})
        reply = f"(Demo mode) {result}"
    elif "time" in lower:
        result = registry.execute("get_current_time", {})
        tool_calls.append({"tool": "get_current_time", "arguments": {}, "result": result})
        reply = f"(Demo mode) {result}"
    elif "note" in lower and ("save" in lower or "write" in lower):
        result = registry.execute("save_note", {"title": "demo", "content": message})
        tool_calls.append({"tool": "save_note", "arguments": {"title": "demo", "content": message}, "result": result})
        reply = f"(Demo mode) {result}"
    elif "list notes" in lower or "show notes" in lower:
        result = registry.execute("list_notes", {})
        tool_calls.append({"tool": "list_notes", "arguments": {}, "result": result})
        reply = f"(Demo mode) {result}"
    else:
        reply = (
            "Demo mode (no LLM_API_KEY set). Try:\n"
            "• 'What is the weather in Abuja?'\n"
            "• 'Calculate: sqrt(144) + 10'\n"
            "• 'What time is it?'\n"
            "• 'Save a note titled meeting: discuss agent demo'\n"
            "Set LLM_API_KEY + optional LLM_BASE_URL / LLM_MODEL for full agent behaviour."
        )
    return ChatResponse(reply=reply, tool_calls=tool_calls)


@app.get("/")
def root():
    return {"message": "MCP Tool Agent API", "docs": "/docs", "health": "/api/health"}
