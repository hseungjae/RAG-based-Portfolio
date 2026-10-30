import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

// 시스템 → 라이트 → 다크 순서로 전환한다
export const THEMES = ['system', 'light', 'dark'] as const
export type Theme = (typeof THEMES)[number]

type ThemeContextValue = { theme: Theme; cycleTheme: () => void }

const ThemeContext = createContext<ThemeContextValue | null>(null)

function storedTheme(): Theme {
  try {
    const t = localStorage.getItem('theme')
    if (t === 'light' || t === 'dark') return t
  } catch {
    // 저장소를 쓸 수 없으면 시스템 설정을 따른다
  }
  return 'system'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(storedTheme)

  useEffect(() => {
    try {
      if (theme === 'system') localStorage.removeItem('theme')
      else localStorage.setItem('theme', theme)
    } catch {
      // 저장하지 못해도 이번 방문 동안은 적용된다
    }

    const media = matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      const dark = theme === 'dark' || (theme === 'system' && media.matches)
      document.documentElement.classList.toggle('dark', dark)
    }
    apply()
    // 시스템 설정을 따를 때는 OS 테마가 바뀌면 바로 반영한다
    if (theme !== 'system') return
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [theme])

  const cycleTheme = () => setTheme((t) => THEMES[(THEMES.indexOf(t) + 1) % THEMES.length])

  return <ThemeContext.Provider value={{ theme, cycleTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme 은 ThemeProvider 안에서만 쓸 수 있어요.')
  return ctx
}
