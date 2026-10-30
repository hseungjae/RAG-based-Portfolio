import { useEffect, useState } from 'react'
import { chatbotRepository } from '@/features/chatbot/data/repositories/chatbot-repository'

const DEFAULT_OWNER = '한승재'

// 서버 설정(이름)을 불러와 화면과 탭 제목에 쓴다. 실패하면 기본값을 그대로 둔다
export function useConfig() {
  const [owner, setOwner] = useState(DEFAULT_OWNER)

  useEffect(() => {
    chatbotRepository
      .getConfig()
      .then((c) => {
        setOwner(c.owner)
        document.title = `${c.owner} · Ask Me Anything`
      })
      .catch(() => {})
  }, [])

  return { owner }
}
