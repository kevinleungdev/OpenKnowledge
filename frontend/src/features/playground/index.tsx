import { Main } from '@/components/layout/main'
import { ChatPanel } from './components/chat-panel'
import { PlaygroundProvider, usePlayground } from './components/playground-provider'
import { RunSettings } from './components/run-settings'

export function Playground() {
  return (
    <Main fixed className='p-3'>
      <PlaygroundProvider>
        <PlaygroundContent />
      </PlaygroundProvider>
    </Main>
  )
}

/**
 * Two-column layout: Chat 3 : Run Settings 1. The container ref is observed by
 * the provider to decide compactness. Run Settings sits inline as the 1/4 column
 * when wide; when narrow it opens as a right-aligned overlay over the Chat
 * (never pushing the Chat below 3:1).
 */
function PlaygroundContent() {
  const { containerRef, isCompact, runSettingsOpen } = usePlayground()

  return (
    <div ref={containerRef} className='relative flex min-h-0 flex-1 gap-4'>
      <ChatPanel className='min-w-0 flex-[3_1_0%]' />
      {runSettingsOpen && (
        <RunSettings
          className={
            isCompact
              ? 'absolute right-0 top-0 z-20 h-full w-80 shadow-lg'
              : 'min-w-0 flex-[1_1_0%]'
          }
        />
      )}
    </div>
  )
}
