import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { ProjectDetailsPage } from "../ProjectDetailsPage"
import * as authHook from "@/hooks/useAuth"
import * as projectsApi from "@/features/projects/api"
import * as customersApi from "@/features/customers/api"
import * as teamApi from "@/features/team/api"
import * as tasksApi from "@/features/tasks/api"
import * as timeApi from "@/features/time-tracking/api"

vi.mock("@/hooks/useAuth", () => ({ useAuth: vi.fn() }))

vi.mock("@/features/projects/api", () => ({
  fetchProject: vi.fn(),
  updateProject: vi.fn(),
  archiveProject: vi.fn(),
  restoreProject: vi.fn(),
  deleteProject: vi.fn(),
  fetchProjectMembers: vi.fn(),
  addProjectMember: vi.fn(),
  removeProjectMember: vi.fn(),
}))

vi.mock("@/features/customers/api", () => ({
  fetchCustomers: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
}))

vi.mock("@/features/tasks/api", () => ({
  fetchTasks: vi.fn(),
}))

vi.mock("@/features/time-tracking/api", () => ({
  fetchTimeEntries: vi.fn(),
}))

const MOCK_PROJECT = {
  id: "proj-1",
  name: "Website Redesign",
  description: "",
  customer: null,
  customer_name: null,
  manager: null,
  manager_name: null,
  status: "IN_PROGRESS" as const,
  priority: "HIGH" as const,
  start_date: "2025-06-01",
  deadline: "2025-09-30",
  progress: 50,
  health: "ON_TRACK" as const,
  task_count: 4,
  done_count: 2,
  in_progress_count: 1,
  todo_count: 1,
  overdue_count: 0,
  tracked_hours: 12.5,
  member_count: 0,
  members: [],
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

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

function renderPage(queryClient?: QueryClient) {
  const qc = queryClient ?? makeQueryClient()
  return {
    qc,
    ...render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/projects/proj-1"]}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetailsPage />} />
            <Route path="/projects" element={<div>PROJECTS_LIST</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(projectsApi.fetchProject).mockResolvedValue(MOCK_PROJECT)
  vi.mocked(projectsApi.deleteProject).mockResolvedValue(undefined)
  vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(teamApi.fetchMembers).mockResolvedValue([])
  vi.mocked(tasksApi.fetchTasks).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(timeApi.fetchTimeEntries).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(projectsApi.fetchProjectMembers).mockResolvedValue([])
})

describe("ProjectDetailsPage delete", () => {
  it("BUG-3: deleting a project navigates away without refetching the deleted resource", async () => {
    const user = userEvent.setup()
    const { qc } = renderPage()

    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    expect(projectsApi.fetchProject).toHaveBeenCalledTimes(1)
    expect(qc.getQueryData(["project", "proj-1"])).toBeDefined()

    await user.click(screen.getByRole("button", { name: /^delete$/i }))
    const confirm = screen.getByRole("button", { name: /delete permanently/i })
    expect(confirm).toBeEnabled()
    await user.click(confirm)

    await waitFor(() => {
      expect(screen.getByText("PROJECTS_LIST")).toBeInTheDocument()
    })

    expect(projectsApi.fetchProject).toHaveBeenCalledTimes(1)

    expect(qc.getQueryData(["project", "proj-1"])).toBeUndefined()
  })
})

describe("ProjectDetailsPage workspace", () => {
  it("shows derived metrics in the overview tab", async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    expect(screen.getByText("50%")).toBeInTheDocument()
    expect(screen.getByText("On track")).toBeInTheDocument()
    expect(screen.getByText(/Tracked time/)).toBeInTheDocument()
    expect(screen.getByText("12.5h")).toBeInTheDocument()
  })

  it("switches between tabs and fetches per-tab data", async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    await user.click(screen.getByRole("button", { name: /Tasks/ }))
    await waitFor(() => {
      expect(tasksApi.fetchTasks).toHaveBeenCalled()
    })
    expect(screen.getByText(/No tasks yet/)).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Members/ }))
    await waitFor(() => {
      expect(projectsApi.fetchProjectMembers).toHaveBeenCalled()
    })
    expect(screen.getByText(/No members assigned/)).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /Activity/ }))
    await waitFor(() => {
      expect(screen.getByText(/No activity yet/)).toBeInTheDocument()
    })
  })

  it("shows a Restore action for archived projects", async () => {
    vi.mocked(projectsApi.fetchProject).mockResolvedValue({
      ...MOCK_PROJECT,
      status: "ARCHIVED",
    })
    vi.mocked(projectsApi.restoreProject).mockResolvedValue({
      ...MOCK_PROJECT,
      status: "IN_PROGRESS",
    })

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    await user.click(screen.getByRole("button", { name: /restore/i }))
    const dialog = screen.getByRole("dialog")
    expect(dialog).toBeInTheDocument()
    const { getByRole: dialogGetByRole } = within(dialog)
    await user.click(dialogGetByRole("button", { name: /^Restore$/ }))
    expect(projectsApi.restoreProject).toHaveBeenCalled()
  })
})
