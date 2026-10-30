import { ThemeProvider } from '@/components'
import { ChatbotPage } from '@/features/chatbot'

export default function App() {
  return (
    <ThemeProvider>
      <ChatbotPage />
    </ThemeProvider>
  )
}
