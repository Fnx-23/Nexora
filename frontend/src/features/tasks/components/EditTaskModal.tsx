import { useState, useEffect } from "react"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Modal } from "@/components/ui/Modal"
import type { Task, TaskPriority, TaskStatus } from "@/types/task"
import { updateTask, deleteTask } from "@/features/tasks/api"
import type { Project } from "@/types/project"
import type { Member } from "@/types/team"

interface EditTaskModalProps {
  open: boolean
  task: Task | null
  onClose: () => void
  onUpdated: () => void
  onDeleted: () => void
  projects: Project[]
  members: Member[]
  canDelete: boolean
}

const PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "URGENT", label: "Urgent" },
]

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: "TODO", label: "To Do" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "IN_REVIEW", label: "In Review" },
  { value: "DONE", label: "Done" },
  { value: "CANCELLED", label: "Cancelled" },
]

export function EditTaskModal({
  open,
  task,
  onClose,
  onUpdated,
  onDeleted,
  projects,
  members,
  canDelete,
}: EditTaskModalProps) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    project: null as string | null,
    status: "TODO" as string,
    priority: "MEDIUM" as string,
    assignee: null as string | null,
    due_date: null as string | null,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [globalError, setGlobalError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (task && open) {
      setForm({
        title: task.title,
        description: task.description,
        project: task.project,
        status: task.status,
        priority: task.priority,
        assignee: task.assignee,
        due_date: task.due_date,
      })
      setErrors({})
      setGlobalError(null)
      setConfirmDelete(false)
    }
  }, [task, open])

  function handleClose() {
    setConfirmDelete(false)
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!task) return
    setErrors({})
    setGlobalError(null)

    if (!form.title.trim()) {
      setErrors({ title: "Title is required." })
      return
    }

    setSubmitting(true)
    try {
      await updateTask(task.id, form)
      onUpdated()
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: Record<string, unknown> }
      }
      const data = error.response?.data
      if (data && typeof data === "object") {
        const fieldErrors: Record<string, string> = {}
        for (const [key, val] of Object.entries(data)) {
          if (key === "detail") setGlobalError(String(val))
          else if (Array.isArray(val)) fieldErrors[key] = val.join(" ")
          else if (typeof val === "string") fieldErrors[key] = val
        }
        if (Object.keys(fieldErrors).length) setErrors(fieldErrors)
      } else {
        setGlobalError("An unexpected error occurred.")
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete() {
    if (!task) return
    setDeleting(true)
    try {
      await deleteTask(task.id)
      setConfirmDelete(false)
      onDeleted()
    } catch {
      setGlobalError("Failed to delete task.")
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Edit task"
      size="lg"
      footer={
        <>
          {canDelete && !confirmDelete && (
            <Button
              variant="danger"
              onClick={() => setConfirmDelete(true)}
              className="mr-auto"
            >
              Delete
            </Button>
          )}
          {confirmDelete && (
            <div className="mr-auto flex items-center gap-2">
              <span className="text-sm text-surface-600">Confirm?</span>
              <Button
                variant="danger"
                isLoading={deleting}
                onClick={handleDelete}
              >
                Yes, delete
              </Button>
              <Button
                variant="secondary"
                onClick={() => setConfirmDelete(false)}
              >
                No
              </Button>
            </div>
          )}
          <Button variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            form="edit-task-form"
            isLoading={submitting}
          >
            Save changes
          </Button>
        </>
      }
    >
      <form id="edit-task-form" onSubmit={handleSubmit} className="space-y-4">
        {globalError && (
          <div
            role="alert"
            className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {globalError}
          </div>
        )}

        <Input
          label="Title"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          error={errors.title}
          required
        />

        <div>
          <label
            htmlFor="edit-task-desc"
            className="mb-1.5 block text-sm font-medium text-surface-700"
          >
            Description
          </label>
          <textarea
            id="edit-task-desc"
            rows={3}
            value={form.description}
            onChange={(e) =>
              setForm((f) => ({ ...f, description: e.target.value }))
            }
            className="block w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-surface-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-0"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Project"
            value={form.project ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, project: e.target.value || null }))
            }
          >
            <option value="">No project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>

          <Select
            label="Assignee"
            value={form.assignee ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, assignee: e.target.value || null }))
            }
          >
            <option value="">Unassigned</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.full_name || m.email}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Select
            label="Priority"
            value={form.priority}
            onChange={(e) =>
              setForm((f) => ({ ...f, priority: e.target.value }))
            }
            error={errors.priority}
          >
            {PRIORITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>

          <Select
            label="Status"
            value={form.status}
            onChange={(e) =>
              setForm((f) => ({ ...f, status: e.target.value }))
            }
            error={errors.status}
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>

          <Input
            label="Due date"
            type="date"
            value={form.due_date ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, due_date: e.target.value || null }))
            }
          />
        </div>
      </form>
    </Modal>
  )
}
