import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { ProjectDetailsPage } from "../ProjectDetailsPage"
import * as authHook from "@/hooks/useAuth"
import * as projectsApi from "@/features/projects/api"
import * as customersApi from "@/features/customers/api"
import * as teamApi from "@/features/team/api"

vi.mock("@/hooks/useAuth", () => ({ useAuth: vi.fn() }))

vi.mock("@/features/projects/api", () => ({
  fetchProject: vi.fn(),
  updateProject: vi.fn(),
  archiveProject: vi.fn(),
  deleteProject: vi.fn(),
}))

vi.mock("@/features/customers/api", () => ({
  fetchCustomers: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
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
})

describe("ProjectDetailsPage delete", () => {
  it("BUG-3: deleting a project navigates away without refetching the deleted resource", async () => {
    const user = userEvent.setup()
    const { qc } = renderPage()

    // Detail query loads once on mount.
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    expect(projectsApi.fetchProject).toHaveBeenCalledTimes(1)
    expect(qc.getQueryData(["project", "proj-1"])).toBeDefined()

    // Open the delete confirmation and confirm.
    await user.click(screen.getByRole("button", { name: /^delete$/i }))
    const confirm = screen.getByRole("button", { name: /delete permanently/i })
    expect(confirm).toBeEnabled()
    await user.click(confirm)

    // onSuccess navigates away to the projects list...
    await waitFor(() => {
      expect(screen.getByText("PROJECTS_LIST")).toBeInTheDocument()
    })

    // ...and the deleted resource is never refetched: fetchProject is still
    // only called once (the initial load). Before the fix, invalidating the
    // detail query retriggered a refetch of the deleted resource, producing a
    // spurious 404 (GET /projects/{id}/).
    expect(projectsApi.fetchProject).toHaveBeenCalledTimes(1)

    // The deleted project's cache entry is removed too.
    expect(qc.getQueryData(["project", "proj-1"])).toBeUndefined()
  })
})
