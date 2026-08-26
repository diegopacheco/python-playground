import { useEffect, useState } from 'react'
import { api } from '../api.js'

const KEYS = ['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', '(', '+', ')', '%', '**', 'C']

export default function Calculator() {
  const [expression, setExpression] = useState('')
  const [last, setLast] = useState(null)
  const [history, setHistory] = useState([])

  async function loadHistory() {
    setHistory((await api('/calc/list-history')).items)
  }

  useEffect(() => { loadHistory() }, [])

  async function compute() {
    if (!expression.trim()) return
    const entry = await api('/calc/compute', { expression })
    setLast(entry)
    setExpression('')
    loadHistory()
  }

  async function clearHistory() {
    await api('/calc/clear-history', {})
    setLast(null)
    loadHistory()
  }

  function press(key) {
    if (key === 'C') return setExpression('')
    setExpression(expression + key)
  }

  return (
    <div className="cols">
      <div className="panel">
        <h2>Calculator</h2>
        <div className="readout">
          <div className="expr">{expression || (last ? last.expression : ' ')}</div>
          <div className="val">{last ? (last.ok ? last.result : 'error') : '0'}</div>
        </div>
        <input
          type="text"
          style={{ marginTop: 12 }}
          value={expression}
          placeholder="2 + 3 * 4"
          onChange={(event) => setExpression(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && compute()}
        />
        <div className="keypad">
          {KEYS.map((key) => (
            <button key={key} className={key === 'C' ? 'btn danger' : 'btn'} onClick={() => press(key)}>{key}</button>
          ))}
        </div>
        <div className="row">
          <button className="btn primary" onClick={compute}>Compute</button>
        </div>
      </div>

      <div className="panel">
        <h2>History <span className="pill">{history.length}</span></h2>
        {history.length === 0 ? (
          <div className="empty">Nothing computed yet</div>
        ) : (
          <ul className="history">
            {history.map((entry) => (
              <li key={entry.id}>
                <span>{entry.expression}</span>
                <span className={entry.ok ? '' : 'bad'}>{entry.ok ? entry.result : 'invalid'}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="row">
          <button className="btn danger" onClick={clearHistory} disabled={history.length === 0}>Clear history</button>
        </div>
      </div>
    </div>
  )
}
