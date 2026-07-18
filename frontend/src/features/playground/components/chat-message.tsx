import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { Bot, Copy, CopyCheck, Loader2, User } from 'lucide-react';
import { ReactNode, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../data/types';
import { ChatInput } from './chat-input';

// Markdown component props type from former ReportView
type MdComponentProps = {
  className?: string
  children?: ReactNode
  [key: string]: any
}

const mdComponents = {
  h1: ({ className, children, ...props }: MdComponentProps) => (
    <h1 className={cn('mt-4 mb-2 text-2xl font-bold', className)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ className, children, ...props }: MdComponentProps) => (
    <h2 className={cn('mt-3 mb-2 text-xl font-bold', className)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ className, children, ...props }: MdComponentProps) => (
    <h3 className={cn('mt-3 mb-1 text-lg font-bold', className)} {...props}>
      {children}
    </h3>
  ),
  p: ({ className, children, ...props }: MdComponentProps) => (
    <p className={cn('mb-3 leading-7', className)} {...props}>
      {children}
    </p>
  ),
  a: ({ className, children, href, ...props }: MdComponentProps) => (
    <Badge className='mx-0.5 text-xs'>
      <a
        className={cn('text-xs text-blue-400 hover:text-blue-300', className)}
        href={href}
        target='_blank'
        rel='noopener noreferrer'
        {...props}
      >
        {children}
      </a>
    </Badge>
  ),
  ul: ({ className, children, ...props }: MdComponentProps) => (
    <ul className={cn('mb-3 list-disc pl-6', className)} {...props}>
      {children}
    </ul>
  ),
  ol: ({ className, children, ...props }: MdComponentProps) => (
    <ol className={cn('mb-3 list-decimal pl-6', className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ className, children, ...props }: MdComponentProps) => (
    <li className={cn('mb-1', className)} {...props}>
      {children}
    </li>
  ),
  blockquote: ({ className, children, ...props }: MdComponentProps) => (
    <blockquote
      className={cn(
        'my-3 border-l-4 border-border pl-4 text-sm italic',
        className
      )}
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }: MdComponentProps) => (
    <code
      className={cn(
        'rounded bg-secondary px-1 py-0.5 font-mono text-xs',
        className
      )}
      {...props}
    >
      {children}
    </code>
  ),
  pre: ({ className, children, ...props }: MdComponentProps) => (
    <pre
      className={cn(
        'my-3 overflow-x-auto rounded-lg bg-secondary p-3 font-mono text-xs',
        className
      )}
      {...props}
    >
      {children}
    </pre>
  ),
  hr: ({ className, ...props }: MdComponentProps) => (
    <hr className={cn('my-4 border-border', className)} {...props} />
  ),
  table: ({ className, children, ...props }: MdComponentProps) => (
    <div className='my-3 overflow-x-auto'>
      <table className={cn('w-full border-collapse', className)} {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ className, children, ...props }: MdComponentProps) => (
    <th
      className={cn(
        'border border-border px-3 py-2 text-left font-bold',
        className
      )}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ className, children, ...props }: MdComponentProps) => (
    <td className={cn('border border-border px-3 py-2', className)} {...props}>
      {children}
    </td>
  ),
}

// Props for HumanMessageBubble
interface HumanMessageBubbleProps {
  message: Message
  mdComponents: typeof mdComponents
}

