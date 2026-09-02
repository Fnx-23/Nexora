import { useCallback, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { StatusBadge } from "@/components/ui/Badge"
import { Modal } from "@/components/ui/Modal"
import { ErrorState } from "@/components/ui/ErrorState"
import { EmptyState } from "@/components/ui/EmptyState"
import { LoadingState } from "@/components/ui/LoadingState"
import {
  Table,
  TableContainer,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui/Table"
import { useAuth } from "@/hooks/useAuth"
import {
  fetchProjects,
  createProject,
  updateProject,
  archiveProject,
  restoreProject,
  type ProjectListParams,
  type CreateProjectPayload,
} from "@/features/projects/api"
import { fetchCustomers } from "@/features/customers/api"
import { fetchMembers } from "@/features/team/api"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"
import { PROJECT_HEALTH_LABELS } from "@/types/project"

const PAGE_SIZE = 25

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "PLANNING", label: "Planning" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "ON_HOLD", label: "On hold" },
  { value: "COMPLETED", label: "Completed" },
  { value: "ARCHIVED", label: "Archived" },
]

const PRIORITY_OPTIONS = [
  { value: "", label: "All priorities" },
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "CRITICAL", label: "Critical" },
]

const EMPTY_FORM: CreateProjectPayload = {
  name: "",
  description: "",
  customer: null,
  manager: null,
  status: "PLANNING",
  priority: "MEDIUM",
  start_date: null,
  deadline: null,
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function DeadlineCell({ deadline }: { deadline: string | null }) {
  if (!deadline) return <span className="text-slate-400">—</span>
  const isPast = new Date(deadline) < new Date()
  return (
    <span className={isPast ? "font-medium text-red-600" : "text-slate-600"}>
      {formatDate(deadline)}
    </span>
  )
}

const HEALTH_CLASSES: Record<string, string> = {
  NOT_STARTED: "bg-slate-100 text-slate-600",
  ON_TRACK: "bg-emerald-50 text-emerald-700",
  AT_RISK: "bg-amber-50 text-amber-700",
  OVERDUE: "bg-red-50 text-red-700",
  COMPLETED: "bg-sky-50 text-sky-700",
}

function HealthBadge({ health }: { health?: string }) {
  if (!health) return <span className="text-slate-400">—</span>
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        HEALTH_CLASSES[health] ?? "bg-slate-100 text-slate-600",
      )}
    >
      {PROJECT_HEALTH_LABELS[health as keyof typeof PROJECT_HEALTH_LABELS] ?? health.replace("_", " ")}
    </span>
  )
}

function ProgressCell({ progress, health }: { progress?: number; health?: string }) {
  const value = progress ?? 0
  const color =
    health === "OVERDUE"
      ? "bg-red-500"
      : health === "AT_RISK"
        ? "bg-amber-500"
        : health === "COMPLETED"
          ? "bg-emerald-500"
          : "bg-brand-600"
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn("h-full rounded-full", color)}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <span className="text-sm tabular-nums text-slate-600">{value}%</span>
    </div>
  )
}

