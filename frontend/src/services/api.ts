import {
  ChatRequest,
  ChatResponse,
  DictionaryRequest,
  DictionaryResponse,
  GrammarCheckRequest,
  GrammarCheckResponse,
  STTResponse,
  TTSRequest,
  TTSResponse,
} from '../types/api'

/** Resolve the backend base URL, preferring local overrides during development. */
export function getApiBase() {
  if (!import.meta.env.DEV) {
    return ''
  }
  const saved = localStorage.getItem('settings:apiBaseUrl')
  return saved || ((import.meta.env.VITE_API_BASE_URL as string) || '/api')
}

/** Perform a standard chat completion call against the FastAPI backend. */
export async function chat(req: ChatRequest, base?: string): Promise<ChatResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/chat`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`)
  return res.json()
}

/**
 * Stream a chat completion using Server-Sent Events, yielding textual deltas.
 * Falls back to sending the raw data chunk when it is not valid JSON.
 */
export async function* chatStream(req: ChatRequest, base?: string): AsyncGenerator<string, void, unknown> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/chat/stream`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      buffer += decoder.decode()
      break
    }
    buffer += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const line = chunk.trim()
      if (!line) continue
      if (line.startsWith('data:')) {
        const data = line.slice(5).trim()
        if (data === '[DONE]') return
        try {
          const parsed = JSON.parse(data)
          if (parsed?.error) throw new Error(parsed.error)
          const text = parsed?.choices?.[0]?.delta?.content ?? parsed?.content ?? ''
          if (text) yield text
        } catch (err) {
          if (data.startsWith('{') || data.startsWith('[')) {
            throw err
          } else {
            yield data
          }
        }
      }
    }
  }

}

export async function tts(req: TTSRequest, base?: string): Promise<TTSResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/tts`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`TTS failed: ${res.status}`)
  return res.json()
}

export async function stt(file: File, base?: string): Promise<STTResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/stt`
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(url, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) throw new Error(`STT failed: ${res.status}`)
  return res.json()
}

export async function grammarCheck(req: GrammarCheckRequest, base?: string): Promise<GrammarCheckResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/grammar`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`Grammar check failed: ${res.status}`)
  return res.json()
}

export async function dictionaryLookup(req: DictionaryRequest, base?: string): Promise<DictionaryResponse> {
  const resolvedBase = base ?? getApiBase()
  const url = `${resolvedBase}/dictionary`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`Dictionary lookup failed: ${res.status}`)
  return res.json()
}
