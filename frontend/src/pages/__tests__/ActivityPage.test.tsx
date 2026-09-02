import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ActivityPage } from "../ActivityPage"
import type { Activity } from "@/types/activity"
import * as authHook from "@/hooks/useAuth"
import * as activityApi from "@/features/activity/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/activity/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/activity/api")>()
  return { ...actual, fetchActivities: vi.fn() }
})

const ACTIVITIES: Activity[] = [
  {
    id: "a1",
    action: "customer.created",
    action_display: "Customer created",
    entity_type: "customer",
    entity_id: "c1",
    actor: "u1",
    actor_name: "Admin Test",
    metadata: { name: "Acme Corp", status: "ACTIVE" },
    timestamp: "2025-08-20T14:00:00Z",
  },
  {
    id: "a2",
    action: "task.status_changed",
    action_display: "Task status changed",
    entity_type: "task",
    entity_id: "t1",
    actor: "u1",
    actor_name: "Admin Test",
    metadata: { title: "Fix login bug", old_status: "TODO", new_status: "IN_PROGRESS" },
    timestamp: "2025-08-20T13:00:00Z",
  },
]

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function mockAuth(companyId: string | null = "c1") {
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
    activeCompany: companyId ? { id: companyId, name: "TestCo", slug: "testco" } : null,
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function resolveWith(results: Activity[], count = results.length) {
  vi.mocked(activityApi.fetchActivities).mockResolvedValue({
    count,
    next: count > results.length ? "next" : null,
    previous: null,
    results,
  })
}

function renderPage() {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={makeQueryClient()}>
        <ActivityPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  resolveWith(ACTIVITIES)
})

describe("ActivityPage", () => {
  it("renders the audit-log entries", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Acme Corp")).toBeInTheDocument()
    })
    expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    expect(screen.getByText("Todo → In progress")).toBeInTheDocument()
  })

  it("shows the event count", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("2 events")).toBeInTheDocument()
    })
  })

  it("exposes type and action filters", async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument())
    expect(screen.getByLabelText("Filter by type")).toBeInTheDocument()
    expect(screen.getByLabelText("Filter by action")).toBeInTheDocument()
  })

  it("refetches scoped by entity type when the type filter changes", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument())

    await user.selectOptions(screen.getByLabelText("Filter by type"), "project")

    await waitFor(() => {
      expect(vi.mocked(activityApi.fetchActivities)).toHaveBeenCalledWith(
        expect.objectContaining({ entity_type: "project", page: 1 }),
      )
    })
  })

  it("refetches scoped by action when the action filter changes", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument())

    await user.selectOptions(screen.getByLabelText("Filter by action"), "task.status_changed")

    await waitFor(() => {
      expect(vi.mocked(activityApi.fetchActivities)).toHaveBeenCalledWith(
        expect.objectContaining({ action: "task.status_changed", page: 1 }),
      )
    })
  })

  it("paginates when there is more than one page", async () => {
    resolveWith(ACTIVITIES, 30)
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getByText("Page 1 of 2")).toBeInTheDocument())

    await user.click(screen.getByRole("button", { name: "Next" }))

    await waitFor(() => {
      expect(vi.mocked(activityApi.fetchActivities)).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
      )
    })
  })

  it("shows an empty state when there is no activity", async () => {
    resolveWith([])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/No activity/i)).toBeInTheDocument()
    })
  })

  it("shows an error state on fetch failure", async () => {
    vi.mocked(activityApi.fetchActivities).mockRejectedValue(new Error("Network"))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Could not load activity")).toBeInTheDocument()
    })
  })
})
