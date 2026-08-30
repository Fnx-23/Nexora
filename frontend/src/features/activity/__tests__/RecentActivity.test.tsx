import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { RecentActivity } from "@/features/activity/RecentActivity"
import type { Activity } from "@/types/activity"
import * as authHook from "@/hooks/useAuth"
import * as activityApi from "@/features/activity/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

// Keep the real query keys; only stub the network call.
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
    action: "project.status_changed",
    action_display: "Project status changed",
    entity_type: "project",
    entity_id: "p1",
    actor: "u1",
    actor_name: "Admin Test",
    metadata: { name: "Website Redesign", old_status: "PLANNING", new_status: "IN_PROGRESS" },
    timestamp: "2025-08-20T13:00:00Z",
  },
  {
    id: "a3",
    action: "team.role_changed",
    action_display: "Team role changed",
    entity_type: "membership",
    entity_id: "m1",
    actor: null,
    actor_name: null,
    metadata: { member_user_id: "u2", old_role: "EMPLOYEE", new_role: "MANAGER" },
    timestamp: "2025-08-19T10:00:00Z",
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

function renderCard(props = {}) {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={makeQueryClient()}>
        <RecentActivity {...props} />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(activityApi.fetchActivities).mockResolvedValue({
    count: ACTIVITIES.length,
    next: null,
    previous: null,
    results: ACTIVITIES,
  })
})

describe("RecentActivity", () => {
  it("renders recent audit-log entries with subjects and details", async () => {
    renderCard()
    await waitFor(() => {
      expect(screen.getByText("Acme Corp")).toBeInTheDocument()
    })
    expect(screen.getByText("Website Redesign")).toBeInTheDocument()
    expect(screen.getByText("Customer created")).toBeInTheDocument()
    // Humanized status transition derived from metadata.
    expect(screen.getByText("Planning → In progress")).toBeInTheDocument()
    expect(screen.getByText("Employee → Manager")).toBeInTheDocument()
    // Actor attribution (appears once per row).
    expect(screen.getAllByText(/Admin Test/).length).toBeGreaterThanOrEqual(1)
    // System-attributed row shows "System".
    expect(screen.getByText(/System/)).toBeInTheDocument()
  })

  it("requests only the configured number of recent events, newest first", async () => {
    renderCard({ limit: 5 })
    await waitFor(() => {
      expect(vi.mocked(activityApi.fetchActivities)).toHaveBeenCalledWith({
        page_size: 5,
        ordering: "-timestamp",
      })
    })
  })

  it("links to the full activity page", async () => {
    renderCard()
    const link = await screen.findByRole("link", { name: "View all" })
    expect(link).toHaveAttribute("href", "/activity")
  })

  it("can hide the 'View all' link", async () => {
    renderCard({ showViewAll: false })
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument())
    expect(screen.queryByRole("link", { name: "View all" })).not.toBeInTheDocument()
  })

  it("shows an empty state when there is no activity", async () => {
    vi.mocked(activityApi.fetchActivities).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
    renderCard()
    await waitFor(() => {
      expect(screen.getByText("No activity yet.")).toBeInTheDocument()
    })
  })

  it("shows a retry affordance on error", async () => {
    vi.mocked(activityApi.fetchActivities).mockRejectedValue(new Error("Network"))
    renderCard()
    await waitFor(() => {
      expect(screen.getByText(/load activity/i)).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument()
  })

  it("shows skeletons while loading", () => {
    vi.mocked(activityApi.fetchActivities).mockReturnValue(new Promise(() => {}))
    const { container } = renderCard()
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0)
    expect(screen.queryByText("No activity yet.")).not.toBeInTheDocument()
  })

  it("does not fetch until a company is active", () => {
    mockAuth(null)
    renderCard()
    expect(vi.mocked(activityApi.fetchActivities)).not.toHaveBeenCalled()
  })
})
