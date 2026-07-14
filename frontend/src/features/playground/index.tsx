import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Separator } from '@/components/ui/separator'
import { useCallback, useEffect, useRef, useState } from 'react'
import { ChatMessagesView } from './components/chat-message'
import type { Message } from './data/types'

// Mock AI responses for demonstration
const mockResponses = [
  "Hello! I'm your AI assistant. How can I help you today?",
  "That's a great question! Let me think about that...",
  "I understand what you're asking. Here's my take on it.",
  "Interesting! I'd be happy to help with that.",
  "Thanks for sharing! Let me provide some thoughts on this.",
]

export function Playground() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: "Hello! I'm your AI assistant. Feel free to start a conversation!",
      timestamp: new Date(),
    },
  ])
  const [isTyping, setIsTyping] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      )
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [messages])

  const handleSubmit = useCallback((content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "human",
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsTyping(true)

    // Simulate AI response after a delay
    setTimeout(() => {
      const randomResponse =
        mockResponses[Math.floor(Math.random() * mockResponses.length)]
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: randomResponse,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1000 + Math.random() * 1000)
  }, [messages]);

  const handleCancel = useCallback(() => {
    setIsTyping(false)
    window.location.reload()
  }, [messages]);

  return (
    <>
      <Header>
        <Search />
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main fixed>
        <div className='mb-4 flex h-[calc(100vh-8rem)] flex-col'>
          <h1 className='mb-4 text-2xl font-bold tracking-tight'>
            Playground
          </h1>

          <Separator className='mb-4' />

          <ChatMessagesView
            messages={messages}
            isLoading={false}
            scrollAreaRef={scrollAreaRef}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
          />
        </div>
      </Main>
    </>
  )
}
