"""Self-contained Vercel serverless FastAPI app for MCP Tool Agent."""
from __future__ import annotations

import math
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="MCP Tool Agent", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_NOTES: dict[str, str] = {}
_MAX_RESULT_LEN = 500
_MAX_EXPONENT = 20


def _calculator(expression: str) -> str:
    allowed = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sqrt": math.sqrt, "pow": math.pow, "sin": math.sin,
        "cos": math.cos, "tan": math.tan, "pi": math.pi, "e": math.e,
    }
    if "**" in expression:
        m = re.search(r"\*\*\s*(\d+)", expression)
        if m and int(m.group(1)) > _MAX_EXPONENT:
            return (
                f"Error evaluating '{expression}': "
                f"exponent too large (max {_MAX_EXPONENT} for demo safety)"
            )
    compact = expression.replace(" ", "")
    if "pow(" in compact:
        m2 = re.search(r"pow\([^,]+,(\d+)", compact)
        if m2 and int(m2.group(1)) > _MAX_EXPONENT:
            return (
                f"Error evaluating '{expression}': "
                f"exponent too large (max {_MAX_EXPONENT} for demo safety)"
            )
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        out = f"{expression} = {result}"
        if len(out) > _MAX_RESULT_LEN:
            s = str(result)
            return (
                f"{expression} = {s[:200]}… "
                f"(result truncated, {len(s)} digits)"
            )
        return out
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


def _get_time() -> str:
    now = datetime.now(timezone.utc)
    return f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"


def _save_note(title: str, content: str) -> str:
    _NOTES[title] = content
    return f"Note '{title}' saved. Total notes: {len(_NOTES)}"


def _list_notes() -> str:
    if not _NOTES:
        return "No notes saved yet."
    lines = [f"- {t}: {c[:80]}" for t, c in _NOTES.items()]
    return "Saved notes:\n" + "\n".join(lines)


def _weather(city: str) -> str:
    city_clean = city.strip().title()
    samples = {
        "Lagos": "Lagos: 31°C, Partly cloudy, humidity 78%",
        "Abuja": "Abuja: 34°C, Sunny, humidity 45%",
        "Port Harcourt": "Port Harcourt: 29°C, Light rain, humidity 85%",
        "London": "London: 12°C, Overcast, humidity 70%",
        "New York": "New York: 18°C, Clear, humidity 55%",
    }
    return samples.get(city_clean, f"{city_clean}: 25°C, Clear skies (mock data)")


def _extract_city(message: str) -> str:
    lower = message.lower()
    for c in ["Port Harcourt", "New York", "Lagos", "Abuja", "London"]:
        if c.lower() in lower:
            return c
    m = re.search(
        r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-]{1,40}?)(?:\?|$|,|\.)",
        message,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return "Abuja"


TOOLS_META = [
    {"name": "calculator", "description": "Evaluate a math expression", "parameters": [{"name": "expression", "type": "string", "description": "e.g. sqrt(144)+10", "required": True}]},
    {"name": "get_current_time", "description": "Get current UTC time", "parameters": []},
    {"name": "get_weather", "description": "Weather for a city (mock)", "parameters": [{"name": "city", "type": "string", "description": "City name", "required": True}]},
    {"name": "save_note", "description": "Save a note", "parameters": [{"name": "title", "type": "string", "required": True}, {"name": "content", "type": "string", "required": True}]},
    {"name": "list_notes", "description": "List saved notes", "parameters": []},
]


def execute_tool(name: str, arguments: dict) -> str:
    if name == "calculator":
        return _calculator(arguments.get("expression", "2+2"))
    if name == "get_current_time":
        return _get_time()
    if name == "get_weather":
        return _weather(arguments.get("city", "Abuja"))
    if name == "save_note":
        return _save_note(arguments.get("title", "note"), arguments.get("content", ""))
    if name == "list_notes":
        return _list_notes()
    return f"Unknown tool: {name}"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[Dict[str, Any]]


