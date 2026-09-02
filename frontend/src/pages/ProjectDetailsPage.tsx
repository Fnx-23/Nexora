import { useCallback, useMemo, useState } from "react"
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
  Table,
  TableContainer,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui/Table"
import {
  ActivityIcon,
  UsersIcon,
  ClockIcon,
  FolderIcon,
  InboxIcon,
  CheckSquareIcon,
} from "@/components/icons"
import { ActivityRow } from "@/features/activity/ActivityRow"
import { useAuth } from "@/hooks/useAuth"
import {
  fetchProject,
  updateProject,
  archiveProject,
  restoreProject,
  deleteProject,
  addProjectMember,
  removeProjectMember,
  fetchProjectMembers,
  type CreateProjectPayload,
} from "@/features/projects/api"
import { fetchCustomers } from "@/features/customers/api"
import { fetchMembers } from "@/features/team/api"
import { fetchTasks, type TaskListParams } from "@/features/tasks/api"
import { fetchTimeEntries } from "@/features/time-tracking/api"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"
import type { Project, ProjectHealth } from "@/types/project"
import { PROJECT_HEALTH_LABELS } from "@/types/project"

const STATUS_OPTIONS = ["PLANNING", "IN_PROGRESS", "ON_HOLD", "COMPLETED"]
const PRIORITY_OPTIONS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

type TabKey = "overview" | "tasks" | "members" | "time" | "documents" | "activity"

const TABS: { key: TabKey; label: string; icon: typeof InboxIcon }[] = [
  { key: "overview", label: "Overview", icon: InboxIcon },
  { key: "tasks", label: "Tasks", icon: CheckSquareIcon },
  { key: "members", label: "Members", icon: UsersIcon },
  { key: "time", label: "Time", icon: ClockIcon },
  { key: "documents", label: "Documents", icon: FolderIcon },
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

function formatHours(hours: number) {
  return `${hours.toLocaleString("en-US", { maximumFractionDigits: 1 })}h`
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline">
      <span className="w-32 shrink-0 text-sm font-medium text-slate-500">{label}</span>
      <span className="text-sm text-slate-900">{children}</span>
    </div>
  )
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string
  value: React.ReactNode
  sub?: React.ReactNode
}) {
  return (
    <Card className="px-5 py-4">
      <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </Card>
  )
}

function ProgressBar({ value, health }: { value: number; health: string }) {
  const color =
    health === "OVERDUE"
      ? "bg-red-500"
      : health === "AT_RISK"
        ? "bg-amber-500"
        : health === "COMPLETED"
          ? "bg-emerald-500"
          : "bg-brand-600"
  return (
    <div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-xs text-slate-500">
        <span>{value}% complete</span>
        <span>
          {value >= 100 ? "All tasks done" : `${100 - value}% remaining`}
        </span>
      </div>
    </div>
  )
}

function HealthBadge({ health }: { health: string }) {
  const classes: Record<string, string> = {
    NOT_STARTED: "bg-slate-100 text-slate-600",
    ON_TRACK: "bg-emerald-50 text-emerald-700",
    AT_RISK: "bg-amber-50 text-amber-700",
    OVERDUE: "bg-red-50 text-red-700",
    COMPLETED: "bg-sky-50 text-sky-700",
  }
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        classes[health] ?? "bg-slate-100 text-slate-600",
      )}
    >
      {PROJECT_HEALTH_LABELS[health as ProjectHealth] ?? health.replace("_", " ")}
    </span>
  )
}

