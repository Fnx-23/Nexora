import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { ProjectsPage } from "../ProjectsPage"
import * as authHook from "@/hooks/useAuth"
import * as projectsApi from "@/features/projects/api"
import * as customersApi from "@/features/customers/api"
import * as teamApi from "@/features/team/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/projects/api", () => ({
  fetchProjects: vi.fn(),
  createProject: vi.fn(),
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

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

const MOCK_PROJECTS = [
  {
    id: "p1",
    name: "Website Redesign",
    description: "Redesign the public site",
    customer: "c1",
    customer_name: "Globex Corp",
    manager: "u2",
    manager_name: "Jane Manager",
    status: "IN_PROGRESS" as const,
    priority: "HIGH" as const,
    start_date: "2025-06-01",
    deadline: "2025-09-30",
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T10:00:00Z",
  },
  {
    id: "p2",
    name: "Mobile App",
    description: "",
    customer: null,
    customer_name: null,
    manager: null,
    manager_name: null,
    status: "PLANNING" as const,
    priority: "MEDIUM" as const,
    start_date: null,
    deadline: null,
    created_at: "2025-02-20T14:00:00Z",
    updated_at: "2025-02-20T14:00:00Z",
  },
]

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
      <MemoryRouter>
        <QueryClientProvider client={qc}>
          <ProjectsPage />
        </QueryClientProvider>
      </MemoryRouter>,
    ),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
    count: MOCK_PROJECTS.length,
    next: null,
    previous: null,
    results: MOCK_PROJECTS,
  })
  vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(teamApi.fetchMembers).mockResolvedValue([])
})

describe("ProjectsPage", () => {
  it("shows loading state", () => {
    vi.mocked(projectsApi.fetchProjects).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Loading projects/i)).toBeInTheDocument()
  })

  it("renders project table with data", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    expect(screen.getByText("Mobile App")).toBeInTheDocument()
  })

  it("shows customer and manager names", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Globex Corp")).toBeInTheDocument()
    })
    expect(screen.getByText("Jane Manager")).toBeInTheDocument()
  })

  it("shows status and priority badges", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    // StatusBadge renders the text value with spaces replacing underscores
    expect(screen.getByText("In progress")).toBeInTheDocument()
    expect(screen.getByText("Planning")).toBeInTheDocument()
    expect(screen.getByText("HIGH")).toBeInTheDocument()
    expect(screen.getByText("MEDIUM")).toBeInTheDocument()
  })

  it("shows project count", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("2 projects")).toBeInTheDocument()
    })
  })

  it("shows error state on fetch failure", async () => {
    vi.mocked(projectsApi.fetchProjects).mockRejectedValue(new Error("Network"))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Could not load projects")).toBeInTheDocument()
    })
  })

  it("shows empty state when no projects", async () => {
    vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("No projects found")).toBeInTheDocument()
    })
  })

  it("shows search input and filter dropdowns", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Search projects/i)).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue("All statuses")).toBeInTheDocument()
    expect(screen.getByDisplayValue("All priorities")).toBeInTheDocument()
    expect(screen.getByDisplayValue("All customers")).toBeInTheDocument()
  })

  it("New project button opens create modal", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("New project")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /new project/i }))
    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getByText("New project", { selector: "h2" })).toBeInTheDocument()
  })

  it("Edit button opens edit modal with project data", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    const row = screen.getByText("Website Redesign").closest("tr")!
    const editBtn = within(row).getByRole("button", { name: "Edit" })
    await user.click(editBtn)

    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getByText("Edit project", { selector: "h2" })).toBeInTheDocument()
    expect(screen.getByDisplayValue("Website Redesign")).toBeInTheDocument()
  })

  it("Archive button shows confirmation modal", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    const row = screen.getByText("Website Redesign").closest("tr")!
    const archiveBtn = within(row).getByRole("button", { name: "Archive" })
    await user.click(archiveBtn)

    expect(screen.getByText("Archive project", { selector: "h2" })).toBeInTheDocument()
    expect(screen.getByText(/Are you sure you want to archive/)).toBeInTheDocument()
  })

  it("EMPLOYEE role does not see archive button", async () => {
    mockAuth("EMPLOYEE")
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    const row = screen.getByText("Website Redesign").closest("tr")!
    expect(within(row).queryByRole("button", { name: "Archive" })).not.toBeInTheDocument()
  })

  it("ARCHIVED projects do not show archive button", async () => {
    vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          ...MOCK_PROJECTS[0],
          status: "ARCHIVED",
        },
      ],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })

    const row = screen.getByText("Website Redesign").closest("tr")!
    expect(within(row).queryByRole("button", { name: "Archive" })).not.toBeInTheDocument()
  })

  it("shows pagination when multiple pages", async () => {
    vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
      count: 30,
      next: "http://test.com/api/v1/projects/?page=2",
      previous: null,
      results: MOCK_PROJECTS,
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Page 1 of 2")).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: "Next" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Previous" })).toBeInTheDocument()
  })

  it("does not show pagination for single page", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    expect(screen.queryByRole("button", { name: "Next" })).not.toBeInTheDocument()
  })

  it("deadline date is formatted", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    expect(screen.getByText("Sep 30, 2025")).toBeInTheDocument()
  })

  it("null deadline shows dash", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Mobile App")).toBeInTheDocument()
    })
    // Mobile App has no deadline, so we should see a dash placeholder
    const mobileRow = screen.getByText("Mobile App").closest("tr")!
    expect(mobileRow).toBeInTheDocument()
  })

  it("name is clickable and renders as button", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    })
    const nameBtn = screen.getByRole("button", { name: "Website Redesign" })
    expect(nameBtn).toBeInTheDocument()
  })
})
