const listeners = new Set()

export function onTape(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export async function api(path, body) {
  const options = body === undefined
    ? { method: 'GET' }
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }

  const response = await fetch(path, options)
  const tape = {
    path,
    status: response.status,
    cassette: response.headers.get('X-Vcr-Cassette') || 'none',
    played: Number(response.headers.get('X-Vcr-Played') || 0),
    retaped: (response.headers.get('X-Vcr-Retaped') || '').split(',').filter(Boolean),
    at: new Date().toLocaleTimeString(),
  }
  const data = await response.json()
  listeners.forEach((listener) => listener(tape))
  if (!response.ok) throw new Error(data.error || `request failed with ${response.status}`)
  return data
}
