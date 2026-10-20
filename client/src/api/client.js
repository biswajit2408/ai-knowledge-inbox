// Thin wrapper around fetch: one place for the base URL, JSON handling and
// turning error responses into readable messages.

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  constructor(message, { status, requestId } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.requestId = requestId
  }
}

async function request(path, { method = 'GET', body } = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Cannot reach the server. Is the backend running?', { status: 0 })
  }

  const requestId = response.headers.get('X-Request-ID')
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(describeError(data, response.status), { status: response.status, requestId })
  }
  return data
}

// FastAPI sends either {"detail": "message"} or, for validation errors,
// {"detail": [{"loc": [...], "msg": "..."}]}.
function describeError(data, status) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((e) => `${e.loc?.at(-1) ?? 'request'}: ${e.msg}`).join('; ')
  }
  return `Request failed (HTTP ${status}).`
}

export const api = {
  listItems: () => request('/items'),
  ingest: (payload) => request('/ingest', { method: 'POST', body: payload }),
  query: (question) => request('/query', { method: 'POST', body: { question } }),
}
