export type Message = {
  id: string
  type: 'human' | 'ai'
  content: string
  timestamp: Date
}
