import { useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { ArrowUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useRotatingPlaceholder } from '@/hooks/use-rotating-placeholder'

const PLACEHOLDERS = [
  '기능경기대회 성적은 어땠나요?',
  '어떤 프로젝트를 했나요?',
  '지금 어디서 일하나요?',
  '트러블슈팅 경험이 있나요?',
  '협업 경험을 알려주세요',
  '강점과 약점이 뭐예요?',
]
const MAX_HEIGHT = 140

type Props = {
  busy: boolean
  onSubmit: (question: string) => void
}

export function ChatForm({ busy, onSubmit }: Props) {
  const [value, setValue] = useState('')
  const textarea = useRef<HTMLTextAreaElement>(null)
  const placeholder = useRotatingPlaceholder(PLACEHOLDERS, value !== '')

  // 내용에 맞춰 높이를 늘리고, 최대 높이를 넘을 때만 스크롤바를 보여준다
  useLayoutEffect(() => {
    const el = textarea.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
    el.style.overflowY = el.scrollHeight > MAX_HEIGHT ? 'auto' : 'hidden'
  }, [value])

  // 답변이 끝나면 바로 다음 질문을 쓸 수 있게 한다 (처음 열 때는 모바일 키보드가 뜨지 않도록 건너뛴다)
  const wasBusy = useRef(false)
  useLayoutEffect(() => {
    if (wasBusy.current && !busy) textarea.current?.focus()
    wasBusy.current = busy
  }, [busy])

  const send = () => {
    const q = value.trim()
    if (!q || busy) return
    setValue('')
    onSubmit(q)
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    send()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    const composing = e.nativeEvent.isComposing
    // 빈 입력창에서 Tab을 누르면 지금 보이는 예시 질문을 채워 넣는다
    if (e.key === 'Tab' && !e.shiftKey && !value && !composing) {
      e.preventDefault()
      setValue(placeholder)
      return
    }
    // 한글 조합 중 Enter는 무시해야 마지막 글자가 중복 전송되지 않는다
    if (e.key === 'Enter' && !e.shiftKey && !composing) {
      e.preventDefault()
      send()
    }
  }

  return (
    <footer className="sticky bottom-0 bg-gradient-to-t from-background from-70% to-transparent px-5 pb-[max(16px,env(safe-area-inset-bottom))] pt-3">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex max-w-[640px] items-end gap-2 rounded-3xl border bg-background py-1.5 pl-[18px] pr-1.5 transition-colors focus-within:border-faint"
      >
        <textarea
          ref={textarea}
          rows={1}
          maxLength={500}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label="질문"
          className="max-h-[140px] min-w-0 flex-1 resize-none overflow-y-hidden bg-transparent py-[7px] leading-[1.6] outline-none placeholder:text-faint focus-visible:outline-none"
        />
        <Button type="submit" size="icon" aria-label="보내기" disabled={busy || !value.trim()} className="disabled:opacity-20">
          <ArrowUp className="size-[18px]" strokeWidth={2.2} />
        </Button>
      </form>
    </footer>
  )
}
