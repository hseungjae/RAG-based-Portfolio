import { API_URL } from '@/core/constants/api-url'
import { requestError } from '@/core/network/http-client'

export type ServerSentEvent = { event: string; data: unknown }

// POST 요청을 보내고 SSE 응답을 이벤트 단위로 하나씩 돌려준다
export async function* postStream(path: string, body: unknown): AsyncGenerator<ServerSentEvent> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok || !res.body) throw await requestError(res)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const raw = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      const event = raw.match(/^event: (.*)$/m)?.[1] ?? 'message'
      const data = JSON.parse(raw.match(/^data: (.*)$/m)?.[1] ?? 'null')
      yield { event, data }
    }
  }
}
