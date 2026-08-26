import { useEffect, useState } from 'react'
import { api } from '../api.js'

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function Gallery() {
  const [images, setImages] = useState([])
  const [url, setUrl] = useState('')
  const [hot, setHot] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setImages((await api('/images/list-images')).items)
  }

  useEffect(() => { load() }, [])

  async function upload(payload) {
    try {
      await api('/images/upload-image', payload)
      setError('')
      load()
    } catch (failure) {
      setError(failure.message)
    }
  }

  async function addFiles(files) {
    for (const file of files) {
      if (!file.type.startsWith('image/')) continue
      await upload({ name: file.name, dataUrl: await readAsDataUrl(file) })
    }
  }

  async function addUrl(event) {
    event.preventDefault()
    if (!url.trim()) return
    await upload({ url: url.trim() })
    setUrl('')
  }

  async function remove(id) {
    await api('/images/delete-image', { id })
    load()
  }

  return (
    <div className="panel">
      <h2>Gallery <span className="pill">{images.length}</span></h2>

      <div
        className={hot ? 'drop hot' : 'drop'}
        onDragOver={(event) => { event.preventDefault(); setHot(true) }}
        onDragLeave={() => setHot(false)}
        onDrop={(event) => {
          event.preventDefault()
          setHot(false)
          addFiles([...event.dataTransfer.files])
        }}
      >
        Drop images here, or
        <label style={{ display: 'inline', color: 'var(--accent)', cursor: 'pointer', margin: '0 4px' }}>
          browse
          <input
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={(event) => addFiles([...event.target.files])}
          />
        </label>
        — dropped bytes are written to the OS temp dir
      </div>

      <form className="row" onSubmit={addUrl}>
        <input
          type="text"
          style={{ flex: 1, minWidth: 240 }}
          placeholder="or paste an image URL"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />
        <button className="btn primary" type="submit">Add from URL</button>
      </form>

      {error && <p className="error">{error}</p>}

      {images.length === 0 ? (
        <div className="empty" style={{ marginTop: 16 }}>The gallery tape is empty</div>
      ) : (
        <div className="gallery">
          {images.map((image) => (
            <figure className="card" key={image.id} style={{ margin: 0 }}>
              <img src={image.url} alt={image.name} loading="lazy" />
              <figcaption className="meta">
                <b title={image.name}>{image.name}</b>
                <span className="pill">{image.source}</span>
                <button className="btn ghost danger" onClick={() => remove(image.id)}>×</button>
              </figcaption>
            </figure>
          ))}
        </div>
      )}
    </div>
  )
}
