import { useState, useEffect, useRef } from 'react'

const API = import.meta.env.VITE_API_URL || ''

const SUGGESTIONS = [
  'What is the weather in Abuja?',
  'Calculate: sqrt(144) + 25 * 2',
  'What time is it?',
  'Save a note titled meeting: discuss MCP agent demo',
  'List my notes',
]

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hi — I am an MCP-style tool agent. I can use calculator, weather, time, and notes tools. Try a suggestion below or type anything.',
      tool_calls: [],
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [tools, setTools] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    fetch(`${API}/api/tools`)
      .then((r) => r.json())
      .then((d) => setTools(d.tools || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text) {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: msg, tool_calls: [] }])
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Request failed')
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: data.reply, tool_calls: data.tool_calls || [] },
      ])
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: `Error: ${e.message}. Is the backend running on port 8000?`,
          tool_calls: [],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>MCP Tool Agent</h1>
        <span className="badge">Tool-calling · OpenAI-compatible · LM Studio ready</span>
      </header>

      {tools.length > 0 && (
        <div className="tools-bar">
          {tools.map((t) => (
            <span key={t.name} className="tool-chip" title={t.description}>
              {t.name}
            </span>
          ))}
        </div>
      )}

      <div className="chat">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.content}
            {m.tool_calls?.length > 0 && (
              <div className="tools">
                {m.tool_calls.map((tc, j) => (
                  <div key={j}>
                    <strong>{tc.tool}</strong>({JSON.stringify(tc.arguments)}) → {tc.result}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="msg assistant">Thinking / calling tools…</div>}
        <div ref={bottomRef} />
      </div>

      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" onClick={() => send(s)} disabled={loading}>
            {s}
          </button>
        ))}
      </div>

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything that needs a tool…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>

      <footer>
        Tools are registered in a central registry. The LLM decides which to call. Works with OpenAI, Claude, NIM, LM Studio.
      </footer>
    </div>
  )
}
