import { useCallback, useState, type FormEvent, type ReactNode } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { DocumentManager } from "@/components/DocumentManager"
import { Avatar } from "@/components/ui/Avatar"
import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Modal } from "@/components/ui/Modal"
import { StatusBadge } from "@/components/ui/Badge"
import { ErrorState } from "@/components/ui/ErrorState"
import { LoadingState } from "@/components/ui/LoadingState"
import { EmptyState } from "@/components/ui/EmptyState"
import {
  ActivityIcon,
  CheckSquareIcon,
  InboxIcon,
  ListChecksIcon,
  MessageSquareIcon,
  FolderIcon,
  TrashIcon,
} from "@/components/icons"
import { ActivityRow } from "@/features/activity/ActivityRow"
import { useAuth } from "@/hooks/useAuth"
import {
  addTaskChecklistItem,
  addTaskComment,
  addTaskSubtask,
  deleteTask,
  deleteTaskChecklistItem,
  deleteTaskComment,
  deleteTaskSubtask,
  fetchLabels,
  fetchTask,
  fetchTaskChecklist,
  fetchTaskComments,
  fetchTaskSubtasks,
  updateTask,
  updateTaskChecklistItem,
  updateTaskComment,
  updateTaskSubtask,
  type CreateTaskPayload,
} from "@/features/tasks/api"
import { fetchProjects } from "@/features/projects/api"
import { fetchMembers } from "@/features/team/api"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"
import type {
  TaskChecklistItem,
  TaskDetail,
  TaskLabel,
  TaskSubtask,
} from "@/types/task"

const STATUS_OPTIONS = ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE", "CANCELLED"]
const PRIORITY_OPTIONS = ["LOW", "MEDIUM", "HIGH", "URGENT"]

type TabKey = "overview" | "checklist" | "subtasks" | "comments" | "attachments" | "activity"

const TABS: { key: TabKey; label: string; icon: typeof InboxIcon }[] = [
  { key: "overview", label: "Overview", icon: InboxIcon },
  { key: "checklist", label: "Checklist", icon: CheckSquareIcon },
  { key: "subtasks", label: "Subtasks", icon: ListChecksIcon },
  { key: "comments", label: "Comments", icon: MessageSquareIcon },
  { key: "attachments", label: "Attachments", icon: FolderIcon },
  { key: "activity", label: "Activity", icon: ActivityIcon },
]

function formatDate(iso: string | null) {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function formatTime(iso: string) {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function InfoRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline">
      <span className="w-32 shrink-0 text-sm font-medium text-slate-500">{label}</span>
      <span className="text-sm text-slate-900">{children}</span>
    </div>
  )
}

function LabelChip({ label }: { label: TaskLabel }) {
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{ backgroundColor: `${label.color}1f`, color: label.color }}
    >
      {label.name}
    </span>
  )
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
}) {
  return (
    <Card className="px-5 py-4">
      <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </Card>
  )
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-brand-600 transition-all"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <div className="mt-1 text-xs text-slate-500">{value}% done</div>
    </div>
  )
}