export function ProjectsPage() {
  const { activeCompany, role } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [priorityFilter, setPriorityFilter] = useState("")
  const [customerFilter, setCustomerFilter] = useState("")
  const [page, setPage] = useState(1)
  const [showArchived, setShowArchived] = useState(false)

  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<CreateProjectPayload>({ ...EMPTY_FORM })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formGlobalError, setFormGlobalError] = useState<string | null>(null)

  const [archiveTarget, setArchiveTarget] = useState<{ id: string; name: string } | null>(null)

  const canDelete = role === "ADMIN" || role === "MANAGER"

  const queryParams = useMemo<ProjectListParams>(() => {
    const params: ProjectListParams = { page, page_size: PAGE_SIZE }
    if (debouncedSearch) params.search = debouncedSearch
    if (statusFilter) params.status = statusFilter
    else if (showArchived) params.status = "ARCHIVED"
    if (priorityFilter) params.priority = priorityFilter
    if (customerFilter) params.customer = customerFilter
    return params
  }, [page, debouncedSearch, statusFilter, priorityFilter, customerFilter, showArchived])

  const projectsQuery = useQuery({
    queryKey: [...queryKeys.projects(companyId), queryParams],
    queryFn: () => fetchProjects(queryParams),
    enabled: companyId !== null,
  })

  const customersQuery = useQuery({
    queryKey: queryKeys.customers(companyId),
    queryFn: () => fetchCustomers({ page_size: 100 }),
    enabled: companyId !== null,
  })

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null,
  })

  const searchTimeout = useMemo(() => {
    let timer: ReturnType<typeof setTimeout>
    return (value: string) => {
      clearTimeout(timer)
      timer = setTimeout(() => {
        setDebouncedSearch(value)
        setPage(1)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [])

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearch(e.target.value)
      searchTimeout(e.target.value)
    },
    [searchTimeout],
  )

  const handleStatusChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value)
    setPage(1)
  }, [])

  const handlePriorityChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setPriorityFilter(e.target.value)
    setPage(1)
  }, [])

  const handleCustomerChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setCustomerFilter(e.target.value)
    setPage(1)
  }, [])

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.projects(companyId) })
  }, [queryClient, companyId])

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => { invalidate(); closeForm() },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateProjectPayload> }) =>
      updateProject(id, payload),
    onSuccess: () => { invalidate(); closeForm() },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const archiveMutation = useMutation({
    mutationFn: archiveProject,
    onSuccess: () => { invalidate(); setArchiveTarget(null) },
  })

  const restoreMutation = useMutation({
    mutationFn: (id: string) => restoreProject(id, "IN_PROGRESS"),
    onSuccess: () => { invalidate() },
  })

  function handleMutationError(err: Error & { response?: { data?: Record<string, unknown> } }) {
    const data = err.response?.data
    if (data && typeof data === "object") {
      const fieldErrors: Record<string, string> = {}
      for (const [key, val] of Object.entries(data)) {
        if (key === "detail") {
          setFormGlobalError(String(val))
        } else if (Array.isArray(val)) {
          fieldErrors[key] = val.join(" ")
        } else if (typeof val === "string") {
          fieldErrors[key] = val
        }
      }
      if (Object.keys(fieldErrors).length) setFormErrors(fieldErrors)
    } else {
      setFormGlobalError("An unexpected error occurred. Please try again.")
    }
  }

  function openCreateForm() {
    setEditingId(null)
    setForm({ ...EMPTY_FORM })
    setFormErrors({})
    setFormGlobalError(null)
    setFormOpen(true)
  }

  function openEditForm(project: {
    id: string; name: string; description: string;
    customer: string | null; manager: string | null;
    status: string; priority: string;
    start_date: string | null; deadline: string | null;
  }) {
    setEditingId(project.id)
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
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
    setEditingId(null)
    setFormErrors({})
    setFormGlobalError(null)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormErrors({})
    setFormGlobalError(null)

    if (!form.name.trim()) {
      setFormErrors({ name: "Project name is required." })
      return
    }

    if (editingId) {
      updateMutation.mutate({ id: editingId, payload: form })
    } else {
      createMutation.mutate(form)
    }
  }

  const data = projectsQuery.data
  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1

  return (
    <div>
      <PageHeader
        title="Projects"
        description="Organize work into trackable projects."
        actions={<Button onClick={openCreateForm}>New project</Button>}
      />

      {projectsQuery.isPending && <LoadingState label="Loading projects…" />}

      {projectsQuery.isError && (
        <ErrorState
          title="Could not load projects"
          description="The server rejected or dropped the request. Check your connection and try again."
          onRetry={() => void projectsQuery.refetch()}
        />
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Input
              placeholder="Search projects…"
              value={search}
              onChange={handleSearchChange}
              className="sm:max-w-xs"
            />
            <Select value={statusFilter} onChange={handleStatusChange} className="sm:max-w-[160px]">
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </Select>
            <Select value={priorityFilter} onChange={handlePriorityChange} className="sm:max-w-[160px]">
              {PRIORITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </Select>
            <Select value={customerFilter} onChange={handleCustomerChange} className="sm:max-w-[180px]">
              <option value="">All customers</option>
              {customersQuery.data?.results.map((c) => (
                <option key={c.id} value={c.id}>{c.company_name || c.name}</option>
              ))}
            </Select>
            <button
              type="button"
              onClick={() => {
                setShowArchived((v) => !v)
                setPage(1)
              }}
              className={cn(
                "inline-flex h-10 items-center rounded-lg border px-3.5 text-sm font-medium transition-colors",
                showArchived
                  ? "border-brand-500 bg-brand-50 text-brand-700"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
              )}
            >
              Archived
            </button>
            {data.count > 0 && (
              <span className="ml-auto text-sm text-slate-500">
                {data.count} project{data.count !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {data.results.length === 0 ? (
            <EmptyState
              title="No projects found"
              description={
                debouncedSearch || statusFilter || priorityFilter || customerFilter
                  ? "Try adjusting your search or filters."
                  : "Create your first project to get started."
              }
              action={
                !debouncedSearch && !statusFilter && !priorityFilter && !customerFilter ? (
                  <Button onClick={openCreateForm}>New project</Button>
                ) : undefined
              }
            />
          ) : (
            <>
              <TableContainer>
                <Table>
                  <THead>
                    <TR>
                      <TH>Name</TH>
                      <TH className="hidden sm:table-cell">Customer</TH>
                      <TH className="hidden md:table-cell">Manager</TH>
                      <TH>Status</TH>
                      <TH className="hidden sm:table-cell">Priority</TH>
                      <TH className="hidden lg:table-cell">Health</TH>
                      <TH className="hidden md:table-cell">Progress</TH>
                      <TH className="hidden xl:table-cell">Members</TH>
                      <TH className="hidden lg:table-cell">Deadline</TH>
                      <TH><span className="sr-only">Actions</span></TH>
                    </TR>
                  </THead>
                  <TBody>
                    {data.results.map((project) => (
                      <TR key={project.id}>
                        <TD>
                          <button
                            type="button"
                            onClick={() => navigate(`/projects/${project.id}`)}
                            className="font-medium text-brand-600 hover:text-brand-800 hover:underline"
                          >
                            {project.name}
                          </button>
                        </TD>
                        <TD className="hidden sm:table-cell text-slate-600">
                          {project.customer_name || "—"}
                        </TD>
                        <TD className="hidden md:table-cell text-slate-600">
                          {project.manager_name || "—"}
                        </TD>
                        <TD><StatusBadge value={project.status} /></TD>
                        <TD className="hidden sm:table-cell">
                          <StatusBadge value={project.priority} />
                        </TD>
                        <TD className="hidden lg:table-cell">
                          <HealthBadge health={project.health} />
                        </TD>
                        <TD className="hidden md:table-cell">
                          <ProgressCell progress={project.progress} health={project.health} />
                        </TD>
                        <TD className="hidden xl:table-cell text-slate-600">
                          {project.member_count ?? 0} member{project.member_count !== 1 ? "s" : ""}
                        </TD>
                        <TD className="hidden lg:table-cell">
                          <DeadlineCell deadline={project.deadline} />
                        </TD>
                        <TD>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditForm(project)}
                            >
                              Edit
                            </Button>
                            {canDelete && project.status !== "ARCHIVED" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  setArchiveTarget({ id: project.id, name: project.name })
                                }
                              >
                                Archive
                              </Button>
                            )}
                            {canDelete && project.status === "ARCHIVED" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                isLoading={restoreMutation.isPending}
                                onClick={() => restoreMutation.mutate(project.id)}
                              >
                                Restore
                              </Button>
                            )}
                          </div>
                        </TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              </TableContainer>

              {totalPages > 1 && (
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
                  <span className="text-sm text-slate-500">
                    Page {page} of {totalPages}
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      <Modal
        open={formOpen}
        onClose={closeForm}
        title={editingId ? "Edit project" : "New project"}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={closeForm}>Cancel</Button>
            <Button
              type="submit"
              form="project-form"
              isLoading={createMutation.isPending || updateMutation.isPending}
            >
              {editingId ? "Save changes" : "Create project"}
            </Button>
          </>
        }
      >
        <form id="project-form" onSubmit={handleSubmit} className="space-y-4">
          {formGlobalError && (
            <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {formGlobalError}
            </div>
          )}

          <Input
            label="Project name"
            placeholder="Website redesign"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            error={formErrors.name}
            required
          />

          <div>
            <label htmlFor="project-desc" className="mb-1.5 block text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              id="project-desc"
              rows={3}
              placeholder="What is this project about?"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Customer"
              value={form.customer ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, customer: e.target.value || null }))}
              error={formErrors.customer}
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
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              error={formErrors.status}
            >
              <option value="PLANNING">Planning</option>
              <option value="IN_PROGRESS">In progress</option>
              <option value="ON_HOLD">On hold</option>
              <option value="COMPLETED">Completed</option>
              <option value="ARCHIVED">Archived</option>
            </Select>

            <Select
              label="Priority"
              value={form.priority}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
              error={formErrors.priority}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
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
        open={archiveTarget !== null}
        onClose={() => setArchiveTarget(null)}
        title="Archive project"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setArchiveTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              isLoading={archiveMutation.isPending}
              onClick={() => archiveTarget && archiveMutation.mutate(archiveTarget.id)}
            >
              Archive
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Are you sure you want to archive{" "}
          <span className="font-medium text-slate-900">{archiveTarget?.name}</span>?
        </p>
      </Modal>
    </div>
  )
}