function OverviewTab({ project }: { project: Project }) {
  const done = project.done_count ?? 0
  const inProgress = project.in_progress_count ?? 0
  const todo = project.todo_count ?? 0
  const overdue = project.overdue_count ?? 0
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <Card className="px-5 py-4">
          <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">
            Progress
          </p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {project.progress ?? 0}%
          </p>
          <div className="mt-2">
            <ProgressBar value={project.progress ?? 0} health={project.health ?? "NOT_STARTED"} />
          </div>
        </Card>
        <StatCard
          label="Health"
          value={<HealthBadge health={project.health ?? "NOT_STARTED"} />}
        />
        <StatCard
          label="Tasks"
          value={
            <span>
              {done}<span className="text-slate-400">/{project.task_count ?? 0}</span>
            </span>
          }
          sub={
            overdue > 0 ? (
              <span className="font-medium text-red-600">{overdue} overdue</span>
            ) : (
              `${todo} to do · ${inProgress} in progress`
            )
          }
        />
        <StatCard label="Tracked time" value={formatHours(project.tracked_hours ?? 0)} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <InfoRow label="Customer">{project.customer_name || "—"}</InfoRow>
          <InfoRow label="Manager">{project.manager_name || "—"}</InfoRow>
          <InfoRow label="Status"><StatusBadge value={project.status} /></InfoRow>
          <InfoRow label="Priority"><StatusBadge value={project.priority} /></InfoRow>
          <InfoRow label="Start date">{formatDate(project.start_date)}</InfoRow>
          <InfoRow label="Deadline">{formatDate(project.deadline)}</InfoRow>
          <InfoRow label="Members">
            <span className="text-slate-900">{project.member_count}</span>
          </InfoRow>
          {project.description && (
            <div className="pt-1">
              <p className="text-sm font-medium text-slate-500">Description</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">
                {project.description}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function TasksTab({ project }: { project: Project }) {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null
  const params = useMemo<TaskListParams>(
    () => ({ project: project.id, page_size: 100 }),
    [project.id],
  )
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: [...queryKeys.tasks(companyId), "project", project.id],
    queryFn: () => fetchTasks(params),
    enabled: true,
  })

  if (isPending) return <LoadingState label="Loading tasks…" />
  if (isError)
    return (
      <ErrorState
        title="Could not load tasks"
        description="The task list could not be loaded."
        onRetry={() => void refetch()}
      />
    )

  const tasks = data?.results ?? []

  if (tasks.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState
            title="No tasks yet"
            description="Tasks for this project will appear here."
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tasks</CardTitle>
      </CardHeader>
      <CardContent>
        <TableContainer>
          <Table>
            <THead>
              <TR>
                <TH>Title</TH>
                <TH className="hidden sm:table-cell">Status</TH>
                <TH className="hidden md:table-cell">Priority</TH>
                <TH className="hidden md:table-cell">Assignee</TH>
                <TH className="hidden lg:table-cell">Due date</TH>
              </TR>
            </THead>
            <TBody>
              {tasks.map((task) => (
                <TR key={task.id}>
                  <TD>
                    <p className="font-medium text-slate-900">{task.title}</p>
                    {task.description && (
                      <p className="mt-0.5 line-clamp-1 text-sm text-slate-500">
                        {task.description}
                      </p>
                    )}
                  </TD>
                  <TD className="hidden sm:table-cell">
                    <StatusBadge value={task.status} />
                  </TD>
                  <TD className="hidden md:table-cell">
                    <StatusBadge value={task.priority} />
                  </TD>
                  <TD className="hidden md:table-cell text-slate-600">
                    {task.assignee_name || "—"}
                  </TD>
                  <TD className="hidden lg:table-cell text-slate-600">
                    {formatDate(task.due_date)}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  )
}

function MembersTab({ project }: { project: Project }) {
  const { activeCompany, role } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null
  const canManage = role === "ADMIN" || role === "MANAGER"
  const [selectedMember, setSelectedMember] = useState("")

  const membersQuery = useQuery({
    queryKey: queryKeys.projectMembers(project.id),
    queryFn: () => fetchProjectMembers(project.id),
  })

  const directoryQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null,
  })

  const addMutation = useMutation({
    mutationFn: (userId: string) => addProjectMember(project.id, userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projectMembers(project.id) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.project(project.id) })
      setSelectedMember("")
    },
  })

  const removeMutation = useMutation({
    mutationFn: (memberId: string) => removeProjectMember(project.id, memberId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projectMembers(project.id) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.project(project.id) })
    },
  })

  const members = membersQuery.data ?? []
  const assignedIds = new Set(members.map((m) => m.user))
  const available = (directoryQuery.data ?? []).filter(
    (m) => !assignedIds.has(m.id),
  )

  if (membersQuery.isPending) return <LoadingState label="Loading members…" />
  if (membersQuery.isError)
    return (
      <ErrorState
        title="Could not load members"
        description="The member list could not be loaded."
        onRetry={() => void membersQuery.refetch()}
      />
    )

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Team members</CardTitle>
          {canManage && (
            <div className="flex items-center gap-2">
              <Select
                value={selectedMember}
                onChange={(e) => setSelectedMember(e.target.value)}
                className="w-56"
                aria-label="Select a member to add"
              >
                <option value="">Add a member…</option>
                {available.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.full_name || m.email}
                  </option>
                ))}
              </Select>
              <Button
                size="sm"
                disabled={!selectedMember}
                isLoading={addMutation.isPending}
                onClick={() => selectedMember && addMutation.mutate(selectedMember)}
              >
                Add
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {members.length === 0 ? (
          <EmptyState
            title="No members assigned"
            description="Add team members to this project to start collaborating."
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {members.map((member) => (
              <li key={member.id} className="flex items-center gap-3 py-3">
                <Avatar name={member.full_name} src={member.avatar} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900">
                    {member.full_name}
                  </p>
                  <p className="truncate text-xs text-slate-500">{member.email}</p>
                </div>
                {canManage && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeMutation.mutate(member.id)}
                  >
                    Remove
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function TimeTab({ projectId }: { projectId: string }) {
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ["timeEntries", "project", projectId],
    queryFn: () =>
      fetchTimeEntries({ project: projectId, page_size: 100 }),
  })

  if (isPending) return <LoadingState label="Loading time entries…" />
  if (isError)
    return (
      <ErrorState
        title="Could not load time entries"
        description="The project time log could not be loaded."
        onRetry={() => void refetch()}
      />
    )

  const entries = data?.results ?? []
  const totalMinutes = entries.reduce((sum, e) => {
    if (!e.duration) return sum
    const [h, m] = e.duration.split(":").map(Number)
    return sum + (h * 60 + (m || 0))
  }, 0)

  if (entries.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState
            title="No time logged"
            description="Time entries billed to this project will appear here."
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Time entries</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-sm text-slate-500">
          Total logged: <span className="font-semibold text-slate-900">{totalMinutes} min</span>
        </p>
        <TableContainer>
          <Table>
            <THead>
              <TR>
                <TH>Date</TH>
                <TH className="hidden sm:table-cell">Member</TH>
                <TH className="hidden md:table-cell">Task</TH>
                <TH>Time</TH>
                <TH className="hidden lg:table-cell">Description</TH>
              </TR>
            </THead>
            <TBody>
              {entries.map((entry) => (
                <TR key={entry.id}>
                  <TD className="text-slate-600">{formatDate(entry.date)}</TD>
                  <TD className="hidden sm:table-cell text-slate-600">
                    {entry.user_name}
                  </TD>
                  <TD className="hidden md:table-cell text-slate-600">
                    {entry.task_title || "—"}
                  </TD>
                  <TD className="whitespace-nowrap text-slate-700">
                    {entry.start_time.slice(0, 5)}–{entry.end_time?.slice(0, 5) ?? "…"}
                  </TD>
                  <TD className="hidden lg:table-cell text-slate-500">
                    {entry.description || "—"}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  )
}

function ActivityTab({ project }: { project: Project }) {
  const activities = project.recent_activity ?? []
  if (activities.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState
            title="No activity yet"
            description="Changes to this project will show up here."
          />
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

export function ProjectDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { activeCompany, role } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const canEdit = role === "ADMIN" || role === "MANAGER" || role === "EMPLOYEE"
  const canDelete = role === "ADMIN" || role === "MANAGER"

  const [activeTab, setActiveTab] = useState<TabKey>("overview")
  const [editOpen, setEditOpen] = useState(false)
  const [form, setForm] = useState<Partial<CreateProjectPayload>>({})
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formGlobalError, setFormGlobalError] = useState<string | null>(null)
  const [archiveOpen, setArchiveOpen] = useState(false)
  const [restoreOpen, setRestoreOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)

  const projectQuery = useQuery({
    queryKey: queryKeys.project(id!),
    queryFn: () => fetchProject(id!),
    enabled: id !== undefined,
  })

  const customersQuery = useQuery({
    queryKey: queryKeys.customers(companyId),
    queryFn: () => fetchCustomers({ page_size: 100 }),
    enabled: companyId !== null && editOpen,
  })

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null && editOpen,
  })

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.projects(companyId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.project(id!) })
  }, [queryClient, companyId, id])

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<CreateProjectPayload>) => updateProject(id!, payload),
    onSuccess: () => {
      invalidate()
      closeEdit()
    },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const archiveMutation = useMutation({
    mutationFn: archiveProject,
    onSuccess: () => {
      invalidate()
      setArchiveOpen(false)
    },
  })

  const restoreMutation = useMutation({
    mutationFn: () => restoreProject(id!, "IN_PROGRESS"),
    onSuccess: () => {
      invalidate()
      setRestoreOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      const key = queryKeys.project(id!)
      void queryClient.cancelQueries({ queryKey: key })
      queryClient.removeQueries({ queryKey: key })
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects(companyId) })
      navigate("/projects")
    },
  })

  function handleMutationError(
    err: Error & { response?: { data?: Record<string, unknown> } },
  ) {
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

  const project = projectQuery.data

  function openEdit() {
    if (!project) return
    setForm({
      name: project.name,
      description: project.description,
      customer: project.customer,
      manager: project.manager,
      status: project.status,
      priority: project.priority,
      start_date: project.start_date,
      deadline: project.deadline,
    })
    setFormErrors({})
    setFormGlobalError(null)
    setEditOpen(true)
  }

  function closeEdit() {
    setEditOpen(false)
    setFormErrors({})
    setFormGlobalError(null)
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name?.trim()) {
      setFormErrors({ name: "Project name is required." })
      return
    }
    updateMutation.mutate(form)
  }

  return (
    <div>
      <PageHeader
        title={project?.name ?? "Project"}
        description={
          project
            ? `Created ${formatDate(project.created_at)} · ${project.task_count} task${project.task_count !== 1 ? "s" : ""}`
            : undefined
        }
        actions={
          project && (
            <div className="flex gap-2">
              {canEdit && <Button onClick={openEdit}>Edit</Button>}
              {canDelete && project.status !== "ARCHIVED" && (
                <Button variant="secondary" onClick={() => setArchiveOpen(true)}>
                  Archive
                </Button>
              )}
              {canDelete && project.status === "ARCHIVED" && (
                <Button variant="secondary" onClick={() => setRestoreOpen(true)}>
                  Restore
                </Button>
              )}
              {canDelete && (
                <Button variant="danger" onClick={() => setDeleteOpen(true)}>
                  Delete
                </Button>
              )}
            </div>
          )
        }
      />

      {projectQuery.isPending && <LoadingState label="Loading project…" />}

      {projectQuery.isError && (
        <ErrorState
          title="Could not load project"
          description="The project may not exist or you may not have access."
          action={<Button onClick={() => navigate("/projects")}>Back to projects</Button>}
        />
      )}

      {project && (
        <div className="space-y-4">
          <nav
            aria-label="Project sections"
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

          {activeTab === "overview" && <OverviewTab project={project} />}
          {activeTab === "tasks" && <TasksTab project={project} />}
          {activeTab === "members" && <MembersTab project={project} />}
          {activeTab === "time" && <TimeTab projectId={project.id} />}
          {activeTab === "documents" && (
            <DocumentManager
              entityKind="PROJECT"
              entityId={project.id}
              canDelete={canDelete}
            />
          )}
          {activeTab === "activity" && <ActivityTab project={project} />}
        </div>
      )}

      <Modal
        open={editOpen}
        onClose={closeEdit}
        title="Edit project"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={closeEdit}>Cancel</Button>
            <Button
              type="submit"
              form="project-edit-form"
              isLoading={updateMutation.isPending}
            >
              Save changes
            </Button>
          </>
        }
      >
        <form id="project-edit-form" onSubmit={handleSave} className="space-y-4">
          {formGlobalError && (
            <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {formGlobalError}
            </div>
          )}
          <Input
            label="Project name"
            value={form.name ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            error={formErrors.name}
            required
          />
          <div>
            <label htmlFor="edit-desc" className="mb-1.5 block text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              id="edit-desc"
              rows={3}
              value={form.description ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Customer"
              value={form.customer ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, customer: e.target.value || null }))}
            >
              <option value="">No customer</option>
              {customersQuery.data?.results.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </Select>
            <Select
              label="Manager"
              value={form.manager ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, manager: e.target.value || null }))}
            >
              <option value="">No manager</option>
              {membersQuery.data?.map((m) => (
                <option key={m.id} value={m.id}>{m.full_name || m.email}</option>
              ))}
            </Select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Status"
              value={form.status ?? "PLANNING"}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              error={formErrors.status}
            >
              {STATUS_OPTIONS.map((v) => (
                <option key={v} value={v}>{v.replace("_", " ")}</option>
              ))}
            </Select>
            <Select
              label="Priority"
              value={form.priority ?? "MEDIUM"}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
              error={formErrors.priority}
            >
              {PRIORITY_OPTIONS.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </Select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Start date"
              type="date"
              value={form.start_date ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value || null }))}
            />
            <Input
              label="Deadline"
              type="date"
              value={form.deadline ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value || null }))}
            />
          </div>
        </form>
      </Modal>

      <Modal
        open={archiveOpen}
        onClose={() => setArchiveOpen(false)}
        title="Archive project"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setArchiveOpen(false)}>Cancel</Button>
            <Button
              variant="danger"
              isLoading={archiveMutation.isPending}
              onClick={() => archiveMutation.mutate(id!)}
            >
              Archive
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          This will set the project status to{" "}
          <span className="font-medium">Archived</span>. You can restore it later.
        </p>
      </Modal>

      <Modal
        open={restoreOpen}
        onClose={() => setRestoreOpen(false)}
        title="Restore project"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setRestoreOpen(false)}>Cancel</Button>
            <Button
              isLoading={restoreMutation.isPending}
              onClick={() => restoreMutation.mutate()}
            >
              Restore
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Restore{" "}
          <span className="font-medium text-slate-900">{project?.name}</span> to{" "}
          <span className="font-medium">In progress</span> so work can continue.
        </p>
      </Modal>

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete project"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteOpen(false)}>Cancel</Button>
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
          <span className="font-medium text-slate-900">{project?.name}</span>?
          This action cannot be undone. Consider archiving instead.
        </p>
      </Modal>
    </div>
  )
}
