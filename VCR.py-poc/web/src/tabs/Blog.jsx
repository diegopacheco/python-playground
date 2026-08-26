import { useEffect, useState } from 'react'
import { api } from '../api.js'

const BLANK = { id: '', title: '', body: '', image: '', youtube: '' }

function youtubeId(value) {
  const raw = (value || '').trim()
  if (!raw) return ''
  const match = raw.match(/(?:v=|youtu\.be\/|embed\/)([A-Za-z0-9_-]{11})/)
  return match ? match[1] : raw
}

export default function Blog() {
  const [posts, setPosts] = useState([])
  const [draft, setDraft] = useState(BLANK)

  async function load() {
    setPosts((await api('/blog/list-posts')).items)
  }

  useEffect(() => { load() }, [])

  async function save(event) {
    event.preventDefault()
    await api(draft.id ? '/blog/update-post' : '/blog/create-post', draft)
    setDraft(BLANK)
    load()
  }

  async function remove(id) {
    await api('/blog/delete-post', { id })
    if (draft.id === id) setDraft(BLANK)
    load()
  }

  return (
    <div className="cols wide">
      <div className="panel">
        <h2>Posts <span className="pill">{posts.length}</span></h2>
        {posts.length === 0 ? (
          <div className="empty">Nothing published on this tape</div>
        ) : (
          posts.map((post) => (
            <article className="post" key={post.id}>
              <h4>{post.title}</h4>
              <div className="when">{post.created}</div>
              <p>{post.body}</p>
              {post.image && <img src={post.image} alt={post.title} loading="lazy" />}
              {post.youtube && (
                <iframe
                  src={`https://www.youtube.com/embed/${youtubeId(post.youtube)}`}
                  title={post.title}
                  allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture"
                  allowFullScreen
                />
              )}
              <div className="row">
                <button className="btn" onClick={() => setDraft({ ...BLANK, ...post })}>Edit</button>
                <button className="btn danger" onClick={() => remove(post.id)}>Delete</button>
              </div>
            </article>
          ))
        )}
      </div>

      <form className="panel" onSubmit={save}>
        <h2>{draft.id ? 'Edit post' : 'New post'}</h2>
        <label>Title</label>
        <input type="text" required value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
        <label>Body</label>
        <textarea style={{ minHeight: 150 }} value={draft.body} onChange={(e) => setDraft({ ...draft, body: e.target.value })} />
        <label>Image URL</label>
        <input type="text" value={draft.image} onChange={(e) => setDraft({ ...draft, image: e.target.value })} />
        <label>YouTube link or id</label>
        <input type="text" value={draft.youtube} onChange={(e) => setDraft({ ...draft, youtube: e.target.value })} />
        <div className="row">
          <button className="btn primary" type="submit">{draft.id ? 'Save post' : 'Publish'}</button>
          {draft.id && <button className="btn" type="button" onClick={() => setDraft(BLANK)}>Cancel</button>}
        </div>
      </form>
    </div>
  )
}
