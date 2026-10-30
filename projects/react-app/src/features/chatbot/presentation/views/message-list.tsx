import type { Message } from '@/features/chatbot/domain/models/message'
import { MessageItem } from '@/features/chatbot/presentation/views/message-item'

export function MessageList({ messages }: { messages: Message[] }) {
  return (
    <section className="flex flex-col gap-7" aria-live="polite">
      {messages.map((m) => (
        <MessageItem key={m.id} message={m} />
      ))}
    </section>
  )
}
