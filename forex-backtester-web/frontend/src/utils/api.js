const BASE = (import.meta.env.VITE_API_URL || '') + '/api'

async function req(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  get:    (path)        => req('GET',    path),
  post:   (path, body)  => req('POST',   path, body),
  delete: (path)        => req('DELETE', path),

  // Auth
  connect:    (body) => req('POST', '/auth/connect',    body),
  verify:     (body) => req('POST', '/auth/verify',     body),
  authStatus: (s)    => req('GET',  `/auth/status?session_name=${s}`),
  disconnect: (body) => req('POST', '/auth/disconnect', body),

  // Channels
  getChannels:   (s)    => req('GET',    `/channels?session_name=${s}`),
  addChannel:    (body) => req('POST',   '/channels', body),
  deleteChannel: (id,s) => req('DELETE', `/channels/${id}?session_name=${s}`),

  // Backtest
  fetchHistory: (body) => req('POST', '/backtest/fetch', body),
  runBacktest:  (body) => req('POST', '/backtest/run',   body),
  jobStatus:    (id)   => req('GET',  `/backtest/status/${id}`),

  // Results
  getStats:   (s, p, pr) => req('GET', `/results/stats?session_name=${s}${p?`&pair=${p}`:''}${pr?`&provider=${pr}`:''}`),
  getTrades:  (s)        => req('GET', `/results/trades?session_name=${s}`),
  getSignals: (s)        => req('GET', `/results/signals?session_name=${s}`),
  exportCsv:  (s)        => window.open(`/api/results/export/csv?session_name=${s}`),
}
