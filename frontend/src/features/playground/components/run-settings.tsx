import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { CircleX } from 'lucide-react'
import { mutedIconButtonClass } from './constants'
import { usePlayground } from './playground-provider'

/**
 * Run Settings panel - configures a future Run. Body is intentionally empty at
 * this stage. `className` controls how it sits in the layout: inline as the 1/4
 * column when wide, or an absolute overlay when narrow (decided by the caller).
 */
export function RunSettings({ className }: { className?: string }) {
  const { setRunSettingsOpen } = usePlayground()

  return (
    <div className={cn('flex flex-col rounded-lg border bg-background', className)}>
      <header className='flex items-center justify-between border-b p-3'>
        <h2 className='text-sm font-semibold'>Run Settings</h2>
        <Button
          type='button'
          variant='ghost'
          size='icon'
          className={mutedIconButtonClass}
          onClick={() => setRunSettingsOpen(false)}
          aria-label='Close run settings'
        >
          <CircleX className='size-4' />
        </Button>
      </header>
      {/* Body intentionally empty - populated when Run settings are defined. */}
      <div className='min-h-0 flex-1' />
    </div>
  )
}
