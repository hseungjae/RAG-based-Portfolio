import { LINKS } from '@/core/constants/links'

const SHORTCUTS = [
  { label: '자기소개 읽어보기', href: LINKS.profile },
  { label: 'GitHub 바로가기', href: LINKS.github },
  { label: '포트폴리오 바로가기', href: LINKS.notion },
]

export function EmptyChat() {
  return (
    <section className="mb-2">
      <p className="mb-3 text-sm text-muted-foreground">Cloud Engineer</p>
      <h1 className="mb-4 break-keep text-[clamp(28px,5.4vw,40px)] font-bold leading-[1.3] tracking-[-0.035em]">
        읽는 대신,
        <br />
        대화로 소개합니다.
      </h1>
      <p className="mb-7 break-keep text-muted-foreground sm:mb-10">
        자기소개 문서에서 관련 내용을 찾아 그 내용만으로 답하는 RAG 챗봇입니다.
      </p>

      <ul className="border-t">
        {SHORTCUTS.map(({ label, href }) => (
          <li key={href} className="border-b">
            <a
              className="group flex w-full items-center justify-between px-0.5 py-3.5"
              href={href}
              target="_blank"
              rel="noopener"
            >
              {label}
              <span className="text-faint transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-foreground">
                ↗
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}
