import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useState } from 'react'

/**
 * Static authoring input. The only action is a disabled Run (the execution
 * pipeline isn't built yet - see ADR-0001). Ctrl+Enter is a no-op: with Run
 * disabled there is nothing to fire, so no key handler is wired.
 */
export const ChatInput: React.FC = () => {
  const [value, setValue] = useState('')

  return (
    <div className='flex flex-row items-center gap-2 rounded-3xl bg-muted px-4 py-3 wrap-break-word'>
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder='Bubble sort algorithm in Python'
        className='min-h-7 max-h-50 w-full resize-none border-0 bg-transparent p-0 text-foreground shadow-none outline-none focus-visible:border-0 focus-visible:ring-0 placeholder:text-muted-foreground md:text-base'
        rows={1}
      />
      <Button type='button' disabled className='shrink-0 gap-1.5'>
        Run
        <kbd className='pointer-events-none h-5 select-none rounded border bg-background px-1 font-mono text-[10px] font-medium text-muted-foreground'>
          Ctrl ↵
        </kbd>
      </Button>
    </div>
  )
}
