import { useEffect } from "react"

import { Button } from "@/components/ui/Button"
import { Modal } from "@/components/ui/Modal"

export interface ConfirmDialogProps {
  open: boolean
  onConfirm: () => void
  onCancel: () => void
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: "danger" | "primary"
  isLoading?: boolean
}

export function ConfirmDialog({
  open,
  onConfirm,
  onCancel,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault()
        if (!isLoading) onConfirm()
      }
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [open, isLoading, onConfirm])

  return (
    <Modal open={open} onClose={onCancel} title={title} description={description} size="sm">
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel} disabled={isLoading}>
          {cancelLabel}
        </Button>
        <Button
          variant={variant}
          onClick={onConfirm}
          isLoading={isLoading}
          disabled={isLoading}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}