function OverviewTab({
  task,
  onEdit,
}: {
  task: TaskDetail
  onEdit: () => void
}) {
  const isOverdue =
    task.due_date && new Date(task.due_date) < new Date() && task.status !== "DONE"

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Checklist"
          value={
            <span>
              {task.checklist_done}
              <span className="text-slate-400">/{task.checklist_total}</span>
            </span>
          }
          sub={
            task.checklist_total > 0 ? (
              <ProgressBar value={Math.round((task.checklist_done / task.checklist_total) * 100)} />
            ) : undefined
          }
        />
        <StatCard
          label="Subtasks"
          value={
            <span>
              {task.subtask_done}
              <span className="text-slate-400">/{task.subtask_total}</span>
            </span>
          }
        />
        <StatCard label="Comments" value={task.comments_count} />
        <StatCard
          label="Due date"
          value={<span className={cn(isOverdue && "text-red-600")}>{formatDate(task.due_date)}</span>}
          sub={isOverdue ? <span className="text-xs font-medium text-red-600">Overdue</span> : undefined}
        />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Details</CardTitle>
            <Button size="sm" onClick={onEdit}>
              Edit
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <InfoRow label="Project">{task.project_name || "—"}</InfoRow>
          <InfoRow label="Status">
            <StatusBadge value={task.status} />
          </InfoRow>
          <InfoRow label="Priority">
            <StatusBadge value={task.priority} />
          </InfoRow>
          <InfoRow label="Assignee">
            <span className="flex items-center gap-2">
              {task.assignee_name ? (
                <>
                  <Avatar name={task.assignee_name} size="xs" />
                  {task.assignee_name}
                </>
              ) : (
                "—"
              )}
            </span>
          </InfoRow>
          <InfoRow label="Created by">{task.created_by_name || "—"}</InfoRow>
          {task.labels.length > 0 && (
            <div>
              <InfoRow label="Labels">
                <span className="inline-flex flex-wrap gap-1.5">
                  {task.labels.map((label) => (
                    <LabelChip key={label.id} label={label} />
                  ))}
                </span>
              </InfoRow>
            </div>
          )}
          {task.description && (
            <div className="pt-1">
              <p className="text-sm font-medium text-slate-500">Description</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{task.description}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function ChecklistTab({ taskId }: { taskId: string }) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState("")

  const query = useQuery({
    queryKey: queryKeys.taskChecklist(taskId),
    queryFn: () => fetchTaskChecklist(taskId),
    enabled: taskId !== undefined,
  })

  const refresh = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.taskChecklist(taskId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.task(taskId) })
  }, [queryClient, taskId])

  const addMutation = useMutation({
    mutationFn: (text: string) => addTaskChecklistItem(taskId, text),
    onSuccess: () => {
      setDraft("")
      refresh()
    },
  })
  const toggleMutation = useMutation({
    mutationFn: (item: TaskChecklistItem) =>
      updateTaskChecklistItem(taskId, item.id, { completed: !item.completed }),
    onSuccess: () => refresh(),
  })
  const removeMutation = useMutation({
    mutationFn: (itemId: string) => deleteTaskChecklistItem(taskId, itemId),
    onSuccess: () => refresh(),
  })

  const items = query.data ?? []
  const done = items.filter((i) => i.completed).length

  if (query.isPending) return <LoadingState label="Loading checklist…" />
  if (query.isError)
    return (
      <ErrorState
        title="Could not load checklist"
        description="The checklist could not be loaded."
        onRetry={() => void query.refetch()}
      />
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Checklist {items.length > 0 && <span className="text-slate-400">({done}/{items.length})</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (draft.trim()) addMutation.mutate(draft.trim())
          }}
          className="flex items-center gap-2"
        >
          <Input
            placeholder="Add a checklist item…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" isLoading={addMutation.isPending} disabled={!draft.trim()}>
            Add
          </Button>
        </form>

        {items.length === 0 ? (
          <EmptyState title="No checklist items" description="Break the task down into small checks." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((item) => (
              <li key={item.id} className="group flex items-center gap-3 py-2.5">
                <button
                  type="button"
                  onClick={() => toggleMutation.mutate(item)}
                  aria-pressed={item.completed}
                  aria-label={item.completed ? "Mark as not done" : "Mark as done"}
                  className={cn(
                    "flex size-5 shrink-0 items-center justify-center rounded-md border-2 transition-colors",
                    item.completed ? "border-brand-600 bg-brand-600" : "border-slate-300 bg-white",
                  )}
                >
                  {item.completed && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={3} className="size-3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </button>
                <span
                  className={cn(
                    "min-w-0 flex-1 text-sm",
                    item.completed ? "text-slate-400 line-through" : "text-slate-800",
                  )}
                >
                  {item.text}
                </span>
                <button
                  type="button"
                  onClick={() => removeMutation.mutate(item.id)}
                  title="Delete item"
                  className="rounded-md p-1.5 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <TrashIcon className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function SubtasksTab({ taskId }: { taskId: string }) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState("")

  const query = useQuery({
    queryKey: queryKeys.taskSubtasks(taskId),
    queryFn: () => fetchTaskSubtasks(taskId),
    enabled: taskId !== undefined,
  })

  const refresh = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.taskSubtasks(taskId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.task(taskId) })
  }, [queryClient, taskId])

  const addMutation = useMutation({
    mutationFn: (title: string) => addTaskSubtask(taskId, title),
    onSuccess: () => {
      setDraft("")
      refresh()
    },
  })
  const toggleMutation = useMutation({
    mutationFn: (item: TaskSubtask) =>
      updateTaskSubtask(taskId, item.id, { completed: !item.completed }),
    onSuccess: () => refresh(),
  })
  const removeMutation = useMutation({
    mutationFn: (subtaskId: string) => deleteTaskSubtask(taskId, subtaskId),
    onSuccess: () => refresh(),
  })

  const items = query.data ?? []
  const done = items.filter((i) => i.completed).length

  if (query.isPending) return <LoadingState label="Loading subtasks…" />
  if (query.isError)
    return (
      <ErrorState
        title="Could not load subtasks"
        description="The subtasks could not be loaded."
        onRetry={() => void query.refetch()}
      />
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Subtasks {items.length > 0 && <span className="text-slate-400">({done}/{items.length})</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (draft.trim()) addMutation.mutate(draft.trim())
          }}
          className="flex items-center gap-2"
        >
          <Input
            placeholder="Add a subtask…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" isLoading={addMutation.isPending} disabled={!draft.trim()}>
            Add
          </Button>
        </form>

        {items.length === 0 ? (
          <EmptyState title="No subtasks" description="Break this task into smaller subtasks." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((item) => (
              <li key={item.id} className="group flex items-center gap-3 py-2.5">
                <button
                  type="button"
                  onClick={() => toggleMutation.mutate(item)}
                  aria-pressed={item.completed}
                  aria-label={item.completed ? "Mark as not done" : "Mark as done"}
                  className={cn(
                    "flex size-5 shrink-0 items-center justify-center rounded-md border-2 transition-colors",
                    item.completed ? "border-brand-600 bg-brand-600" : "border-slate-300 bg-white",
                  )}
                >
                  {item.completed && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={3} className="size-3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </button>
                <span
                  className={cn(
                    "min-w-0 flex-1 text-sm",
                    item.completed ? "text-slate-400 line-through" : "text-slate-800",
                  )}
                >
                  {item.title}
                </span>
                <button
                  type="button"
                  onClick={() => removeMutation.mutate(item.id)}
                  title="Delete subtask"
                  className="rounded-md p-1.5 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <TrashIcon className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function CommentsTab({ taskId }: { taskId: string }) {
  const { user, role } = useAuth()
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState("")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingDraft, setEditingDraft] = useState("")

  const canModerate = role === "ADMIN" || role === "MANAGER"

  const query = useQuery({
    queryKey: queryKeys.taskComments(taskId),
    queryFn: () => fetchTaskComments(taskId),
    enabled: taskId !== undefined,
  })

  const refresh = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.taskComments(taskId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.task(taskId) })
  }, [queryClient, taskId])

  const addMutation = useMutation({
    mutationFn: (body: string) => addTaskComment(taskId, body),
    onSuccess: () => {
      setDraft("")
      refresh()
    },
  })
  const editMutation = useMutation({
    mutationFn: ({ commentId, body }: { commentId: string; body: string }) =>
      updateTaskComment(taskId, commentId, body),
    onSuccess: () => {
      setEditingId(null)
      refresh()
    },
  })
  const removeMutation = useMutation({
    mutationFn: (commentId: string) => deleteTaskComment(taskId, commentId),
    onSuccess: () => refresh(),
  })

  const comments = query.data ?? []
  const me = user?.id

  if (query.isPending) return <LoadingState label="Loading comments…" />
  if (query.isError)
    return (
      <ErrorState
        title="Could not load comments"
        description="The comments could not be loaded."
        onRetry={() => void query.refetch()}
      />
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Comments</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (draft.trim()) addMutation.mutate(draft.trim())
          }}
          className="flex items-start gap-2"
        >
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Add a comment…"
            rows={2}
            className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
          <Button type="submit" isLoading={addMutation.isPending} disabled={!draft.trim()}>
            Post
          </Button>
        </form>

        {comments.length === 0 ? (
          <EmptyState title="No comments yet" description="Discuss the task with your team." />
        ) : (
          <ul className="space-y-4">
            {comments.map((comment) => {
              const canEdit = comment.author === me || canModerate
              const isEditing = editingId === comment.id
              return (
                <li key={comment.id} className="flex gap-3">
                  <Avatar name={comment.author_name ?? "?"} size="sm" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-slate-900">
                        {comment.author_name ?? "Unknown"}
                      </p>
                      <span className="text-xs text-slate-400">
                        <time dateTime={comment.created_at}>{formatTime(comment.created_at)}</time>
                      </span>
                    </div>
                    {isEditing ? (
                      <div className="mt-1.5 space-y-2">
                        <textarea
                          value={editingDraft}
                          onChange={(e) => setEditingDraft(e.target.value)}
                          rows={2}
                          autoFocus
                          className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            isLoading={editMutation.isPending}
                            onClick={() => {
                              if (editingDraft.trim())
                                editMutation.mutate({
                                  commentId: comment.id,
                                  body: editingDraft.trim(),
                                })
                            }}
                          >
                            Save
                          </Button>
                          <Button size="sm" variant="secondary" onClick={() => setEditingId(null)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <p className="mt-0.5 whitespace-pre-wrap text-sm text-slate-700">
                        {comment.body}
                      </p>
                    )}
                    {canEdit && !isEditing && (
                      <div className="mt-1 flex gap-2 text-xs">
                        <button
                          type="button"
                          className="font-medium text-slate-400 hover:text-slate-700"
                          onClick={() => {
                            setEditingId(comment.id)
                            setEditingDraft(comment.body)
                          }}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="font-medium text-slate-400 hover:text-red-600"
                          onClick={() => removeMutation.mutate(comment.id)}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function ActivityTab({ task }: { task: TaskDetail }) {
  const activities = task.recent_activity ?? []
  if (activities.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState title="No activity yet" description="Changes to this task will show up here." />
        </CardContent>
      </Card>
    )
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent activity</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-4">
          {activities.map((activity) => (
            <ActivityRow key={activity.id} activity={activity} />
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

export function TaskDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { activeCompany, role } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const canDelete = role === "ADMIN" || role === "MANAGER"

  const [activeTab, setActiveTab] = useState<TabKey>("overview")
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [form, setForm] = useState<Partial<CreateTaskPayload>>({})
  const [labelSelection, setLabelSelection] = useState<string[]>([])
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formGlobalError, setFormGlobalError] = useState<string | null>(null)

  const taskQuery = useQuery({
    queryKey: queryKeys.task(id!),
    queryFn: () => fetchTask(id!),
    enabled: id !== undefined,
  })

  const projectsQuery = useQuery({
    queryKey: queryKeys.projects(companyId),
    queryFn: () => fetchProjects({ page_size: 100 }),
    enabled: companyId !== null && editOpen,
  })

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null && editOpen,
  })

  const labelsQuery = useQuery({
    queryKey: queryKeys.labels(companyId),
    queryFn: () => fetchLabels({ page_size: 100 }),
    enabled: companyId !== null && editOpen,
  })

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.tasks(companyId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.task(id!) })
  }, [queryClient, companyId, id])

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<CreateTaskPayload>) => updateTask(id!, payload),
    onSuccess: () => {
      invalidate()
      setEditOpen(false)
    },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) =>
      handleMutationError(err),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTask,
    onSuccess: () => {
      const key = queryKeys.task(id!)
      void queryClient.cancelQueries({ queryKey: key })
      queryClient.removeQueries({ queryKey: key })
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks(companyId) })
      navigate("/tasks")
    },
  })

  function handleMutationError(err: Error & { response?: { data?: Record<string, unknown> } }) {
    const data = err.response?.data
    if (data && typeof data === "object") {
      const fieldErrors: Record<string, string> = {}
      for (const [key, val] of Object.entries(data)) {
        if (key === "detail") setFormGlobalError(String(val))
        else if (Array.isArray(val)) fieldErrors[key] = val.join(" ")
        else if (typeof val === "string") fieldErrors[key] = val
      }
      if (Object.keys(fieldErrors).length) setFormErrors(fieldErrors)
    } else {
      setFormGlobalError("An unexpected error occurred.")
    }
  }

  const task = taskQuery.data

  function openEdit() {
    if (!task) return
    setForm({
      title: task.title,
      description: task.description,
      project: task.project,
      status: task.status,
      priority: task.priority,
      assignee: task.assignee,
      due_date: task.due_date,
    })
    setLabelSelection(task.labels.map((l) => l.id))
    setFormErrors({})
    setFormGlobalError(null)
    setEditOpen(true)
  }

  function handleSave(e: FormEvent) {
    e.preventDefault()
    if (!form.title?.trim()) {
      setFormErrors({ title: "Title is required." })
      return
    }
    const payload: Partial<CreateTaskPayload> = {
      ...form,
      title: form.title.trim(),
      label_ids: labelSelection,
    }
    updateMutation.mutate(payload)
  }

  return (
    <div>
      <PageHeader
        title={task?.title ?? "Task"}
        description={
          task
            ? `Created ${formatDate(task.created_at)} · ${task.project_name ?? "No project"}`
            : undefined
        }
        actions={
          task && (
            <div className="flex gap-2">
              <Button onClick={openEdit}>Edit</Button>
              {canDelete && (
                <Button variant="danger" onClick={() => setDeleteOpen(true)}>
                  Delete
                </Button>
              )}
            </div>
          )
        }
      />

      {taskQuery.isPending && <LoadingState label="Loading task…" />}

      {taskQuery.isError && (
        <ErrorState
          title="Could not load task"
          description="The task may not exist or you may not have access."
          action={<Button onClick={() => navigate("/tasks")}>Back to tasks</Button>}
        />
      )}

      {task && (
        <div className="space-y-4">
          {task.labels.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              {task.labels.map((label) => (
                <LabelChip key={label.id} label={label} />
              ))}
            </div>
          )}

          <nav
            aria-label="Task sections"
            className="flex gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1"
          >
            {TABS.map((tab) => {
              const Icon = tab.icon
              const active = activeTab === tab.key
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium whitespace-nowrap transition-colors",
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                  )}
                >
                  <Icon className="size-4" />
                  {tab.label}
                </button>
              )
            })}
          </nav>

          {activeTab === "overview" && <OverviewTab task={task} onEdit={openEdit} />}
          {activeTab === "checklist" && <ChecklistTab taskId={task.id} />}
          {activeTab === "subtasks" && <SubtasksTab taskId={task.id} />}
          {activeTab === "comments" && <CommentsTab taskId={task.id} />}
          {activeTab === "attachments" && (
            <DocumentManager entityKind="TASK" entityId={task.id} canDelete={canDelete} />
          )}
          {activeTab === "activity" && <ActivityTab task={task} />}
        </div>
      )}

      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit task"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              form="task-edit-form"
              isLoading={updateMutation.isPending}
            >
              Save changes
            </Button>
          </>
        }
      >
        <form id="task-edit-form" onSubmit={handleSave} className="space-y-4">
          {formGlobalError && (
            <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {formGlobalError}
            </div>
          )}
          <Input
            label="Title"
            value={form.title ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            error={formErrors.title}
            required
          />
          <div>
            <label htmlFor="task-edit-desc" className="mb-1.5 block text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              id="task-edit-desc"
              rows={3}
              value={form.description ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Project"
              value={form.project ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, project: e.target.value || null }))}
              error={formErrors.project}
            >
              <option value="">No project</option>
              {projectsQuery.data?.results.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
            <Select
              label="Assignee"
              value={form.assignee ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, assignee: e.target.value || null }))}
              error={formErrors.assignee}
            >
              <option value="">Unassigned</option>
              {membersQuery.data?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.full_name || m.email}
                </option>
              ))}
            </Select>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Select
              label="Status"
              value={form.status ?? "TODO"}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              error={formErrors.status}
            >
              {STATUS_OPTIONS.map((v) => (
                <option key={v} value={v}>
                  {v.replace("_", " ")}
                </option>
              ))}
            </Select>
            <Select
              label="Priority"
              value={form.priority ?? "MEDIUM"}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
              error={formErrors.priority}
            >
              {PRIORITY_OPTIONS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </Select>
            <Input
              label="Due date"
              type="date"
              value={form.due_date ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value || null }))}
            />
          </div>
          <div>
            <p className="mb-1.5 text-sm font-medium text-slate-700">Labels</p>
            {labelsQuery.isPending ? (
              <p className="text-sm text-slate-400">Loading labels…</p>
            ) : (labelsQuery.data?.results ?? []).length === 0 ? (
              <p className="text-sm text-slate-400">No labels yet in your workspace.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {labelsQuery.data?.results.map((label) => {
                  const selected = labelSelection.includes(label.id)
                  return (
                    <button
                      key={label.id}
                      type="button"
                      onClick={() =>
                        setLabelSelection((prev) =>
                          selected ? prev.filter((v) => v !== label.id) : [...prev, label.id],
                        )
                      }
                      aria-pressed={selected}
                      className={cn(
                        "rounded-md border px-2 py-1 text-xs font-medium transition-colors",
                        selected
                          ? "border-brand-300 bg-brand-50 text-brand-700"
                          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                      )}
                    >
                      <LabelChip label={label} />
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </form>
      </Modal>

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete task"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              isLoading={deleteMutation.isPending}
              onClick={() => deleteMutation.mutate(id!)}
            >
              Delete permanently
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Are you sure you want to permanently delete{" "}
          <span className="font-medium text-slate-900">{task?.title}</span>? This action cannot
          be undone.
        </p>
      </Modal>
    </div>
  )
}