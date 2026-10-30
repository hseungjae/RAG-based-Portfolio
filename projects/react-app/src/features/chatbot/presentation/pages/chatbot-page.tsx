import { useEffect } from 'react'
import { cn } from '@/core/utils/utils'
import { useChat } from '@/features/chatbot/domain/use-cases/use-chat'
import { useConfig } from '@/features/chatbot/domain/use-cases/use-config'
import { ChatForm } from '@/features/chatbot/presentation/views/chat-form'
import { EmptyChat } from '@/features/chatbot/presentation/views/empty-chat'
import { Header } from '@/features/chatbot/presentation/views/header'
import { MessageList } from '@/features/chatbot/presentation/views/message-list'

export function ChatbotPage() {
  const { owner } = useConfig()
  const { messages, busy, ask, reset } = useChat()
  const chatting = messages.length > 0

  // 새 메시지나 답변 조각이 오면 맨 아래로 내린다
  useEffect(() => {
    window.scrollTo({ top: document.body.scrollHeight })
  }, [messages])

  const handleReset = () => {
    reset()
    window.scrollTo({ top: 0 })
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <Header owner={owner} chatting={chatting} onReset={handleReset} />
      <main className={cn('mx-auto w-full max-w-[680px] flex-1 px-5 pb-6', chatting ? 'pt-6' : 'pt-8 sm:pt-14')}>
        {/* 대화가 시작되면 소개를 감춘다 */}
        {!chatting && <EmptyChat />}
        <MessageList messages={messages} />
      </main>
      <ChatForm busy={busy} onSubmit={ask} />
    </div>
  )
}
