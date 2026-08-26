import { useEffect, useState } from 'react'
import { api } from '../api.js'

const BLANK = { id: '', title: '', author: '', year: '', tags: '', notes: '' }

export default function Books() {
  const [books, setBooks] = useState([])
  const [term, setTerm] = useState('')
  const [draft, setDraft] = useState(BLANK)
  const [error, setError] = useState('')

  async function load(search) {
    try {
      const data = search
        ? await api(`/books/search-books?q=${encodeURIComponent(search)}`)
        : await api('/books/list-books')
      setBooks(data.items)
      setError('')
    } catch (failure) {
      setError(failure.message)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => load(term.trim()), 180)
    return () => clearTimeout(timer)
  }, [term])

  async function save(event) {
    event.preventDefault()
    const payload = { ...draft, year: Number(draft.year) || 0 }
    try {
      await api(draft.id ? '/books/update-book' : '/books/create-book', payload)
      setDraft(BLANK)
      load(term.trim())
    } catch (failure) {
      setError(failure.message)
    }
  }

  async function remove(id) {
    try {
      await api('/books/delete-book', { id })
      if (draft.id === id) setDraft(BLANK)
      load(term.trim())
    } catch (failure) {
      setError(failure.message)
    }
  }

  return (
    <div className="cols wide">
      <div className="panel">
        <h2>Library</h2>
        <input
          type="text"
          placeholder="Search title, author or tag"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
        />
        {books.length === 0 ? (
          <div className="empty" style={{ marginTop: 14 }}>No books on this tape</div>
        ) : (
          <table style={{ marginTop: 14 }}>
            <thead>
              <tr><th>Title</th><th>Author</th><th>Year</th><th>Tags</th><th /></tr>
            </thead>
            <tbody>
              {books.map((book) => (
                <tr key={book.id} className={book.id === draft.id ? 'on' : ''} onClick={() => setDraft({ ...BLANK, ...book })}>
                  <td>{book.title}</td>
                  <td>{book.author}</td>
                  <td>{book.year || '—'}</td>
                  <td><span className="pill">{book.tags || 'none'}</span></td>
                  <td>
                    <button className="btn ghost danger" onClick={(event) => { event.stopPropagation(); remove(book.id) }}>
                      delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {error && <p className="error">{error}</p>}
      </div>

      <form className="panel" onSubmit={save}>
        <h2>{draft.id ? 'Edit book' : 'New book'}</h2>
        <label>Title</label>
        <input type="text" required value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
        <label>Author</label>
        <input type="text" value={draft.author} onChange={(e) => setDraft({ ...draft, author: e.target.value })} />
        <label>Year</label>
        <input type="number" value={draft.year} onChange={(e) => setDraft({ ...draft, year: e.target.value })} />
        <label>Tags</label>
        <input type="text" value={draft.tags} onChange={(e) => setDraft({ ...draft, tags: e.target.value })} />
        <label>Notes</label>
        <textarea value={draft.notes} onChange={(e) => setDraft({ ...draft, notes: e.target.value })} />
        <div className="row">
          <button className="btn primary" type="submit">{draft.id ? 'Save changes' : 'Add book'}</button>
          {draft.id && <button className="btn" type="button" onClick={() => setDraft(BLANK)}>Cancel</button>}
        </div>
      </form>
    </div>
  )
}
