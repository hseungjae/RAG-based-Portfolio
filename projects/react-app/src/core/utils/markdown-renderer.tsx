import type { ReactNode } from 'react'

// 굵게 / 목록 / 문단 정도만 지원하는 작은 마크다운 렌더러.
// HTML 문자열이 아니라 React 요소로 만들기 때문에 이스케이프가 따로 필요 없다.

const LIST_ITEM = /^\s*([-*]|\d+\.)\s+/

function inline(text: string): ReactNode[] {
  return text.split(/\*\*(.+?)\*\*/g).map((part, i) => (i % 2 ? <strong key={i}>{part}</strong> : part))
}

export function MarkdownRenderer({ text }: { text: string }) {
  return text.split(/\n{2,}/).map((block, i) => {
    const lines = block.split('\n')
    if (lines.every((l) => LIST_ITEM.test(l))) {
      return (
        <ul key={i} className="mb-2.5 mt-1 list-disc pl-5 last:mb-0">
          {lines.map((l, j) => (
            <li key={j}>{inline(l.replace(LIST_ITEM, ''))}</li>
          ))}
        </ul>
      )
    }
    return (
      <p key={i} className="mb-2.5 last:mb-0">
        {lines.map((l, j) => (
          <span key={j}>
            {j > 0 && <br />}
            {inline(l)}
          </span>
        ))}
      </p>
    )
  })
}
