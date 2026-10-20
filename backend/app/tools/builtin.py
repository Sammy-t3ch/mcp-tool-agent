"""
Built-in tools for the MCP Tool Agent demo.
"""

import math
import operator
from datetime import datetime, timezone
from typing import Any

from .registry import Tool, ToolParameter, ToolRegistry

_NOTES: dict[str, str] = {}


def _calculator(expression: str) -> str:
    allowed = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sqrt": math.sqrt, "pow": math.pow, "sin": math.sin,
        "cos": math.cos, "tan": math.tan, "pi": math.pi, "e": math.e,
        "+": operator.add, "-": operator.sub, "*": operator.mul,
        "/": operator.truediv, "**": operator.pow, "%": operator.mod,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


def _get_time(timezone_name: str = "UTC") -> str:
    now = datetime.now(timezone.utc)
    return f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"


def _save_note(title: str, content: str) -> str:
    _NOTES[title] = content
    return f"Note '{title}' saved successfully. Total notes: {len(_NOTES)}"


def _list_notes() -> str:
    if not _NOTES:
        return "No notes saved yet."
    lines = [f"- {title}: {content[:80]}{'...' if len(content) > 80 else ''}" for title, content in _NOTES.items()]
    return "Saved notes:\n" + "\n".join(lines)


def _get_note(title: str) -> str:
    if title not in _NOTES:
        return f"No note found with title '{title}'."
    return f"Note '{title}':\n{_NOTES[title]}"


def _weather_mock(city: str) -> str:
    city_clean = city.strip().title()
    samples = {
        "Lagos": "Lagos: 31°C, Partly cloudy, humidity 78%",
        "Abuja": "Abuja: 34°C, Sunny, humidity 45%",
        "Port Harcourt": "Port Harcourt: 29°C, Light rain, humidity 85%",
        "London": "London: 12°C, Overcast, humidity 70%",
        "New York": "New York: 18°C, Clear, humidity 55%",
    }
    return samples.get(city_clean, f"{city_clean}: 25°C, Clear skies (mock data for demo)")


def register_builtin_tools(registry: ToolRegistry) -> None:
    registry.register(Tool(
        name="calculator",
        description="Evaluate a mathematical expression. Supports +, -, *, /, **, sqrt, sin, cos, etc.",
        parameters=[
            ToolParameter(name="expression", type="string", description="The math expression to evaluate, e.g. '2 + 2 * 3' or 'sqrt(16)'"),
        ],
        execute=_calculator,
    ))
    registry.register(Tool(
        name="get_current_time",
        description="Get the current UTC date and time.",
        parameters=[],
        execute=_get_time,
    ))
    registry.register(Tool(
        name="save_note",
        description="Save a short note with a title for later retrieval.",
        parameters=[
            ToolParameter(name="title", type="string", description="Short title for the note"),
            ToolParameter(name="content", type="string", description="The note content"),
        ],
        execute=_save_note,
    ))
    registry.register(Tool(
        name="list_notes",
        description="List all previously saved notes.",
        parameters=[],
        execute=_list_notes,
    ))
    registry.register(Tool(
        name="get_note",
        description="Retrieve a previously saved note by its title.",
        parameters=[
            ToolParameter(name="title", type="string", description="Title of the note to retrieve"),
        ],
        execute=_get_note,
    ))
    registry.register(Tool(
        name="get_weather",
        description="Get current weather for a city (demo uses mock data).",
        parameters=[
            ToolParameter(name="city", type="string", description="City name, e.g. Lagos, Abuja, London"),
        ],
        execute=_weather_mock,
    ))
