import React, { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ---------------------------------------------------------------------------
// Agent pipeline configuration — 5 agents
// ---------------------------------------------------------------------------
const AGENTS_CONFIG = [
  {
    id: 1,
    name: 'MCP Data Agent',
    icon: '📦',
    desc: 'Responses API · FastMCP server · Approved budgets, historical actuals & policy',
  },
  {
    id: 2,
    name: 'Web Search Agent',
    icon: '🔎',
    desc: 'Azure AI agent_reference · Tavily · UAE inflation, sector benchmarks & news',
  },
  {
    id: 3,
    name: 'Code Interpreter Agent',
    icon: '💻',
    desc: 'Azure AI Agent Service · Variance calculations, policy flags & trend analysis',
  },
  {
    id: 4,
    name: 'Summary Agent',
    icon: '📝',
    desc: 'Responses API · Synthesises all inputs into an executive Markdown report',
  },
  {
    id: 5,
    name: 'Outlook Mail Agent',
    icon: '📧',
    desc: 'Azure AI agent_reference · OutlookWorkIQ · Sends report to lananoor@microsoft.com',
  },
]

const INITIAL_AGENTS = AGENTS_CONFIG.map(a => ({
  ...a,
  taskStatus: 'idle',
  output: '',
}))

// ---------------------------------------------------------------------------
// Spinner
// ---------------------------------------------------------------------------
function Spinner({ size = 18 }) {
  return (
    <svg
      className="spinner-svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="12" cy="12" r="9"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray="42 14"
      />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Status icon
// ---------------------------------------------------------------------------
function StatusIcon({ status }) {
  if (status === 'running') return <Spinner size={20} />
  if (status === 'complete') return <span className="icon-tick">✓</span>
  if (status === 'error')    return <span className="icon-error">✗</span>
  return <span className="icon-idle">○</span>
}

// ---------------------------------------------------------------------------
// Agent card
// ---------------------------------------------------------------------------
function AgentCard({ agent, isLast }) {
  const { taskStatus, output } = agent
  const [expanded, setExpanded] = useState(false)

  React.useEffect(() => {
    if (output) setExpanded(true)
  }, [output])

  return (
    <div className="agent-row">
      <div className={`agent-card agent-${taskStatus}`}>
        <div className="agent-card-header" onClick={() => output && setExpanded(e => !e)}>
          <div className="agent-number">{agent.id}</div>
          <div className="agent-meta">
            <div className="agent-name">{agent.icon} {agent.name}</div>
            <div className="agent-desc">{agent.desc}</div>
          </div>
          <div className="agent-status-area">
            <StatusIcon status={taskStatus} />
            {output && (
              <span className="agent-toggle">{expanded ? '▲' : '▼'}</span>
            )}
          </div>
        </div>

        {expanded && output && (
          <div className="agent-output">
            <pre>{output.length > 800 ? output.slice(0, 800) + '\n\n… [truncated — full result in report]' : output}</pre>
          </div>
        )}
      </div>

      {!isLast && (
        <div className={`pipeline-connector ${taskStatus === 'complete' ? 'connector-lit' : ''}`}>
          <div className="connector-line" />
          <div className="connector-arrow">▼</div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Status banner
// ---------------------------------------------------------------------------
function StatusBanner({ status, error }) {
  if (status === 'idle') return null
  if (status === 'complete') {
    return (
      <div className="banner banner-complete">
        <span className="banner-tick">✓</span>
        <span>Workflow complete — report generated &amp; emailed</span>
      </div>
    )
  }
  if (status === 'error') {
    return (
      <div className="banner banner-error">
        <span>⚠ Error: {error}</span>
      </div>
    )
  }
  return (
    <div className="banner banner-running">
      <Spinner size={16} />
      <span>Workflow running…</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------
export default function App() {
  const [report, setReport]     = useState('')
  const [status, setStatus]     = useState('idle')
  const [agents, setAgents]     = useState(INITIAL_AGENTS)
  const [markdown, setMarkdown] = useState('')
  const [wordPath, setWordPath] = useState(null)
  const [mailResult, setMailResult] = useState('')
  const [error, setError]       = useState('')
  const reportRef = useRef(null)
  const readerRef = useRef(null)

  // Load sample report on mount
  React.useEffect(() => {
    fetch('/api/sample')
      .then(r => r.json())
      .then(d => setReport(d.content))
      .catch(() => setReport('# Budget Variance Report\n\n(Could not load sample)'))
  }, [])

  const updateAgent = (id, taskStatus, output) => {
    setAgents(prev =>
      prev.map(a =>
        a.id === id ? { ...a, taskStatus, output: output !== undefined ? output : a.output } : a,
      ),
    )
  }

  const reset = () => {
    if (readerRef.current) {
      try { readerRef.current.cancel() } catch {}
      readerRef.current = null
    }
    setStatus('idle')
    setAgents(INITIAL_AGENTS)
    setMarkdown('')
    setWordPath(null)
    setMailResult('')
    setError('')
  }

  const run = async () => {
    reset()
    await new Promise(r => setTimeout(r, 50))

    setStatus('running')
    setAgents(AGENTS_CONFIG.map(a => ({ ...a, taskStatus: 'idle', output: '' })))

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget_report: report }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Server returned ${res.status}: ${text}`)
      }

      const reader = res.body.getReader()
      readerRef.current = reader
      const dec = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })

        const lines = buf.split('\n')
        buf = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          let ev
          try { ev = JSON.parse(line.slice(6)) }
          catch { continue }

          switch (ev.event) {
            case 'agent_start':
              updateAgent(ev.agent, 'running')
              break
            case 'agent_complete':
              updateAgent(ev.agent, 'complete', ev.output ?? '')
              break
            case 'executor_start':
              // Word doc conversion happening — agent 4 already complete
              break
            case 'executor_complete':
              setMarkdown(ev.markdown ?? '')
              setWordPath(ev.word_doc_path || null)
              setMailResult(ev.mail_result || '')
              setTimeout(() => reportRef.current?.scrollIntoView({ behavior: 'smooth' }), 300)
              break
            case 'done':
              setStatus('complete')
              break
            case 'error':
              setError(ev.message ?? 'Unknown error')
              setStatus('error')
              break
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        setError(e.message)
        setStatus('error')
      }
    }
  }

  const downloadWord = () => window.open('/api/download', '_blank')

  const isRunning = status === 'running'
  const isDone    = status === 'complete'

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="header-logo">📊</div>
            <div>
              <div className="header-title">Budget Variance Report Workflow</div>
              <div className="header-sub">
                Azure AI Agent Service · MCP Data · Web Search · Code Interpreter · Outlook
              </div>
            </div>
          </div>
          <StatusBanner status={status} error={error} />
        </div>
      </header>

      {/* ── Body ── */}
      <div className="body-grid">

        {/* ── Left column ── */}
        <div className="col-left">

          {/* Input card */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">📄 Budget Variance Report Input</h2>
            </div>
            <textarea
              className="slip-textarea"
              value={report}
              onChange={e => setReport(e.target.value)}
              disabled={isRunning}
              placeholder="Paste your budget variance report (Markdown format)…"
              spellCheck={false}
            />
            <div className="input-footer">
              <button
                className="btn-run"
                onClick={run}
                disabled={isRunning}
              >
                {isRunning
                  ? <><Spinner size={15} /> Running…</>
                  : isDone
                    ? '↻ Run Again'
                    : '▶ Run Workflow'}
              </button>
              {status !== 'idle' && (
                <button className="btn-secondary" onClick={reset} disabled={isRunning}>
                  ✕ Reset
                </button>
              )}
            </div>
          </section>

          {/* Pipeline card */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">🤖 Agent Pipeline</h2>
              {isDone && <span className="all-done-badge">✓ All complete</span>}
            </div>
            <div className="pipeline">
              {agents.map((agent, idx) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  isLast={idx === agents.length - 1}
                />
              ))}
            </div>
          </section>

        </div>

        {/* ── Right column — Report ── */}
        <div className="col-right">
          <section className="card report-card" ref={reportRef}>
            <div className="card-header">
              <h2 className="card-title">📋 Variance Analysis Report</h2>
              {markdown && (
                <button className="btn-download" onClick={downloadWord}>
                  ↓ Download Word
                </button>
              )}
            </div>

            {mailResult && (
              <div className="mail-sent-banner">
                <span>📧</span>
                <span>Report emailed to lananoor@microsoft.com</span>
              </div>
            )}

            {!markdown && (
              <div className="report-empty">
                {isRunning
                  ? <><Spinner size={28} /><p>Generating report…</p></>
                  : <><span className="report-empty-icon">📊</span><p>Run the workflow to see the analysis report here.</p></>
                }
              </div>
            )}

            {markdown && (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {markdown}
                </ReactMarkdown>
              </div>
            )}

            {markdown && wordPath && (
              <div className="report-footer">
                <button className="btn-download-full" onClick={downloadWord}>
                  ↓ Download Word Document
                </button>
                <span className="word-path">{wordPath.split(/[/\\]/).pop()}</span>
              </div>
            )}
          </section>
        </div>

      </div>
    </div>
  )
}
