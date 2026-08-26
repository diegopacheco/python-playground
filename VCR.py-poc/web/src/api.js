const listeners = new Set()

export function onTape(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function announce(tape) {
  listeners.forEach((listener) => listener({ at: new Date().toLocaleTimeString(), ...tape }))
}

export async function api(path, body) {
  const options = body === undefined
    ? { method: 'GET' }
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }

  let response
  try {
    response = await fetch(path, options)
  } catch (failure) {
    const error = 'the VCR player is not answering on :7500'
    announce({ path, status: 0, cassette: 'unreachable', played: 0, retaped: [], ok: false, error })
    throw new Error(error)
  }

  const tape = {
    path,
    status: response.status,
    cassette: response.headers.get('X-Vcr-Cassette') || 'none',
    played: Number(response.headers.get('X-Vcr-Played') || 0),
    retaped: (response.headers.get('X-Vcr-Retaped') || '').split(',').filter(Boolean),
    ok: response.ok,
    error: '',
  }

  let data
  try {
    data = await response.json()
  } catch (failure) {
    tape.ok = false
    tape.error = `${response.status} did not return JSON`
    announce(tape)
    throw new Error(tape.error)
  }

  if (!response.ok) tape.error = data.error || `request failed with ${response.status}`
  announce(tape)
  if (!response.ok) throw new Error(tape.error)
  return data
}
