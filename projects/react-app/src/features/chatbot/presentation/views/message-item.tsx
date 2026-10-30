import { MarkdownRenderer } from '@/core/utils/markdown-renderer'
import type { Message } from '@/features/chatbot/domain/models/message'
import { LoadingIndicator } from '@/features/chatbot/presentation/views/loading-indicator'

function Answer({ message }: { message: Message }) {
  if (message.error) return <div className="text-destructive">{message.content}</div>
  if (!message.content) return <LoadingIndicator slow={message.slow} />
  return <MarkdownRenderer text={message.content} />
}

export function MessageItem({ message }: { message: Message }) {
  if (message.role === 'user') {
    return (
      <div className="max-w-[80%] self-end whitespace-pre-wrap break-keep rounded-[18px] bg-muted px-4 py-2.5 [overflow-wrap:anywhere]">
        {message.content}
      </div>
    )
  }
  return (
    <div className="break-keep [overflow-wrap:anywhere]">
      <Answer message={message} />
    </div>
  )
}
