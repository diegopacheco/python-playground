import { useEffect, useState } from 'react'
import { onTape } from './api.js'
import Books from './tabs/Books.jsx'
import Calculator from './tabs/Calculator.jsx'
import Gallery from './tabs/Gallery.jsx'
import Notes from './tabs/Notes.jsx'
import Game from './tabs/Game.jsx'
import Blog from './tabs/Blog.jsx'

const TABS = [
  { id: 'books', name: 'Books', endpoint: '/books/list-books', view: Books },
  { id: 'calc', name: 'Calculator', endpoint: '/calc/compute', view: Calculator },
  { id: 'gallery', name: 'Gallery', endpoint: '/images/list-images', view: Gallery },
  { id: 'notes', name: 'Notes', endpoint: '/notes/list-notes', view: Notes },
  { id: 'game', name: 'Rock Paper Scissors', endpoint: '/game/play-round', view: Game },
  { id: 'blog', name: 'Blog', endpoint: '/blog/list-posts', view: Blog },
]

function Monitor() {
  const [tape, setTape] = useState(null)
  useEffect(() => onTape(setTape), [])

  if (!tape) return (
    <div className="monitor"><span className="dot" /><span className="idle">no cassette played yet</span></div>
  )

  return (
    <div className="monitor">
      <span className="dot" />
      <span className="label">{tape.path}</span>
      <span className="label">{tape.status}</span>
      <span className="label">played from</span>
      <span className="cassette">{tape.cassette}</span>
      <span className="label">x{tape.played}</span>
      {tape.retaped.length > 0 && <span className="retaped">retaped {tape.retaped.join(' ')}</span>}
      <span className="idle">{tape.at}</span>
    </div>
  )
}

export default function App() {
  const [active, setActive] = useState('books')
  const Current = TABS.find((tab) => tab.id === active).view

  return (
    <div className="shell">
      <header className="masthead">
        <h1><span className="reel">VCR.py</span> POC</h1>
        <p>Six features. Zero backend. Every response replayed from a YAML cassette.</p>
      </header>

      <Monitor />

      <nav className="tabs">
        {TABS.map((tab) => (
          <button key={tab.id} className={tab.id === active ? 'on' : ''} onClick={() => setActive(tab.id)}>
            {tab.name}
            <small>{tab.endpoint}</small>
          </button>
        ))}
      </nav>

      <Current />
    </div>
  )
}
