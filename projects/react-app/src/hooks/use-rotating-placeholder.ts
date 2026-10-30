import { useEffect, useState } from 'react'

// 빈 입력창에 예시 질문을 돌아가며 보여준다
export function useRotatingPlaceholder(items: string[], paused: boolean, intervalMs = 3000) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    // 입력 중일 땐 보이지 않으니 바꾸지 않고, 움직임 줄이기 설정이면 고정한다
    if (paused || matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const timer = setInterval(() => setIndex((i) => (i + 1) % items.length), intervalMs)
    return () => clearInterval(timer)
  }, [items.length, paused, intervalMs])

  return items[index]
}
