import { useEffect, type RefObject } from "react"

export function useClickOutside<T extends HTMLElement>(
  ref: RefObject<T | null>,
  handler: () => void,
  enabled = true,
): void {
  useEffect(() => {
    if (!enabled) return

    function listener(event: MouseEvent | TouchEvent) {
      const element = ref.current
      if (!element || element.contains(event.target as Node)) return
      handler()
    }

    document.addEventListener("mousedown", listener)
    document.addEventListener("touchstart", listener)
    return () => {
      document.removeEventListener("mousedown", listener)
      document.removeEventListener("touchstart", listener)
    }
  }, [ref, handler, enabled])
}
