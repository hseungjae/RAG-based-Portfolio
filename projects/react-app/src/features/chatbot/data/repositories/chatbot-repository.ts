import { getJson } from '@/core/network/http-client'
import { postStream } from '@/core/network/stream-client'
import type { ChatQueryDto } from '@/features/chatbot/data/dto/chat-query-dto'
import type { ConfigDto } from '@/features/chatbot/data/dto/config-dto'

export const chatbotRepository = {
  getConfig: () => getJson<ConfigDto>('/config'),

  // SSE 응답(sources → delta… → done, 실패 시 error)을 읽어 답변 조각마다 onDelta를 부른다
  async streamChat(query: ChatQueryDto, onDelta: (text: string) => void) {
    for await (const { event, data } of postStream('/chat', query)) {
      if (event === 'delta') onDelta(data as string)
      else if (event === 'error') throw new Error(data as string)
    }
  },
}
