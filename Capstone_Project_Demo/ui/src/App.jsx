import { useMemo, useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState('What controls does the policy require for sanctions screening alerts?')
  const [topK, setTopK] = useState(6)
  const [answer, setAnswer] = useState('')
  const [confidence, setConfidence] = useState('')
  const [citations, setCitations] = useState([])
  const [latency, setLatency] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const apiBase = useMemo(() => {
    return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  }, [])

  async function handleAsk(event) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${apiBase}/api/v1/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: Number(topK) }),
      })

      if (!response.ok) {
        const message = await response.text()
        throw new Error(message || `Request failed with ${response.status}`)
      }

      const data = await response.json()
      setAnswer(data.answer || '')
      setConfidence(data.confidence || '')
      setCitations(data.citations || [])
      setLatency(data.latency_ms ?? null)
    } catch (err) {
      setError(err.message || 'Failed to query API')
      setAnswer('')
      setConfidence('')
      setCitations([])
      setLatency(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="header">
        <p className="eyebrow">Compliance Knowledge Agent</p>
        <h1>Policy Q&A Console</h1>
        <p className="sub">
          AI-Recommend / Human-Approve. Ask a compliance question and review citation-grounded output.
        </p>
      </header>

      <section className="panel">
        <form onSubmit={handleAsk} className="query-form">
          <label htmlFor="question">Question</label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={5}
            required
            minLength={5}
            placeholder="Ask about AML, KYC, data privacy, operational risk, etc."
          />

          <div className="controls">
            <label htmlFor="topk">Top K</label>
            <input
              id="topk"
              type="number"
              value={topK}
              min={1}
              max={20}
              onChange={(e) => setTopK(e.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Querying...' : 'Ask Agent'}
            </button>
          </div>
        </form>

        <div className="meta-row">
          <span>API: {apiBase}</span>
          {latency !== null && <span>Latency: {latency} ms</span>}
          {confidence && <span>Confidence: {confidence}</span>}
        </div>

        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}

        <div className="answer-box">
          <h2>Answer</h2>
          <p>{answer || 'Submit a question to see the response.'}</p>
        </div>

        <div className="citations-box">
          <h2>Citations</h2>
          {citations.length === 0 ? (
            <p>No citations yet.</p>
          ) : (
            <ul>
              {citations.map((item, idx) => (
                <li key={`${item}-${idx}`}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <footer className="footer">
        Review required before operational use.
      </footer>
    </main>
  )
}

export default App
