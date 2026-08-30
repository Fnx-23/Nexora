import { useEffect, useId, useRef, type HTMLAttributes, type ReactNode } from "react"
import { createPortal } from "react-dom"

import { XIcon } from "@/components/icons"
import { cn } from "@/utils/cn"

type ModalSize = "sm" | "md" | "lg"

const sizeClasses: Record<ModalSize, string> = {
  sm: "max-w-md",
  md: "max-w-xl",
  lg: "max-w-3xl",
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
    // Move initial focus into the dialog so screen readers announce the label.
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
      // Restore focus to the element that was focused before the dialog opened.
      previouslyFocused.current?.focus()
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        role="presentation"
        className="absolute inset-0 bg-slate-900/50"
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
        <div className="flex items-start justify-between px-6 pt-6 pb-3">
          <div>
            {title && (
              <h2 id={titleId} className="text-lg font-semibold text-slate-900">
                {title}
              </h2>
            )}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          >
            <XIcon className="size-5" />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
        {footer && (
          <div className="flex justify-end gap-3 border-t border-slate-100 px-6 py-5">{footer}</div>
        )}
      </div>
    </div>,
    document.body,
  )
}