@app.get("/")
def root():
    return {"message": "MCP Tool Agent API", "health": "/api/health", "docs": "/docs"}


@app.get("/api/health")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "tools": [t["name"] for t in TOOLS_META],
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
    }


@app.get("/api/tools")
@app.get("/tools")
def list_tools():
    return {"tools": TOOLS_META}


def _demo_chat(message: str) -> ChatResponse:
    lower = message.lower()
    tool_calls: List[Dict[str, Any]] = []

    if any(x in lower for x in ["calculate", "math", "sqrt"]) and "weather" not in lower:
        expr = message.split(":")[-1].strip() if ":" in message else "2+2"
        for prefix in ["calculate", "Calculate"]:
            expr = expr.replace(prefix, "").strip()
        result = execute_tool("calculator", {"expression": expr})
        tool_calls.append({"tool": "calculator", "arguments": {"expression": expr}, "result": result})
        return ChatResponse(reply=f"Tool result: {result}", tool_calls=tool_calls)

    if "weather" in lower or "temperature" in lower:
        city = _extract_city(message)
        result = execute_tool("get_weather", {"city": city})
        tool_calls.append({"tool": "get_weather", "arguments": {"city": city}, "result": result})
        return ChatResponse(reply=result, tool_calls=tool_calls)

    if "time" in lower:
        result = execute_tool("get_current_time", {})
        tool_calls.append({"tool": "get_current_time", "arguments": {}, "result": result})
        return ChatResponse(reply=result, tool_calls=tool_calls)

    if "note" in lower and ("save" in lower or "write" in lower or "meeting" in lower):
        result = execute_tool("save_note", {"title": "demo", "content": message})
        tool_calls.append({"tool": "save_note", "arguments": {"title": "demo", "content": message}, "result": result})
        return ChatResponse(reply=result, tool_calls=tool_calls)

    if "list" in lower and "note" in lower:
        result = execute_tool("list_notes", {})
        tool_calls.append({"tool": "list_notes", "arguments": {}, "result": result})
        return ChatResponse(reply=result, tool_calls=tool_calls)

    return ChatResponse(
        reply=(
            "Demo mode active. Try:\n"
            "• What is the weather in Abuja?\n"
            "• Calculate: sqrt(144) + 10\n"
            "• What time is it?\n"
            "• Save a note: meeting about agent demo\n"
            "• List my notes"
        ),
        tool_calls=[],
    )


@app.post("/api/chat")
@app.post("/chat")
def chat(req: ChatRequest):
    if os.getenv("LLM_API_KEY"):
        try:
            return _llm_chat(req.message)
        except Exception as e:
            demo = _demo_chat(req.message)
            demo.reply = f"(LLM error: {e}) " + demo.reply
            return demo
    return _demo_chat(req.message)


def _llm_chat(message: str) -> ChatResponse:
    import json
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL") or None)
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    openai_tools = []
    for t in TOOLS_META:
        props = {}
        required = []
        for p in t["parameters"]:
            props[p["name"]] = {"type": p.get("type", "string"), "description": p.get("description", "")}
            if p.get("required", True):
                required.append(p["name"])
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {"type": "object", "properties": props, "required": required},
            },
        })

    messages = [
        {"role": "system", "content": "You are a helpful agent with tools. Use tools when useful. Be concise."},
        {"role": "user", "content": message},
    ]

    response = client.chat.completions.create(model=model, messages=messages, tools=openai_tools, tool_choice="auto")
    msg = response.choices[0].message
    tool_calls_log = []

    if msg.tool_calls:
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = execute_tool(name, args)
            tool_calls_log.append({"tool": name, "arguments": args, "result": result})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        response = client.chat.completions.create(model=model, messages=messages)
        final = response.choices[0].message.content or ""
    else:
        final = msg.content or ""

    return ChatResponse(reply=final, tool_calls=tool_calls_log)
