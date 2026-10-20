"""
Core agent loop: send messages + tools to an OpenAI-compatible LLM,
execute any tool calls, and return the final answer.
"""

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.tools.registry import ToolRegistry


class AgentService:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY", "not-needed"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def run(self, user_message: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI agent with access to tools. "
                    "Use tools when they help answer the user accurately. "
                    "After receiving tool results, give a clear natural-language answer. "
                    "Be concise and practical."
                ),
            }
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tools = self.registry.openai_tools()
        tool_calls_log = []

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                try:
                    result = self.registry.execute(name, args)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Tool error: {e}"

                tool_calls_log.append({"tool": name, "arguments": args, "result": result_str})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            final = response.choices[0].message.content or ""
        else:
            final = msg.content or ""

        return {
            "reply": final,
            "tool_calls": tool_calls_log,
        }
