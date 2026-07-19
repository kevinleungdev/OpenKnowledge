import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { cn } from '@/lib/utils'
import { Pencil, SlidersHorizontal } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { ChatInput } from './chat-input'
import { ChatMessagesView } from './chat-message'
import { mutedIconButtonClass } from './constants'
import { DEFAULT_TITLE, usePlayground } from './playground-provider'

/** Click-to-edit Chat panel title. Enter/blur commits, Escape cancels; an empty commit reverts to the default. */
function EditableTitle() {
  const { title, setTitle } = usePlayground()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  const startEdit = () => {
    setDraft(title)
    setEditing(true)
  }

  const commit = () => {
    const next = draft.trim() === '' ? DEFAULT_TITLE : draft
    setTitle(next)
    setEditing(false)
  }

  const cancel = () => {
    setEditing(false)
  }

  if (editing) {
    return (
      <Input
        ref={inputRef}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            commit()
          } else if (e.key === 'Escape') {
            e.preventDefault()
            cancel()
          }
        }}
        onBlur={commit}
        className='h-9 w-64 text-lg'
      />
    )
  }

  return (
    <button
      type='button'
      onClick={startEdit}
      className='flex items-center gap-1.5 text-lg font-semibold text-foreground hover:text-primary'
    >
      {title}
      <Pencil className='size-4 text-muted-foreground' />
    </button>
  )
}

/**
 * Chat panel - composes the editable title + Run Settings toggle header, a
 * scrollable message list (invisible scrollbar), and an absolutely positioned
 * ChatInput centered at the bottom.
 */
export function ChatPanel({ className }: { className?: string }) {
  const { runSettingsOpen, setRunSettingsOpen } = usePlayground()

  return (
    <div className={cn('relative flex flex-col', className)}>
      {/* Header: editable title (left) + Run Settings toggle (right, hidden when open) */}
      <div className='flex items-center justify-between px-2 py-3'>
        <div className='flex items-center gap-1'>
          {/* Mobile-only sidebar trigger (desktop uses the sidebar-header toggle) */}
          <SidebarTrigger className={cn(mutedIconButtonClass, 'md:hidden')} />
          <EditableTitle />
        </div>
        {!runSettingsOpen && (
          <Button
            type='button'
            variant='ghost'
            size='icon'
            className={cn(mutedIconButtonClass, 'size-8')}
            onClick={() => setRunSettingsOpen(true)}
            aria-label='Open run settings'
          >
            <SlidersHorizontal className='size-5' />
          </Button>
        )}
      </div>

      {/* Scrollable message list - plain div with hidden scrollbar (no radix ScrollArea) */}
      <div className='relative min-h-0 flex-1 overflow-y-auto scrollbar-none [&::-webkit-scrollbar]:hidden'>
        <ChatMessagesView />
      </div>

      {/* Absolute, bottom-centered input bar */}
      <div className='absolute bottom-0 left-1/2 w-full max-w-4xl -translate-x-1/2 px-4 pb-4'>
        <ChatInput />
      </div>
    </div>
  )
}
