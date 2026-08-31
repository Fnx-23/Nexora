import { useEffect, useId, useRef, type HTMLAttributes, type ReactNode } from "react"
import { createPortal } from "react-dom"

import { XIcon } from "@/components/icons"
import { cn } from "@/utils/cn"

type ModalSize = "sm" | "md" | "lg"

const sizeClasses: Record<ModalSize, string> = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
}

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

export interface ModalProps extends HTMLAttributes<HTMLDivElement> {
  open: boolean
  onClose: () => void
  title?: string
  description?: string
  size?: ModalSize
  footer?: ReactNode
}

export function Modal({
  open,
  onClose,
  title,
  description,
  size = "md",
  footer,
  children,
  className,
}: ModalProps) {
  const titleId = useId()
  const dialogRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!open) return

    previouslyFocused.current = document.activeElement as HTMLElement | null
    dialogRef.current?.focus()

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose()
        return
      }
      if (event.key === "Tab") {
        trapFocus(event)
      }
    }

    function trapFocus(event: KeyboardEvent) {
      const focusable = dialogRef.current
        ? Array.from(dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE))
        : []
      if (!focusable.length) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener("keydown", onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      document.removeEventListener("keydown", onKeyDown)
      document.body.style.overflow = previousOverflow
      previouslyFocused.current?.focus()
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        role="presentation"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-label={title ? undefined : "Dialog"}
        tabIndex={-1}
        className={cn(
          "relative w-full rounded-xl bg-white shadow-xl outline-none",
          sizeClasses[size],
          className,
        )}
      >
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-4">
          <div>
            {title && (
              <h2 id={titleId} className="text-base font-semibold text-slate-900">
                {title}
              </h2>
            )}
            {description && <p className="mt-0.5 text-sm text-slate-500">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          >
            <XIcon className="size-4" />
          </button>
        </div>
        <div className="px-6 py-4">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-slate-100 px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}
