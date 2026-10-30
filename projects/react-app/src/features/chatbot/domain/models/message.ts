export type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  error?: boolean
  slow?: boolean // 첫 글자가 늦어져 지연 안내를 보여주는 중
}
