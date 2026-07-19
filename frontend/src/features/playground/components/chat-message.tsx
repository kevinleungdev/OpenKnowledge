import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import {
  Bot,
  Copy,
  CopyCheck,
  MoreVertical,
  ThumbsDown,
  ThumbsUp,
  User,
} from 'lucide-react'
import { type ComponentProps, type FC, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../data/types'
import { mutedIconButtonClass } from './constants'

const mdComponents = {
  h1: ({ className, children, ...props }: ComponentProps<'h1'>) => (
    <h1 className={cn('mt-4 mb-2 text-2xl font-bold', className)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ className, children, ...props }: ComponentProps<'h2'>) => (
    <h2 className={cn('mt-3 mb-2 text-xl font-bold', className)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ className, children, ...props }: ComponentProps<'h3'>) => (
    <h3 className={cn('mt-3 mb-1 text-lg font-bold', className)} {...props}>
      {children}
    </h3>
  ),
  p: ({ className, children, ...props }: ComponentProps<'p'>) => (
    <p className={cn('mb-3 leading-7', className)} {...props}>
      {children}
    </p>
  ),
  a: ({ className, children, href, ...props }: ComponentProps<'a'>) => (
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
  ul: ({ className, children, ...props }: ComponentProps<'ul'>) => (
    <ul className={cn('mb-3 list-disc pl-6', className)} {...props}>
      {children}
    </ul>
  ),
  ol: ({ className, children, ...props }: ComponentProps<'ol'>) => (
    <ol className={cn('mb-3 list-decimal pl-6', className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ className, children, ...props }: ComponentProps<'li'>) => (
    <li className={cn('mb-1', className)} {...props}>
      {children}
    </li>
  ),
  blockquote: ({ className, children, ...props }: ComponentProps<'blockquote'>) => (
    <blockquote
      className={cn('my-3 border-l-4 border-border pl-4 text-sm italic', className)}
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }: ComponentProps<'code'>) => (
    <code
      className={cn('rounded bg-secondary px-1 py-0.5 font-mono text-xs', className)}
      {...props}
    >
      {children}
    </code>
  ),
  pre: ({ className, children, ...props }: ComponentProps<'pre'>) => (
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
  hr: ({ className, ...props }: ComponentProps<'hr'>) => (
    <hr className={cn('my-4 border-border', className)} {...props} />
  ),
  table: ({ className, children, ...props }: ComponentProps<'table'>) => (
    <div className='my-3 overflow-x-auto'>
      <table className={cn('w-full border-collapse', className)} {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ className, children, ...props }: ComponentProps<'th'>) => (
    <th
      className={cn('border border-border px-3 py-2 text-left font-bold', className)}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ className, children, ...props }: ComponentProps<'td'>) => (
    <td className={cn('border border-border px-3 py-2', className)} {...props}>
      {children}
    </td>
  ),
}

// Props for HumanMessageBubble
interface HumanMessageBubbleProps {
  message: Message
}

// HumanMessageBubble Component - [text][avatar], right-anchored, top-aligned
const HumanMessageBubble: FC<HumanMessageBubbleProps> = ({ message }) => {
  return (
    <div className='flex w-full items-start justify-end gap-3 py-4'>
      {/* Content: Markdown bubble */}
      <div className='flex w-fit max-w-[80%] flex-col items-end gap-1'>
        <div className='min-h-7 rounded-3xl rounded-tr-lg bg-primary px-4 py-3 wrap-break-word text-primary-foreground'>
          <ReactMarkdown components={mdComponents}>{message.content}</ReactMarkdown>
        </div>
      </div>

      {/* Avatar */}
      <Avatar className='size-8 shrink-0'>
        <AvatarFallback>
          <User size={16} />
        </AvatarFallback>
      </Avatar>
    </div>
  )
}

// Props for AiResponseActions
interface AiResponseActionsProps {
  message: Message
  handleCopy: (text: string, messageId: string) => void
  copiedMessageId: string | null
}

// AI Response Actions - gray icon row below AI text: thumbs up/down (mutually
// exclusive, in-session), copy (swaps to CopyCheck for 2s), and a more-menu
// whose only item is a disabled placeholder.
const AiResponseActions: FC<AiResponseActionsProps> = ({
  message,
  handleCopy,
  copiedMessageId,
}) => {
  const [thumb, setThumb] = useState<'up' | 'down' | null>(null)
  const isCopied = copiedMessageId === message.id

  return (
    <div className='flex items-center gap-0.5'>
      <Button
        type='button'
        variant='ghost'
        size='icon'
        className={cn(mutedIconButtonClass, thumb === 'up' && 'text-primary hover:text-primary')}
        onClick={() => setThumb((prev) => (prev === 'up' ? null : 'up'))}
        aria-pressed={thumb === 'up'}
      >
        <ThumbsUp className='size-4' />
      </Button>
      <Button
        type='button'
        variant='ghost'
        size='icon'
        className={cn(
          mutedIconButtonClass,
          thumb === 'down' && 'text-primary hover:text-primary'
        )}
        onClick={() => setThumb((prev) => (prev === 'down' ? null : 'down'))}
        aria-pressed={thumb === 'down'}
      >
        <ThumbsDown className='size-4' />
      </Button>
      <Button
        type='button'
        variant='ghost'
        size='icon'
        className={mutedIconButtonClass}
        onClick={() => handleCopy(message.content, message.id)}
      >
        {isCopied ? <CopyCheck className='size-4' /> : <Copy className='size-4' />}
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button type='button' variant='ghost' size='icon' className={mutedIconButtonClass}>
            <MoreVertical className='size-4' />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align='start'>
          <DropdownMenuItem disabled>Coming soon</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

// Props for AiMessageBubble
interface AiMessageBubbleProps {
  message: Message
  handleCopy: (text: string, messageId: string) => void
  copiedMessageId: string | null
}

// AiMessageBubble Component - [avatar][text], left-anchored, top-aligned
const AiMessageBubble: FC<AiMessageBubbleProps> = ({
  message,
  handleCopy,
  copiedMessageId,
}) => {
  return (
    <div className='flex w-full items-start gap-3 py-4'>
      {/* Avatar */}
      <Avatar className='size-8 shrink-0'>
        <AvatarFallback>
          <Bot size={16} />
        </AvatarFallback>
      </Avatar>

      {/* Content: Markdown bubble + response actions */}
      <div className='flex w-fit max-w-[80%] flex-col items-start gap-1'>
        <div className='min-h-7 rounded-3xl rounded-tl-lg bg-muted px-4 py-3 wrap-break-word text-foreground'>
          <ReactMarkdown components={mdComponents}>{message.content}</ReactMarkdown>
        </div>

        <AiResponseActions
          message={message}
          handleCopy={handleCopy}
          copiedMessageId={copiedMessageId}
        />
      </div>
    </div>
  )
}

// Static seed exchange - placeholder content, not server state. Held here (not
// in the provider, not in TanStack Query) until the Run pipeline is wired.
// Several turns so the scrollable area can be exercised.
const SEED_AI_BUBBLE = `Here's a compact bubble sort in Python:

\`\`\`python
def bubble_sort(items):
    n = len(items)
    for i in range(n):
        for j in range(n - i - 1):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items
\`\`\`

It walks the list repeatedly, swapping adjacent pairs that are out of order, until a full pass makes no swaps.`

const SEED_AI_SELECTION = `Selection sort picks the smallest remaining element on each pass and swaps it into place:

\`\`\`python
def selection_sort(items):
    for i in range(len(items)):
        lo = i
        for j in range(i + 1, len(items)):
            if items[j] < items[lo]:
                lo = j
        items[i], items[lo] = items[lo], items[i]
    return items
\`\`\`

It does fewer swaps than bubble sort but still makes O(n²) comparisons.`

const SEED_AI_INSERTION = `Insertion sort builds the sorted list one item at a time, inserting each into its correct spot:

\`\`\`python
def insertion_sort(items):
    for i in range(1, len(items)):
        cur = items[i]
        j = i - 1
        while j >= 0 and items[j] > cur:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = cur
    return items
\`\`\`

It shines on small or nearly-sorted lists.`

const SEED_AI_NEARLY = `For nearly-sorted data, **insertion sort** is typically the best of these three. It runs in near O(n) time when each element is only a few positions from its target, because the inner \`while\` loop barely moves.

Bubble sort can also approach O(n) with an early-exit check, but insertion sort is usually faster in practice.`

const SEED_AI_MERGE = `Merge sort is divide-and-conquer - O(n log n) guaranteed:

\`\`\`python
def merge_sort(items):
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    left = merge_sort(items[:mid])
    right = merge_sort(items[mid:])
    return merge(left, right)

def merge(left, right):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:]); out.extend(right[j:])
    return out
\`\`\`

It needs O(n) extra space but is stable.`

const SEED_AI_QUICK = `Quicksort partitions around a pivot and recurses - O(n log n) average, O(n²) worst case:

\`\`\`python
def quicksort(items):
    if len(items) <= 1:
        return items
    pivot = items[len(items) // 2]
    less = [x for x in items if x < pivot]
    equal = [x for x in items if x == pivot]
    greater = [x for x in items if x > pivot]
    return quicksort(less) + equal + quicksort(greater)
\`\`\`

This version is concise but not in-place; in-place variants are more memory-efficient.`

const SEED_MESSAGES: Message[] = [
  { id: 'seed-human-1', type: 'human', content: 'Bubble sort algorithm in Python', timestamp: new Date() },
  { id: 'seed-ai-1', type: 'ai', content: SEED_AI_BUBBLE, timestamp: new Date() },
  { id: 'seed-human-2', type: 'human', content: 'How does selection sort differ?', timestamp: new Date() },
  { id: 'seed-ai-2', type: 'ai', content: SEED_AI_SELECTION, timestamp: new Date() },
  { id: 'seed-human-3', type: 'human', content: 'What about insertion sort?', timestamp: new Date() },
  { id: 'seed-ai-3', type: 'ai', content: SEED_AI_INSERTION, timestamp: new Date() },
  { id: 'seed-human-4', type: 'human', content: 'Which is best for nearly-sorted data?', timestamp: new Date() },
  { id: 'seed-ai-4', type: 'ai', content: SEED_AI_NEARLY, timestamp: new Date() },
  { id: 'seed-human-5', type: 'human', content: 'Show me merge sort', timestamp: new Date() },
  { id: 'seed-ai-5', type: 'ai', content: SEED_AI_MERGE, timestamp: new Date() },
  { id: 'seed-human-6', type: 'human', content: 'And quicksort?', timestamp: new Date() },
  { id: 'seed-ai-6', type: 'ai', content: SEED_AI_QUICK, timestamp: new Date() },
]

export function ChatMessagesView() {
  const [messages] = useState<Message[]>(() => SEED_MESSAGES)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMessageId(messageId)
      setTimeout(() => {
        setCopiedMessageId(null)
      }, 2000) // Reset after 2 seconds
    } catch {
      // Clipboard unavailable (e.g. insecure context) - copy silently fails.
    }
  }

  return (
    <div className='mx-auto max-w-4xl space-y-2 p-4 pb-28 md:p-6'>
      {messages.map((message, index) =>
        message.type === 'human' ? (
          <HumanMessageBubble key={message.id ?? `msg-${index}`} message={message} />
        ) : (
          <AiMessageBubble
            key={message.id ?? `msg-${index}`}
            message={message}
            handleCopy={handleCopy}
            copiedMessageId={copiedMessageId}
          />
        )
      )}
    </div>
  )
}
