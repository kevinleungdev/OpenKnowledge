import * as React from 'react'
import { useIsCompact } from '../hooks/use-is-compact'

type PlaygroundContextType = {
  /** Whether the Run Settings panel is open (inline when wide, overlay when narrow). */
  runSettingsOpen: boolean
  setRunSettingsOpen: React.Dispatch<React.SetStateAction<boolean>>
  /** True when the Main column is too narrow for Run Settings to sit inline. */
  isCompact: boolean
  /** Ref attached to the measured layout container (the two-column flex). */
  containerRef: React.RefObject<HTMLDivElement | null>
  /** The editable Chat panel title. */
  title: string
  setTitle: React.Dispatch<React.SetStateAction<string>>
}

const PlaygroundContext = React.createContext<PlaygroundContextType | null>(null)

export const DEFAULT_TITLE = 'Untitled prompt'

export function PlaygroundProvider({ children }: { children: React.ReactNode }) {
  const [runSettingsOpen, setRunSettingsOpen] = React.useState(true)
  const [title, setTitle] = React.useState(DEFAULT_TITLE)

  const [containerRef, isCompact] = useIsCompact<HTMLDivElement>({
    // Crossing into narrow territory forces Run Settings closed so it never gets
    // crushed into the Chat column - reopening happens as an overlay (Q3). Fired
    // from the ResizeObserver callback, not a React effect.
    onChange: (compact) => {
      if (compact) setRunSettingsOpen(false)
    },
  })

  return (
    <PlaygroundContext
      value={{ runSettingsOpen, setRunSettingsOpen, isCompact, containerRef, title, setTitle }}
    >
      {children}
    </PlaygroundContext>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const usePlayground = () => {
  const playgroundContext = React.useContext(PlaygroundContext)

  if (!playgroundContext) {
    throw new Error('usePlayground has to be used within <PlaygroundContext>')
  }

  return playgroundContext
}