// HumanMessageBubble Component
const HumanMessageBubble: React.FC<HumanMessageBubbleProps> = ({
  message,
  mdComponents,
}) => {
  return (
    <div className='flex w-full flex-col items-end gap-2 py-4'>
      {/* Header row: timestamp + Avatar */}
      <div className='flex items-center gap-3'>
        <Avatar className='size-8 shrink-0'>
          <AvatarFallback>
            <User size={16} />
          </AvatarFallback>
        </Avatar>
      </div>

      {/* Content: Markdown bubble */}
      <div className='w-fit max-w-[80%]'>
        <div
          className={`min-h-7 rounded-3xl rounded-tr-lg bg-primary px-4 py-3 wrap-break-word text-primary-foreground`}
        >
          <ReactMarkdown components={mdComponents}>
            {typeof message.content === 'string'
              ? message.content
              : JSON.stringify(message.content)}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

// Props for AiMessageBubble
interface AiMessageBubbleProps {
  message: Message
  mdComponents: typeof mdComponents
  handleCopy: (text: string, messageId: string) => void
  copiedMessageId: string | null
}

// AiMessageBubble Component
const AiMessageBubble: React.FC<AiMessageBubbleProps> = ({
  message,
  mdComponents,
  handleCopy,
  copiedMessageId,
}) => {
  return (
    <div className='flex w-full flex-col justify-start gap-2 py-4'>
      {/* Header row: Avatar + timestamp */}
      <div className='flex items-center gap-3'>
        <Avatar className='size-8 shrink-0'>
          <AvatarFallback>
            <Bot size={16} />
          </AvatarFallback>
        </Avatar>
      </div>

      {/* Content: Markdown bubble + Copy button */}
      <div className='flex w-fit max-w-[80%] flex-col items-start gap-1 pl-11'>
        <div
          className={`min-h-7 rounded-3xl rounded-tl-lg bg-muted px-4 pt-3 wrap-break-word text-foreground`}
        >
          <ReactMarkdown components={mdComponents}>
            {typeof message.content === 'string'
              ? message.content
              : JSON.stringify(message.content)}
          </ReactMarkdown>
        </div>

        <Button
          variant='ghost'
          className={`cursor-pointer self-end text-muted-foreground hover:bg-transparent hover:text-foreground ${
            message.content.length > 0 ? 'visible' : 'hidden'
          }`}
          onClick={() =>
            handleCopy(
              typeof message.content === 'string'
                ? message.content
                : JSON.stringify(message.content),
              message.id!
            )
          }
        >
          {copiedMessageId === message.id ? 'Copied' : 'Copy'}
          {copiedMessageId === message.id ? <CopyCheck /> : <Copy />}
        </Button>
      </div>
    </div>
  )
}

interface ChatMessagesViewProps {
  messages: Message[]
  isLoading: boolean
  scrollAreaRef: React.RefObject<HTMLDivElement | null>
  onSubmit: (inputValue: string, effort: string, model: string) => void
  onCancel: () => void
}

export function ChatMessagesView({
  messages,
  isLoading,
  scrollAreaRef,
  onSubmit,
  onCancel,
}: ChatMessagesViewProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMessageId(messageId)
      setTimeout(() => {
        setCopiedMessageId(null)
      }, 2000) // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  return (
    <div className='flex h-full flex-col'>
      <ScrollArea className='flex-1 overflow-y-auto' ref={scrollAreaRef}>
        <div className='mx-auto max-w-4xl space-y-2 p-4 pt-16 md:p-6'>
          {messages.map((message, index) => {
            // const isLast = index === messages.length - 1;
            return (
              <div key={message.id || `msg-${index}`} className='space-y-3'>
                <div
                  className={`flex items-start gap-3 ${message.type === 'human' ? 'justify-end' : ''}`}
                >
                  {message.type === 'human' ? (
                    <HumanMessageBubble
                      message={message}
                      mdComponents={mdComponents}
                    />
                  ) : (
                    <AiMessageBubble
                      message={message}
                      mdComponents={mdComponents}
                      handleCopy={handleCopy}
                      copiedMessageId={copiedMessageId}
                    />
                  )}
                </div>
              </div>
            )
          })}
          {isLoading &&
            (messages.length === 0 ||
              (messages[messages.length - 1].type === 'human' && (
                <div className='mt-3 flex items-start gap-3'>
                  {' '}
                  {/* AI message row structure */}
                  <div className='group relative max-w-[85%] rounded-xl p-3 wrap-break-word shadow-sm md:max-w-[80%]'>
                    <div className='flex h-full items-center justify-start'>
                      <Loader2 className='mr-2 h-5 w-5 animate-spin text-muted-foreground' />
                      <span>Processing...</span>
                    </div>
                  </div>
                </div>
              )))}
        </div>
      </ScrollArea>
      <ChatInput
        onSubmit={onSubmit}
        isLoading={isLoading}
        onCancel={onCancel}
        hasHistory={messages.length > 0}
      />
    </div>
  )
}
