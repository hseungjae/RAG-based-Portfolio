import { useRef, useState } from 'react'
import type { ChatTurnDto } from '@/features/chatbot/data/dto/chat-query-dto'
import { chatbotRepository } from '@/features/chatbot/data/repositories/chatbot-repository'
import type { Message } from '@/features/chatbot/domain/models/message'

const SLOW_MS = 10_000 // 이 시간이 지나도 첫 글자가 없으면 지연 안내를 보여준다
const HISTORY_SIZE = 6 // 최근 대화만 서버에 보내서 후속 질문 맥락으로 사용

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [busy, setBusy] = useState(false)
  const history = useRef<ChatTurnDto[]>([])
  const nextId = useRef(0)

  const update = (id: number, patch: Partial<Message>) =>
    setMessages((ms) => ms.map((m) => (m.id === id ? { ...m, ...patch } : m)))

  async function ask(question: string) {
    if (busy) return
    setBusy(true)
    const answerId = nextId.current + 1
    nextId.current += 2
    setMessages((ms) => [
      ...ms,
      { id: answerId - 1, role: 'user', content: question },
      { id: answerId, role: 'assistant', content: '' },
    ])

    let answer = ''
    // 무료 Gemini API는 붐빌 때 첫 응답까지 수십 초가 걸리기도 해서, 기다리는 이유를 알려준다
    const slowTimer = setTimeout(() => {
      if (!answer) update(answerId, { slow: true })
    }, SLOW_MS)

    try {
      await chatbotRepository.streamChat({ question, history: history.current.slice(-HISTORY_SIZE) }, (delta) => {
        answer += delta
        update(answerId, { content: answer, slow: false })
      })
      history.current.push({ role: 'user', content: question }, { role: 'assistant', content: answer })
    } catch (e) {
      const message = e instanceof Error ? e.message : '요청에 실패했어요.'
      update(answerId, { content: message, error: true, slow: false })
    } finally {
      clearTimeout(slowTimer)
      setBusy(false)
    }
  }

  function reset() {
    if (busy) return
    history.current = []
    setMessages([])
  }

  return { messages, busy, ask, reset }
}
