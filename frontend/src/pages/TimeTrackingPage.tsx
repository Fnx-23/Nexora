import { useCallback, useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Modal } from "@/components/ui/Modal"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
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
  fetchTimeEntries,
  fetchTimeEntrySummary,
  createTimeEntry,
  updateTimeEntry,
  deleteTimeEntry,
  type TimeEntryListParams,
  type CreateTimeEntryPayload,
} from "@/features/time-tracking/api"
import { fetchProjects } from "@/features/projects/api"
import { fetchAllTasks } from "@/features/tasks/api"
import { queryKeys } from "@/utils/queryKeys"
import type { TimeEntry } from "@/types/timeEntry"

function formatMinutes(mins: number): string {
  const h = Math.floor(mins / 60)
  const m = Math.round(mins % 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

function todayStr(): string {
  return new Date().toISOString().split("T")[0]
}

function weekAgoStr(): string {
  const d = new Date()
  d.setDate(d.getDate() - 6)
  return d.toISOString().split("T")[0]
}

function getWeekDates(): string[] {
  const dates: string[] = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    dates.push(d.toISOString().split("T")[0])
  }
  return dates
}

const EMPTY_FORM: CreateTimeEntryPayload = {
  project: "",
  task: null,
  date: todayStr(),
  start_time: "09:00",
  end_time: null,
  description: "",
}

export function TimeTrackingPage() {
  const { activeCompany, role } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const [formOpen, setFormOpen] = useState(false)
  const [editingEntry, setEditingEntry] = useState<TimeEntry | null>(null)
  const [form, setForm] = useState<CreateTimeEntryPayload>({ ...EMPTY_FORM })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formGlobalError, setFormGlobalError] = useState<string | null>(null)

  const [deleteTarget, setDeleteTarget] = useState<TimeEntry | null>(null)

  const [projectFilter, setProjectFilter] = useState("")
  const [dateFrom, setDateFrom] = useState(weekAgoStr())
  const [dateTo, setDateTo] = useState(todayStr())

  const canDelete = role === "ADMIN" || role === "MANAGER"

  const queryParams = useMemo<TimeEntryListParams>(() => {
    const params: TimeEntryListParams = {}
    if (projectFilter) params.project = projectFilter
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    return params
  }, [projectFilter, dateFrom, dateTo])

  const entriesQuery = useQuery({
    queryKey: [...queryKeys.timeEntries(companyId), queryParams],
    queryFn: () => fetchTimeEntries(queryParams),
    enabled: companyId !== null,
  })

  const summaryQuery = useQuery({
    queryKey: [...queryKeys.timeEntrySummary(companyId), queryParams],
    queryFn: () =>
      fetchTimeEntrySummary({
        date_from: queryParams.date_from,
        date_to: queryParams.date_to,
        project: queryParams.project,
      }),
    enabled: companyId !== null,
  })

  const projectsQuery = useQuery({
    queryKey: queryKeys.projects(companyId),
    queryFn: () => fetchProjects({ page_size: 100 }),
    enabled: companyId !== null,
  })

  const tasksQuery = useQuery({
    queryKey: [...queryKeys.tasks(companyId), { project: form.project }],
    queryFn: () => fetchAllTasks({ project: form.project }),
    enabled: companyId !== null && !!form.project,
  })

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.timeEntries(companyId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.timeEntrySummary(companyId) })
  }, [queryClient, companyId])

  const createMutation = useMutation({
    mutationFn: createTimeEntry,
    onSuccess: () => {
      invalidate()
      closeForm()
    },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateTimeEntryPayload> }) =>
      updateTimeEntry(id, payload),
    onSuccess: () => {
      invalidate()
      closeForm()
    },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTimeEntry,
    onSuccess: () => {
      invalidate()
      setDeleteTarget(null)
    },
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
    setEditingEntry(null)
    setForm({ ...EMPTY_FORM })
    setFormErrors({})
    setFormGlobalError(null)
    setFormOpen(true)
  }

  function openEditForm(entry: TimeEntry) {
    setEditingEntry(entry)
    setForm({
      project: entry.project,
      task: entry.task,
      date: entry.date,
      start_time: entry.start_time,
      end_time: entry.end_time,
      description: entry.description,
    })
    setFormErrors({})
    setFormGlobalError(null)
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
    setEditingEntry(null)
    setFormErrors({})
    setFormGlobalError(null)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormErrors({})
    setFormGlobalError(null)

    if (!form.project) {
      setFormErrors({ project: "Project is required." })
      return
    }
    if (!form.start_time) {
      setFormErrors({ start_time: "Start time is required." })
      return
    }

    if (editingEntry) {
      updateMutation.mutate({ id: editingEntry.id, payload: form })
    } else {
      createMutation.mutate(form)
    }
  }

  const entries = entriesQuery.data?.results ?? []
  const summary = summaryQuery.data
  const weekDates = getWeekDates()
  const weekTotals = summary?.by_date ?? []
  const weekTotalMap = new Map(weekTotals.map((d) => [d.date, d.total_minutes]))
  const weekTotalMinutes = summary?.total_duration_minutes ?? 0

  return (
    <div>
      <PageHeader
        title="Time Tracking"
        description="Log and review work hours across your projects."
        actions={<Button onClick={openCreateForm}>Log time</Button>}
      />

      {entriesQuery.isPending && <LoadingState label="Loading entries…" />}

      {entriesQuery.isError && (
        <ErrorState
          title="Could not load time entries"
          description="Check your connection and try again."
          onRetry={() => void entriesQuery.refetch()}
        />
      )}

      {entriesQuery.data && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <p className="text-sm text-slate-500">Total This Period</p>
                <p className="text-3xl font-semibold tracking-tight text-slate-900">
                  {formatMinutes(weekTotalMinutes)}
                </p>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-400">
                  {summary?.total_entries ?? 0} entries
                </p>
              </CardContent>
            </Card>

            <Card className="sm:col-span-2 xl:col-span-1">
              <CardHeader className="pb-2">
                <p className="text-sm text-slate-500">Today</p>
                <p className="text-3xl font-semibold tracking-tight text-slate-900">
                  {formatMinutes(weekTotalMap.get(todayStr()) ?? 0)}
                </p>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-400">
                  {entries.filter((e) => e.date === todayStr()).length} entries
                </p>
              </CardContent>
            </Card>

            {/* Weekly bar */}
            <Card className="sm:col-span-2">
              <CardHeader className="pb-2">
                <p className="text-sm text-slate-500">This Week</p>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-1.5" style={{ height: 64 }}>
                  {weekDates.map((d) => {
                    const mins = weekTotalMap.get(d) ?? 0
                    const maxMins = Math.max(...weekDates.map((dd) => weekTotalMap.get(dd) ?? 0), 1)
                    const pct = (mins / maxMins) * 100
                    const isToday = d === todayStr()
                    return (
                      <div key={d} className="flex flex-1 flex-col items-center gap-1">
                        <div
                          className={`w-full rounded-t ${isToday ? "bg-brand-500" : "bg-brand-200"}`}
                          style={{ height: `${Math.max(pct, mins > 0 ? 8 : 0)}%` }}
                          title={`${d}: ${formatMinutes(mins)}`}
                        />
                        <span className="text-[10px] text-slate-400">
                          {new Date(d + "T00:00:00").toLocaleDateString("en", { weekday: "short" }).slice(0, 2)}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* By-project breakdown */}
          {summary && summary.by_project.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Time by Project</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {summary.by_project.map((p) => (
                    <div key={p.project_name} className="flex items-center gap-3">
                      <span className="min-w-[140px] truncate text-sm text-slate-700">
                        {p.project_name}
                      </span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-brand-400"
                          style={{
                            width: `${(p.total_minutes / Math.max(summary.total_duration_minutes, 1)) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="w-16 text-right text-sm font-medium text-slate-900">
                        {formatMinutes(p.total_minutes)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Filters */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              className="sm:max-w-[200px]"
            >
              <option value="">All projects</option>
              {projectsQuery.data?.results.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="sm:max-w-[160px]"
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="sm:max-w-[160px]"
            />
            {entries.length > 0 && (
              <span className="ml-auto text-sm text-slate-500">
                {entries.length} entr{entries.length !== 1 ? "ies" : "y"} ·{" "}
                {formatMinutes(weekTotalMinutes)}
              </span>
            )}
          </div>

          {/* Entries Table */}
          {entries.length === 0 ? (
            <EmptyState
              title="No time entries"
              description={
                projectFilter || dateFrom || dateTo
                  ? "Try adjusting your filters."
                  : "Log your first time entry to get started."
              }
              action={
                !projectFilter && !dateFrom && !dateTo ? (
                  <Button onClick={openCreateForm}>Log time</Button>
                ) : undefined
              }
            />
          ) : (
            <TableContainer>
              <Table>
                <THead>
                  <TR>
                    <TH>Date</TH>
                    <TH>Project</TH>
                    <TH className="hidden sm:table-cell">Task</TH>
                    <TH>Start</TH>
                    <TH className="hidden sm:table-cell">End</TH>
                    <TH>Duration</TH>
                    <TH className="hidden md:table-cell">Description</TH>
                    <TH><span className="sr-only">Actions</span></TH>
                  </TR>
                </THead>
                <TBody>
                  {entries.map((entry) => (
                    <TR key={entry.id}>
                      <TD className="text-sm">{entry.date}</TD>
                      <TD>
                        <span className="font-medium text-slate-900">
                          {entry.project_name || "—"}
                        </span>
                      </TD>
                      <TD className="hidden sm:table-cell text-slate-600 text-sm">
                        {entry.task_title || "—"}
                      </TD>
                      <TD className="text-sm">{entry.start_time.slice(0, 5)}</TD>
                      <TD className="hidden sm:table-cell text-sm">
                        {entry.end_time ? entry.end_time.slice(0, 5) : "—"}
                      </TD>
                      <TD>
                        <span className="text-sm font-medium text-slate-900">
                          {entry.duration ? formatMinutes(parseDuration(entry.duration)) : "Running"}
                        </span>
                      </TD>
                      <TD className="hidden md:table-cell max-w-[200px] truncate text-sm text-slate-600">
                        {entry.description || "—"}
                      </TD>
                      <TD>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditForm(entry)}
                          >
                            Edit
                          </Button>
                          {canDelete && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeleteTarget(entry)}
                            >
                              Delete
                            </Button>
                          )}
                        </div>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </TableContainer>
          )}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        open={formOpen}
        onClose={closeForm}
        title={editingEntry ? "Edit time entry" : "Log time"}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={closeForm}>
              Cancel
            </Button>
            <Button
              type="submit"
              form="time-entry-form"
              isLoading={createMutation.isPending || updateMutation.isPending}
            >
              {editingEntry ? "Save changes" : "Log entry"}
            </Button>
          </>
        }
      >
        <form id="time-entry-form" onSubmit={handleSubmit} className="space-y-4">
          {formGlobalError && (
            <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {formGlobalError}
            </div>
          )}

          <Select
            label="Project"
            value={form.project}
            onChange={(e) => {
              setForm((f) => ({ ...f, project: e.target.value, task: null }))
              setFormErrors((fe) => {
                const next = { ...fe }
                delete next.project
                return next
              })
            }}
            error={formErrors.project}
            required
          >
            <option value="">Select a project</option>
            {projectsQuery.data?.results.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>

          {form.project && (
            <Select
              label="Task (optional)"
              value={form.task ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, task: e.target.value || null }))}
            >
              <option value="">No task</option>
              {tasksQuery.data?.results.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </Select>
          )}

          <div className="grid gap-4 sm:grid-cols-3">
            <Input
              label="Date"
              type="date"
              value={form.date}
              onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
              required
            />
            <Input
              label="Start time"
              type="time"
              value={form.start_time}
              onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
              error={formErrors.start_time}
              required
            />
            <Input
              label="End time (optional)"
              type="time"
              value={form.end_time ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value || null }))}
              error={formErrors.end_time}
            />
          </div>

          <Input
            label="Description"
            placeholder="What did you work on?"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete time entry"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              isLoading={deleteMutation.isPending}
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
            >
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Are you sure you want to delete this time entry for{" "}
          <span className="font-medium text-slate-900">{deleteTarget?.project_name}</span>{" "}
          on {deleteTarget?.date}?
        </p>
      </Modal>
    </div>
  )
}

function parseDuration(iso: string): number {
  const parts = iso.split(":")
  if (parts.length < 3) return 0
  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10) + parseInt(parts[2], 10) / 60
}
