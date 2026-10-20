import { useState, useEffect, useRef } from 'react'

const API = import.meta.env.VITE_API_URL || ''

const SUGGESTIONS = [
  'What is the weather in Abuja?',
  'Calculate: sqrt(144) + 25 * 2',
  'What time is it?',
  'Save a note: meeting about agent demo',
  'List my notes',
]

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Tool-calling agent ready. I can run calculator, weather, time, and notes tools. Pick a prompt below or type your own.',
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
  }, [messages, loading])

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
          content: `Backend offline — deploy the API (Render blueprint in the repo) and set VITE_API_URL.\n\n${e.message}`,
          tool_calls: [],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="brand-row">
            <div className="logo">M</div>
            <h1>MCP Tool Agent</h1>
          </div>
          <p className="tagline">
            Registry-based tool calling. OpenAI-compatible · LM Studio ready.
          </p>
        </div>
        <span className="badge">Live demo</span>
      </header>

      <div className="tools-strip">
        <span className="tools-label">Tools</span>
        {(tools.length
          ? tools.map((t) => t.name)
          : ['calculator', 'get_weather', 'get_current_time', 'save_note', 'list_notes']
        ).map((name) => (
          <span key={name} className="tool-chip">
            {name}
          </span>
        ))}
      </div>

      <div className="chat">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.content}
            {m.tool_calls?.length > 0 && (
              <div className="tools-block">
                {m.tool_calls.map((tc, j) => (
                  <div key={j} className="tool-call">
                    <div>
                      <span className="name">{tc.tool}</span>
                      {' '}
                      {JSON.stringify(tc.arguments)}
                    </div>
                    <div className="result">→ {tc.result}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="typing" aria-label="Loading">
            <span /><span /><span />
          </div>
        )}
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
          placeholder="Ask something that needs a tool…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>

      <p className="footer">
        Tools live in a central registry. The model picks which to call.
        <br />
        Built for demos · GitHub: Sammy-t3ch/mcp-tool-agent
      </p>
    </div>
  )
}
