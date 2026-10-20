"""
MCP-inspired tool registry.
Each tool has a name, description, JSON schema for parameters, and an execute function.
The agent (LLM) sees the tool list and decides which one to call.
"""

from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True


class Tool(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]
    execute: Callable[..., Any] = Field(exclude=True)

    def to_openai_schema(self) -> dict:
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {"type": p.type, "description": p.description}
            if p.required:
                required.append(p.name)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def openai_tools(self) -> List[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def execute(self, name: str, arguments: dict) -> Any:
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool.execute(**arguments)
