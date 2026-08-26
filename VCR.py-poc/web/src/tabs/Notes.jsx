import { useEffect, useState } from 'react'
import { api } from '../api.js'

const BLANK = { id: '', title: '', body: '', todos: [] }

export default function Notes() {
  const [notes, setNotes] = useState([])
  const [draft, setDraft] = useState(BLANK)
  const [todo, setTodo] = useState('')
  const [error, setError] = useState('')

  async function load() {
    try {
      setNotes((await api('/notes/list-notes')).items)
      setError('')
    } catch (failure) {
      setError(failure.message)
    }
  }

  useEffect(() => { load() }, [])

  async function persist(note) {
    await api(note.id ? '/notes/update-note' : '/notes/create-note', note)
    await load()
  }

  async function save(event) {
    event.preventDefault()
    try {
      await persist(draft)
      setDraft(BLANK)
    } catch (failure) {
      setError(failure.message)
    }
  }

  async function remove(id) {
    try {
      await api('/notes/delete-note', { id })
      if (draft.id === id) setDraft(BLANK)
      await load()
    } catch (failure) {
      setError(failure.message)
    }
  }

  function addTodo(event) {
    event.preventDefault()
    if (!todo.trim()) return
    const next = { id: `t${Date.now()}`, text: todo.trim(), done: false }
    setDraft({ ...draft, todos: [...draft.todos, next] })
    setTodo('')
  }

  async function toggle(id) {
    const next = { ...draft, todos: draft.todos.map((t) => (t.id === id ? { ...t, done: !t.done } : t)) }
    setDraft(next)
    if (!next.id) return
    try {
      await persist(next)
    } catch (failure) {
      setError(failure.message)
    }
  }

  function dropTodo(id) {
    setDraft({ ...draft, todos: draft.todos.filter((t) => t.id !== id) })
  }

  return (
    <div className="cols">
      <div className="panel">
        <h2>Notes <span className="pill">{notes.length}</span></h2>
        {notes.length === 0 ? (
          <div className="empty">No notes on this tape</div>
        ) : (
          <ul className="stack">
            {notes.map((note) => {
              const done = note.todos.filter((t) => t.done).length
              return (
                <li key={note.id} className={note.id === draft.id ? 'on' : ''} onClick={() => setDraft({ ...BLANK, ...note })}>
                  <b>{note.title || 'Untitled'}</b>
                  <small>{note.todos.length > 0 ? `${done}/${note.todos.length} done · ` : ''}{note.body.slice(0, 60)}</small>
                </li>
              )
            })}
          </ul>
        )}
        <div className="row">
          <button className="btn" onClick={() => setDraft(BLANK)}>New note</button>
        </div>
      </div>

      <form className="panel" onSubmit={save}>
        <h2>{draft.id ? 'Edit note' : 'New note'}</h2>
        <label>Title</label>
        <input type="text" required value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
        <label>Note</label>
        <textarea value={draft.body} onChange={(e) => setDraft({ ...draft, body: e.target.value })} />

        <h3 style={{ marginTop: 18 }}>To-do</h3>
        <ul className="todos">
          {draft.todos.map((item) => (
            <li key={item.id} className={item.done ? 'done' : ''}>
              <input type="checkbox" checked={item.done} onChange={() => toggle(item.id)} />
              <label>{item.text}</label>
              <button className="btn ghost danger" type="button" onClick={() => dropTodo(item.id)}>×</button>
            </li>
          ))}
        </ul>
        <div className="row">
          <input
            type="text"
            style={{ flex: 1, minWidth: 180 }}
            placeholder="Add a to-do"
            value={todo}
            onChange={(event) => setTodo(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && addTodo(event)}
          />
          <button className="btn" type="button" onClick={addTodo}>Add</button>
        </div>

        <div className="row">
          <button className="btn primary" type="submit">{draft.id ? 'Save note' : 'Create note'}</button>
          {draft.id && <button className="btn danger" type="button" onClick={() => remove(draft.id)}>Delete</button>}
        </div>

        {error && <p className="error">{error}</p>}
      </form>
    </div>
  )
}
