import { useState } from "react"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Modal } from "@/components/ui/Modal"
import type { TaskPriority } from "@/types/task"
import { createTask, type CreateTaskPayload } from "@/features/tasks/api"
import type { Project } from "@/types/project"
import type { Member } from "@/types/team"

interface CreateTaskModalProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
  projects: Project[]
  members: Member[]
}

const PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "URGENT", label: "Urgent" },
]

export function CreateTaskModal({
  open,
  onClose,
  onCreated,
  projects,
  members,
}: CreateTaskModalProps) {
  const [form, setForm] = useState<CreateTaskPayload>({
    title: "",
    description: "",
    project: null,
    status: "TODO",
    priority: "MEDIUM",
    assignee: null,
    due_date: null,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [globalError, setGlobalError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function reset() {
    setForm({
      title: "",
      description: "",
      project: null,
      status: "TODO",
      priority: "MEDIUM",
      assignee: null,
      due_date: null,
    })
    setErrors({})
    setGlobalError(null)
  }

  function handleClose() {
    reset()
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErrors({})
    setGlobalError(null)

    if (!form.title.trim()) {
      setErrors({ title: "Title is required." })
      return
    }

    setSubmitting(true)
    try {
      await createTask(form)
      reset()
      onCreated()
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

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Create task"
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            form="create-task-form"
            isLoading={submitting}
          >
            Create task
          </Button>
        </>
      }
    >
      <form id="create-task-form" onSubmit={handleSubmit} className="space-y-4">
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
          placeholder="What needs to be done?"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          error={errors.title}
          required
        />

        <div>
          <label
            htmlFor="task-desc"
            className="mb-1.5 block text-sm font-medium text-surface-700"
          >
            Description
          </label>
          <textarea
            id="task-desc"
            rows={3}
            placeholder="Add more detail..."
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
            <option value="TODO">To Do</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="IN_REVIEW">In Review</option>
            <option value="DONE">Done</option>
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
