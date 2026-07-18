import * as React from 'react'

// Main content width below which the Run Settings panel can no longer sit
// inline beside the Chat (3:1) and must collapse to an overlay.
const COMPACT_THRESHOLD_REM = 64

/**
 * Container-query-style compactness check: observes an element's width with a
 * ResizeObserver rather than the viewport, so "not enough room" reacts to the
 * sidebar opening/closing (which changes the Main column width, not the window).
 *
 * Returns a ref to attach to the observed element and a boolean that is `true`
 * once the element is narrower than the threshold. The first measurement is read
 * synchronously in a layout effect (before paint) so the first render matches
 * the real width - no flash of the wrong state on a narrow viewport at load -
 * and subsequent changes are tracked by the ResizeObserver.
 *
 * `onChange` fires from that initial measurement and on each transition; use it
 * to react (e.g. auto-collapse) without wiring a setState-in-effect yourself.
 */
export function useIsCompact<T extends HTMLElement>(options?: {
  onChange?: (isCompact: boolean) => void
}) {
  const ref = React.useRef<T | null>(null)
  const [isCompact, setIsCompact] = React.useState(false)

  // Keep the latest onChange in a ref so the observer (created once) always
  // calls the current callback without needing it as a dependency.
  const onChangeRef = React.useRef(options?.onChange)
  React.useEffect(() => {
    onChangeRef.current = options?.onChange
  })

  React.useLayoutEffect(() => {
    const el = ref.current
    if (!el) return

    const measure = (width: number) => width < COMPACT_THRESHOLD_REM * 16
    // Read synchronously before paint so the first render matches the real
    // width (no flash of the wrong state on a narrow viewport at load).
    let prev = measure(el.getBoundingClientRect().width)
    setIsCompact(prev)
    onChangeRef.current?.(prev)

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (!entry) return
      const next = measure(entry.contentRect.width)
      if (next !== prev) {
        prev = next
        setIsCompact(next)
        onChangeRef.current?.(next)
      }
    })
    observer.observe(el)

    return () => observer.disconnect()
  }, [])

  return [ref, isCompact] as const
}
