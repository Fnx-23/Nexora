import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { TaskDetailsPage } from "../TaskDetailsPage"
import * as authHook from "@/hooks/useAuth"
import * as tasksApi from "@/features/tasks/api"
import * as projectsApi from "@/features/projects/api"
import * as teamApi from "@/features/team/api"
import type { TaskDetail } from "@/types/task"
import type { Member } from "@/types/team"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/tasks/api", () => ({
  fetchTask: vi.fn(),
  fetchTaskChecklist: vi.fn(),
  fetchTaskComments: vi.fn(),
  fetchTaskSubtasks: vi.fn(),
  addTaskChecklistItem: vi.fn(),
  updateTaskChecklistItem: vi.fn(),
  deleteTaskChecklistItem: vi.fn(),
  addTaskComment: vi.fn(),
  updateTaskComment: vi.fn(),
  deleteTaskComment: vi.fn(),
  addTaskSubtask: vi.fn(),
  updateTaskSubtask: vi.fn(),
  deleteTaskSubtask: vi.fn(),
  fetchLabels: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
  changeTaskStatus: vi.fn(),
  createLabel: vi.fn(),
  updateLabel: vi.fn(),
  deleteLabel: vi.fn(),
}))

vi.mock("@/features/projects/api", () => ({
  fetchProjects: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

const TASK: TaskDetail = {
  id: "t1",
  title: "Fix login bug",
  description: "SSO broken",
  project: "p1",
  project_name: "Sprint 1",
  status: "IN_PROGRESS",
  priority: "HIGH",
  assignee: "u2",
  assignee_name: "Bob Employee",
  created_by: "u1",
  created_by_name: "Alice Admin",
  due_date: "2099-12-01",
  labels: [{ id: "l1", name: "bug", color: "#ef4444", created_at: "2025-01-01T00:00:00Z" }],
  checklist_total: 2,
  checklist_done: 1,
  subtask_total: 1,
  subtask_done: 0,
  comments_count: 1,
  recent_activity: [],
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T10:00:00Z",
}

function mockAuth(role: "ADMIN" | "MANAGER" | "EMPLOYEE" = "ADMIN") {
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user: {
      id: "u1",
      email: "admin@test.com",
      first_name: "Admin",
      last_name: "Test",
      avatar: null,
      full_name: "Admin Test",
    },
    activeCompany: { id: "c1", name: "TestCo", slug: "testco" },
    role,
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function renderPage(queryClient?: QueryClient) {
  const qc = queryClient ?? makeQueryClient()
  return {
    qc,
    ...render(
      <MemoryRouter initialEntries={["/tasks/t1"]}>
        <QueryClientProvider client={qc}>
          <Routes>
            <Route path="/tasks/:id" element={<TaskDetailsPage />} />
          </Routes>
        </QueryClientProvider>
      </MemoryRouter>,
    ),
  }
}

const CHECKLIST = [
  { id: "c1", task: "t1", text: "Repro the bug", completed: true, position: 1, created_at: "2025-01-15T10:00:00Z" },
  { id: "c2", task: "t1", text: "Fix root cause", completed: false, position: 2, created_at: "2025-01-15T10:00:00Z" },
]

const COMMENTS = [
  {
    id: "m1",
    task: "t1",
    author: "u1",
    author_name: "Admin Test",
    body: "I can repro this consistently.",
    created_at: "2025-01-15T11:00:00Z",
    updated_at: "2025-01-15T11:00:00Z",
  },
]

const SUBTASKS = [
  { id: "s1", task: "t1", title: "Add regression test", completed: false, position: 1, created_at: "2025-01-15T10:00:00Z" },
]

const MEMBERS: Member[] = [
  {
    id: "u1",
    email: "admin@test.com",
    first_name: "Admin",
    last_name: "Test",
    full_name: "Admin Test",
    role: "ADMIN",
    membership_id: "m-u1",
    membership_active: true,
    joined_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "u2",
    email: "bob@test.com",
    first_name: "Bob",
    last_name: "Employee",
    full_name: "Bob Employee",
    role: "EMPLOYEE",
    membership_id: "m-u2",
    membership_active: true,
    joined_at: "2025-01-01T00:00:00Z",
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(tasksApi.fetchTask).mockResolvedValue(TASK)
  vi.mocked(tasksApi.fetchTaskChecklist).mockResolvedValue(CHECKLIST)
  vi.mocked(tasksApi.fetchTaskComments).mockResolvedValue(COMMENTS)
  vi.mocked(tasksApi.fetchTaskSubtasks).mockResolvedValue(SUBTASKS)
  vi.mocked(tasksApi.fetchLabels).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [TASK.labels[0]],
  })
  vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(teamApi.fetchMembers).mockResolvedValue(MEMBERS)
})

describe("TaskDetailsPage", () => {
  it("shows loading state then renders overview", async () => {
    renderPage()
    expect(screen.getByText(/Loading task/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    expect(screen.getByText("Sprint 1")).toBeInTheDocument()
    expect(screen.getByText("Bob Employee")).toBeInTheDocument()
    expect(screen.getAllByText("bug").length).toBeGreaterThan(0)
  })

  it("renders all section tabs", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: /Overview/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Comments/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Checklist/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Subtasks/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Attachments/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Activity/i })).toBeInTheDocument()
  })

  it("shows an error state when the task cannot be loaded", async () => {
    vi.mocked(tasksApi.fetchTask).mockRejectedValue(new Error("Not found"))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Could not load task")).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: /Back to tasks/i })).toBeInTheDocument()
  })

  it("loads and renders checklist items with progress", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /Checklist/i }))
    await waitFor(() => {
      expect(screen.getByText("Repro the bug")).toBeInTheDocument()
    })
    expect(screen.getByText("Fix root cause")).toBeInTheDocument()
  })

  it("adds a checklist item", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /Checklist/i }))
    await waitFor(() => {
      expect(screen.getByText("Repro the bug")).toBeInTheDocument()
    })
    await user.type(screen.getByPlaceholderText(/Add a checklist item/i), "Verify the fix")
    await user.click(screen.getByRole("button", { name: /^Add$/ }))
    await waitFor(() => {
      const calls = vi.mocked(tasksApi.addTaskChecklistItem).mock.calls
      expect(calls.length).toBeGreaterThan(0)
      expect(calls[0][0]).toBe("t1")
      expect(calls[0][1]).toBe("Verify the fix")
    })
  })

  it("loads and renders comments", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /Comments/i }))
    await waitFor(() => {
      expect(screen.getByText("I can repro this consistently.")).toBeInTheDocument()
    })
    expect(screen.getByText("Admin Test")).toBeInTheDocument()
  })

  it("posts a comment", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /Comments/i }))
    await waitFor(() => {
      expect(screen.getByText("I can repro this consistently.")).toBeInTheDocument()
    })
    await user.type(screen.getByPlaceholderText(/Add a comment/i), "Assigning to Bob.")
    await user.click(screen.getByRole("button", { name: /^Post$/ }))
    await waitFor(() => {
      const calls = vi.mocked(tasksApi.addTaskComment).mock.calls
      expect(calls.length).toBeGreaterThan(0)
      expect(calls[0][0]).toBe("t1")
      expect(calls[0][1]).toBe("Assigning to Bob.")
    })
  })

  it("renders subtasks and their progress", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /Subtasks/i }))
    await waitFor(() => {
      expect(screen.getByText("Add regression test")).toBeInTheDocument()
    })
  })

  it("allows admins to delete the task", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /Delete/i }))
    await user.click(screen.getByRole("button", { name: /Delete permanently/i }))
    await waitFor(() => {
      const calls = vi.mocked(tasksApi.deleteTask).mock.calls
      expect(calls.length).toBeGreaterThan(0)
      expect(calls[0][0]).toBe("t1")
    })
  })
})