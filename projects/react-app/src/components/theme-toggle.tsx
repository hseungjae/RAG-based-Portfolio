import { Monitor, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme, type Theme } from '@/components/ui/theme-provider'

const LABEL: Record<Theme, string> = { system: '시스템 설정', light: '라이트 모드', dark: '다크 모드' }
const ICON: Record<Theme, typeof Sun> = { system: Monitor, light: Sun, dark: Moon }

export function ThemeToggle() {
  const { theme, cycleTheme } = useTheme()
  const Icon = ICON[theme]
  const label = `테마: ${LABEL[theme]} (눌러서 변경)`

  return (
    <Button variant="ghost" size="none" className="-m-1 p-1" onClick={cycleTheme} title={label} aria-label={label}>
      <Icon className="size-[18px]" strokeWidth={1.8} />
    </Button>
  )
}
