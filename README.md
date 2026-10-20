# MCP Tool Agent

**AI agent that uses tools via an MCP-inspired registry.**

The agent receives a user message, decides which tool(s) to call, executes them, and returns a natural-language answer. Works with any OpenAI-compatible endpoint (OpenAI, Claude proxies, Google AI Studio, NVIDIA NIM, **LM Studio** local models, etc.).

---

## Why this project exists

Demonstrates:

- Tool/function calling architecture (MCP-style registry)
- Clean separation: tools are registered once, agent discovers them at runtime
- Multi-provider LLM support (cloud + local via LM Studio)
- Demo mode that still shows tool execution even without an API key

Perfect for showing employers you can build **agents that connect apps and tools to LLMs**.

---

## Tools included

| Tool | Purpose |
|------|---------|
| `calculator` | Safe math evaluation |
| `get_current_time` | UTC time |
| `get_weather` | Mock weather by city |
| `save_note` / `list_notes` / `get_note` | Simple in-memory notes |

Easy to add more tools — just register them in `app/tools/builtin.py`.

---

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set LLM_API_KEY (optional for demo mode)
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  

### Frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | For full agent | API key for the LLM provider |
| `LLM_BASE_URL` | No | Base URL (e.g. `http://localhost:1234/v1` for LM Studio) |
| `LLM_MODEL` | No | Model name (default `gpt-4o-mini`) |

Without `LLM_API_KEY` the server runs in **demo mode** and still executes tools via simple pattern matching so reviewers can see the tool system working.

---

## Architecture

```
User message
    ↓
AgentService (OpenAI-compatible client)
    ↓
Tool decision (LLM function-calling)
    ↓
ToolRegistry.execute(name, args)
    ↓
Tool result → second LLM pass → final reply
```

Tools are registered with name, description, and JSON-schema parameters. The same schema is sent to any OpenAI-compatible model.

---

## Example requests

```bash
# List tools
curl http://localhost:8000/api/tools

# Chat (demo mode works without key)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Abuja?"}'
```

---

## Adding a new tool

1. Write an execute function in `app/tools/builtin.py`
2. Register it with `registry.register(Tool(...))`
3. Restart the server — the agent will see it automatically

---

## License

MIT
