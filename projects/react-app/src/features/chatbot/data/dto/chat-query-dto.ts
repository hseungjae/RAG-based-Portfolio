// POST /api/chat 요청 본문 (projects/system/webapp/dto.py 와 같은 모양)
export type ChatTurnDto = { role: 'user' | 'assistant'; content: string }

export type ChatQueryDto = {
  question: string
  history: ChatTurnDto[]
}
