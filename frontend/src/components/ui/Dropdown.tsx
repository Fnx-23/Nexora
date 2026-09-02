import { useEffect, useId, useRef, useState } from "react"
import { createPortal } from "react-dom"

import { cn } from "@/utils/cn"

export interface DropdownProps {
  trigger: (props: {
    toggle: () => void
    triggerProps: {
      onClick: () => void
      "aria-expanded"?: boolean
      "aria-haspopup"?: "menu"
    }
  }) => React.ReactNode
  children: React.ReactNode
}

export function Dropdown({ trigger, children }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const id = useId()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node
      if (
        containerRef.current &&
        !containerRef.current.contains(target) &&
        (!menuRef.current || !menuRef.current.contains(target))
      ) {
        setOpen(false)
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false)
        return
      }
      if (event.key === "ArrowDown" && !open) {
        event.preventDefault()
        setOpen(true)
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [open])

  return (
    <div ref={containerRef} className="relative inline-flex">
      {trigger({
        toggle: () => setOpen((v) => !v),
        triggerProps: {
          onClick: () => setOpen((v) => !v),
          "aria-expanded": open,
          "aria-haspopup": "menu" as const,
        },
      })}
      {open &&
        createPortal(
          <div
            ref={menuRef}
            id={id}
            role="menu"
            aria-expanded="true"
            onClick={() => setOpen(false)}
            className={cn(
              "absolute right-0 z-50 mt-2 min-w-[180px] rounded-lg border border-slate-200 bg-white py-1 shadow-lg",
            )}
          >
            {children}
          </div>,
          document.body,
        )}
    </div>
  )
}

export function DropdownLabel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-3 py-2", className)} {...props} />
}

export function DropdownItem({
  className,
  danger,
  onClick,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { danger?: boolean }) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2.5 px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50",
        danger && "text-red-600 hover:bg-red-50",
        className,
      )}
      {...props}
    />
  )
}

export function DropdownSeparator() {
  return <div className="my-1 border-t border-slate-100" />
}
