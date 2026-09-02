import { useCallback, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { ErrorState } from "@/components/ui/ErrorState"
import { LoadingState } from "@/components/ui/LoadingState"
import { useAuth } from "@/hooks/useAuth"
import { KanbanBoard } from "@/features/tasks/components/KanbanBoard"
import { CreateTaskModal } from "@/features/tasks/components/CreateTaskModal"
import {
  fetchAllTasks,
  fetchLabels,
  changeTaskStatus,
  type TaskListParams,
} from "@/features/tasks/api"
import { fetchProjects } from "@/features/projects/api"
import { fetchMembers } from "@/features/team/api"
import { queryKeys } from "@/utils/queryKeys"
import type { Task, TaskStatus } from "@/types/task"

const PRIORITY_OPTIONS = [
  { value: "", label: "All priorities" },
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "URGENT", label: "Urgent" },
]

export function TasksPage() {
  const { activeCompany } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const companyId = activeCompany?.id ?? null

  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [priorityFilter, setPriorityFilter] = useState("")
  const [assigneeFilter, setAssigneeFilter] = useState("")
  const [labelFilter, setLabelFilter] = useState("")

  const [createOpen, setCreateOpen] = useState(false)
  const [createStatus, setCreateStatus] = useState<TaskStatus>("TODO")

  const queryParams = useMemo<TaskListParams>(() => {
    const params: TaskListParams = { page_size: 200 }
    if (debouncedSearch) params.search = debouncedSearch
    if (priorityFilter) params.priority = priorityFilter
    if (assigneeFilter) params.assignee = assigneeFilter
    if (labelFilter) params.label = labelFilter
    return params
  }, [debouncedSearch, priorityFilter, assigneeFilter, labelFilter])

  const tasksQuery = useQuery({
    queryKey: [...queryKeys.tasks(companyId), queryParams],
    queryFn: () => fetchAllTasks(queryParams),
    enabled: companyId !== null,
  })

  const projectsQuery = useQuery({
    queryKey: queryKeys.projects(companyId),
    queryFn: () => fetchProjects({ page_size: 100 }),
    enabled: companyId !== null,
  })

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null,
  })

  const labelsQuery = useQuery({
    queryKey: queryKeys.labels(companyId),
    queryFn: () => fetchLabels({ page_size: 100 }),
    enabled: companyId !== null,
  })

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.tasks(companyId) })
  }, [queryClient, companyId])

  const statusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: TaskStatus }) =>
      changeTaskStatus(taskId, status),
    onSuccess: () => invalidate(),
    onError: () => invalidate(),
  })

  const handleStatusChange = useCallback(
    (taskId: string, newStatus: TaskStatus) => {
      queryClient.setQueryData(
        [...queryKeys.tasks(companyId), queryParams],
        (old: Awaited<ReturnType<typeof fetchAllTasks>> | undefined) => {
          if (!old) return old
          return {
            ...old,
            results: old.results.map((t: Task) =>
              t.id === taskId ? { ...t, status: newStatus } : t,
            ),
          }
        },
      )

      statusMutation.mutate(
        { taskId, status: newStatus },
        {
          onError: () => {
            void queryClient.invalidateQueries({
              queryKey: queryKeys.tasks(companyId),
            })
          },
        },
      )
    },
    [queryClient, companyId, queryParams, statusMutation],
  )

  const handleTaskClick = useCallback(
    (task: Task) => {
      navigate(`/tasks/${task.id}`)
    },
    [navigate],
  )

  const handleQuickCreate = useCallback((status: TaskStatus) => {
    setCreateStatus(status)
    setCreateOpen(true)
  }, [])

  const searchTimeout = useMemo(() => {
    let timer: ReturnType<typeof setTimeout>
    return (value: string) => {
      clearTimeout(timer)
      timer = setTimeout(() => setDebouncedSearch(value), 300)
      return () => clearTimeout(timer)
    }
  }, [])

  const tasks = tasksQuery.data?.results ?? []

  return (
    <div>
      <PageHeader
        title="Tasks"
        description="Track and manage work across your projects."
        actions={<Button onClick={() => setCreateOpen(true)}>New task</Button>}
      />

      {tasksQuery.isPending && <LoadingState label="Loading tasks…" />}

      {tasksQuery.isError && (
        <ErrorState
          title="Could not load tasks"
          description="Check your connection and try again."
          onRetry={() => void tasksQuery.refetch()}
        />
      )}

      {tasksQuery.data && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Input
              placeholder="Search tasks…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                searchTimeout(e.target.value)
              }}
              className="sm:max-w-xs"
            />
            <Select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="sm:max-w-[160px]"
            >
              {PRIORITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </Select>
            <Select
              aria-label="Filter by assignee"
              value={assigneeFilter}
              onChange={(e) => setAssigneeFilter(e.target.value)}
              className="sm:max-w-[160px]"
            >
              <option value="">All assignees</option>
              {membersQuery.data?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.full_name || m.email}
                </option>
              ))}
            </Select>
            <Select
              aria-label="Filter by label"
              value={labelFilter}
              onChange={(e) => setLabelFilter(e.target.value)}
              className="sm:max-w-[160px]"
            >
              <option value="">All labels</option>
              {labelsQuery.data?.results.map((label) => (
                <option key={label.id} value={label.id}>
                  {label.name}
                </option>
              ))}
            </Select>
            {tasks.length > 0 && (
              <span className="ml-auto text-sm text-slate-500">
                {tasks.length} task{tasks.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {tasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 py-16">
              <p className="text-sm font-medium text-slate-500">
                {debouncedSearch || priorityFilter || assigneeFilter || labelFilter
                  ? "No tasks match your filters."
                  : "No tasks yet. Create your first task to get started."}
              </p>
              {!debouncedSearch &&
                !priorityFilter &&
                !assigneeFilter &&
                !labelFilter && (
                  <Button className="mt-4" onClick={() => setCreateOpen(true)}>
                    New task
                  </Button>
                )}
            </div>
          ) : (
            <KanbanBoard
              tasks={tasks}
              onStatusChange={handleStatusChange}
              onTaskClick={handleTaskClick}
              onQuickCreate={handleQuickCreate}
            />
          )}
        </div>
      )}

      <CreateTaskModal
        open={createOpen}
        defaultStatus={createStatus}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false)
          invalidate()
        }}
        projects={projectsQuery.data?.results ?? []}
        members={membersQuery.data ?? []}
        labels={labelsQuery.data?.results ?? []}
      />
    </div>
  )
}
