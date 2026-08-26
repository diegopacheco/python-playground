import { useEffect, useState } from 'react'
import { api } from '../api.js'

const HAND = { rock: '✊', paper: '✋', scissors: '✌️' }
const VERDICT = { win: 'You win', loss: 'PC wins', draw: 'Draw' }

export default function Game() {
  const [round, setRound] = useState(null)
  const [history, setHistory] = useState([])
  const [score, setScore] = useState({ win: 0, loss: 0, draw: 0 })

  async function load() {
    const data = await api('/game/list-history')
    setHistory(data.items)
    setScore(data.score)
  }

  useEffect(() => { load() }, [])

  async function play(move) {
    setRound(await api('/game/play-round', { move }))
    load()
  }

  async function clear() {
    await api('/game/clear-history', {})
    setRound(null)
    load()
  }

  return (
    <div className="cols">
      <div className="panel">
        <h2>Rock Paper Scissors</h2>
        <div className="moves">
          {Object.keys(HAND).map((move) => (
            <button key={move} className="btn" title={move} onClick={() => play(move)}>{HAND[move]}</button>
          ))}
        </div>
        <div className="verdict">
          {round ? (
            <>
              <div style={{ fontSize: 36 }}>{HAND[round.player]} vs {HAND[round.pc]}</div>
              <span className={round.outcome}>{VERDICT[round.outcome]}</span>
            </>
          ) : (
            <span style={{ color: 'var(--muted)', fontSize: 15 }}>Pick a hand — the PC move comes off a fresh tape</span>
          )}
        </div>
        <div className="scoreline" style={{ marginTop: 14 }}>
          <div className="win"><b>{score.win}</b>wins</div>
          <div className="loss"><b>{score.loss}</b>losses</div>
          <div><b>{score.draw}</b>draws</div>
        </div>
      </div>

      <div className="panel">
        <h2>Rounds <span className="pill">{history.length}</span></h2>
        {history.length === 0 ? (
          <div className="empty">No rounds played</div>
        ) : (
          <ul className="history">
            {history.map((entry) => (
              <li key={entry.id}>
                <span>{HAND[entry.player]} vs {HAND[entry.pc]}</span>
                <span className={entry.outcome === 'loss' ? 'bad' : ''}>{VERDICT[entry.outcome]}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="row">
          <button className="btn danger" onClick={clear} disabled={history.length === 0}>Clear history</button>
        </div>
      </div>
    </div>
  )
}
