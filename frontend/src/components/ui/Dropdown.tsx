import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type ReactNode,
} from "react"

import { useClickOutside } from "@/hooks/useClickOutside"
import { cn } from "@/utils/cn"

interface DropdownContextValue {
  close: () => void
}

const DropdownContext = createContext<DropdownContextValue | null>(null)

/** Props the trigger element must spread to stay accessible. */
export interface DropdownTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  ref: (node: HTMLButtonElement | null) => void
}

export interface DropdownProps {
  /**
   * Renders the menu button. Spread `triggerProps` onto it so the component
   * can manage `aria-expanded`, `aria-haspopup`, keyboard activation and
   * focus restoration.
   */
  trigger: (props: { open: boolean; toggle: () => void; triggerProps: DropdownTriggerProps }) => ReactNode
  children: ReactNode
  align?: "left" | "right"
  menuClassName?: string
}

const MENU_KEYS = new Set(["ArrowDown", "ArrowUp", "Home", "End"])

/**
 * Headless dropdown following the WAI-ARIA menu-button pattern:
 * - trigger carries `aria-expanded` / `aria-haspopup` and is focused again on close
 * - opening moves focus to the first item; ArrowUp/Down/Home/End move within
 * - Escape closes and restores focus; Tab simply closes
 *
 * Panel items should call `useDropdown().close()` after acting.
 */
export function Dropdown({ trigger, children, align = "right", menuClassName }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  // Whether the menu was opened through the keyboard; drives initial focus.
  const openedViaKeyboard = useRef(false)

  useClickOutside(containerRef, () => setOpen(false), open)

  const close = useCallback(() => setOpen(false), [])

  useEffect(() => {
    if (!open) return

    function focusMenuItem(index: number) {
      const items = menuItems()
      if (!items.length) return
      items[Math.max(0, Math.min(index, items.length - 1))].focus()
    }

    function menuItems(): HTMLElement[] {
      return Array.from(
        menuRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]:not([disabled])') ?? [],
      )
    }

    if (openedViaKeyboard.current) {
      focusMenuItem(0)
    }

    function onMenuKeyDown(event: KeyboardEvent) {
      const items = menuItems()
      const currentIndex = items.findIndex((item) => item === document.activeElement)

      switch (event.key) {
        case "ArrowDown":
          event.preventDefault()
          focusMenuItem(currentIndex + 1)
          break
        case "ArrowUp":
          event.preventDefault()
          focusMenuItem(currentIndex <= 0 ? items.length - 1 : currentIndex - 1)
          break
        case "Home":
          event.preventDefault()
          focusMenuItem(0)
          break
        case "End":
          event.preventDefault()
          focusMenuItem(items.length - 1)
          break
        case "Tab":
          // Menus are transient: leaving with Tab closes without trapping.
          setOpen(false)
          break
      }
    }

    const menu = menuRef.current
    menu?.addEventListener("keydown", onMenuKeyDown)
    return () => menu?.removeEventListener("keydown", onMenuKeyDown)
  }, [open])

  // Escape must also be catchable when focus is outside the menu (e.g. trigger).
  useEffect(() => {
    if (!open) return
    function onDocumentKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.stopPropagation()
        setOpen(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener("keydown", onDocumentKeyDown, true)
    return () => document.removeEventListener("keydown", onDocumentKeyDown, true)
  }, [open])

  // Restore focus when closed by any means other than a pointer press that
  // already moved focus elsewhere (outside click, item action, Escape).
  useEffect(() => {
    if (open) return
    const container = containerRef.current
    if (
      document.activeElement &&
      document.activeElement !== document.body &&
      (!container || !container.contains(document.activeElement))
    ) {
      return
    }
    if (document.activeElement === triggerRef.current) return
    triggerRef.current?.focus()
  }, [open])

  const setTriggerRef = useCallback((node: HTMLButtonElement | null) => {
    triggerRef.current = node
  }, [])

  const contextValue = useMemo<DropdownContextValue>(() => ({ close }), [close])

  const toggle = useCallback(() => setOpen((value) => !value), [])

  const triggerProps = useMemo<DropdownTriggerProps>(
    () => ({
      ref: setTriggerRef,
      onClick: toggle,
      onKeyDown: (event) => {
        if (event.key === "ArrowDown" && !open) {
          event.preventDefault()
          openedViaKeyboard.current = true
          setOpen(true)
          return
        }
        if (MENU_KEYS.has(event.key)) {
          event.preventDefault()
        }
      },
      "aria-expanded": open,
      "aria-haspopup": "menu",
    }),
    [open, setTriggerRef, toggle],
  )

  return (
    <div ref={containerRef} className="relative inline-block">
      {trigger({ open, toggle, triggerProps })}
      {open && (
        <DropdownContext.Provider value={contextValue}>
          <div
            ref={menuRef}
            role="menu"
            tabIndex={-1}
            className={cn(
              "absolute z-40 mt-2 w-52 rounded-lg border border-slate-200 bg-white py-1 shadow-lg",
              align === "right" ? "right-0" : "left-0",
              menuClassName,
            )}
          >
            {children}
          </div>
        </DropdownContext.Provider>
      )}
    </div>
  )
}

export interface DropdownItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  danger?: boolean
}

export function DropdownItem({ danger, className, onClick, ...props }: DropdownItemProps) {
  const context = useContext(DropdownContext)
  return (
    <button
      type="button"
      role="menuitem"
      onClick={(event) => {
        context?.close()
        onClick?.(event)
      }}
      className={cn(
        "flex w-full items-center gap-2.5 px-4 py-2 text-left text-sm transition-colors",
        danger ? "text-red-600 hover:bg-red-50" : "text-slate-700 hover:bg-slate-50 hover:text-slate-900",
        className,
      )}
      {...props}
    />
  )
}

export function DropdownSeparator() {
  return <div role="presentation" className="my-1 border-t border-slate-100" />
}

export function DropdownLabel({ children }: { children: ReactNode }) {
  return <div className="truncate px-4 pt-2 pb-1 text-xs font-medium text-slate-400">{children}</div>
}
