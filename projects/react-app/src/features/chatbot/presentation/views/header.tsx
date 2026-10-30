import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'
import { LINKS } from '@/core/constants/links'

type Props = {
  owner: string
  chatting: boolean
  onReset: () => void
}

export function Header({ owner, chatting, onReset }: Props) {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between bg-background px-[max(20px,calc((100%-680px)/2))]">
      <a className="font-bold" href="/">
        {owner}
      </a>
      <nav className="flex items-center gap-4 sm:gap-5">
        {chatting && (
          <Button variant="link" size="none" onClick={onReset}>
            새 대화
          </Button>
        )}
        <Button variant="link" size="none" asChild>
          <a href={LINKS.github} target="_blank" rel="noopener">
            GitHub
          </a>
        </Button>
        <Button variant="link" size="none" asChild>
          <a href={LINKS.notion} target="_blank" rel="noopener">
            Notion
          </a>
        </Button>
        <ThemeToggle />
      </nav>
    </header>
  )
}
