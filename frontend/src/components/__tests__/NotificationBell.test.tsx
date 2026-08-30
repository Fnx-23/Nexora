import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { NotificationBell } from "../layout/NotificationBell"
import * as authHook from "@/hooks/useAuth"
import * as notificationsApi from "@/features/notifications/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/notifications/api", () => ({
  fetchNotifications: vi.fn(),
  fetchUnreadCount: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

const MOCK_NOTIFICATIONS = [
  {
    id: "n1",
    verb: 'You have been assigned to task "Fix bug"',
    entity_type: "task",
    entity_id: "t1",
    entity_name: "Fix bug",
    link: "/tasks",
    is_read: false,
    actor_name: "Admin Test",
    created_at: "2025-08-20T10:00:00Z",
  },
  {
    id: "n2",
    verb: 'You have been assigned as manager of project "Website"',
    entity_type: "project",
    entity_id: "p1",
    entity_name: "Website",
    link: "/projects/p1",
    is_read: true,
    actor_name: "Admin Test",
    created_at: "2025-08-19T08:00:00Z",
  },
]

function mockAuth() {
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
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function renderBell(queryClient?: QueryClient) {
  const qc = queryClient ?? makeQueryClient()
  return {
    qc,
    ...render(
      <MemoryRouter>
        <QueryClientProvider client={qc}>
          <NotificationBell />
        </QueryClientProvider>
      </MemoryRouter>,
    ),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(notificationsApi.fetchUnreadCount).mockResolvedValue({ count: 2 })
  vi.mocked(notificationsApi.fetchNotifications).mockResolvedValue({
    count: MOCK_NOTIFICATIONS.length,
    next: null,
    previous: null,
    results: MOCK_NOTIFICATIONS,
  })
  vi.mocked(notificationsApi.markNotificationRead).mockResolvedValue(
    MOCK_NOTIFICATIONS[0],
  )
  vi.mocked(notificationsApi.markAllNotificationsRead).mockResolvedValue({ updated: 2 })
})

describe("NotificationBell", () => {
  describe("badge", () => {
    it("shows unread count badge", async () => {
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
    })

    it("hides badge when zero unread", async () => {
      vi.mocked(notificationsApi.fetchUnreadCount).mockResolvedValue({ count: 0 })
      renderBell()
      await waitFor(() => {
        expect(screen.getByLabelText(/Notifications/)).toBeInTheDocument()
      })
      expect(screen.queryByText("0")).not.toBeInTheDocument()
    })

    it("shows 9+ for counts above 9", async () => {
      vi.mocked(notificationsApi.fetchUnreadCount).mockResolvedValue({ count: 15 })
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("9+")).toBeInTheDocument()
      })
    })
  })

  describe("dropdown", () => {
    it("opens dropdown on click", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      expect(screen.getByText("Notifications", { selector: "h3" })).toBeInTheDocument()
    })

    it("shows notification items", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText(/assigned to task/)).toBeInTheDocument()
      })
      expect(screen.getByText(/assigned as manager/)).toBeInTheDocument()
    })

    it("shows unread indicator dot", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText(/assigned to task/)).toBeInTheDocument()
      })
      // Unread notification has a dot (bg-brand-500 span)
      const dots = document.querySelectorAll(".bg-brand-500")
      expect(dots.length).toBeGreaterThanOrEqual(1)
    })

    it("shows empty state", async () => {
      vi.mocked(notificationsApi.fetchNotifications).mockResolvedValue({
        count: 0,
        next: null,
        previous: null,
        results: [],
      })
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText("No notifications yet.")).toBeInTheDocument()
      })
    })

    it("shows mark all read button when there are unread", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText("Mark all read")).toBeInTheDocument()
      })
    })

    it("calls mark all read on click", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText("Mark all read")).toBeInTheDocument()
      })
      await user.click(screen.getByText("Mark all read"))
      expect(notificationsApi.markAllNotificationsRead).toHaveBeenCalled()
    })

    it("closes on outside click", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText("Notifications", { selector: "h3" })).toBeInTheDocument()
      })
      await user.click(document.body)
      await waitFor(() => {
        expect(screen.queryByText("Notifications", { selector: "h3" })).not.toBeInTheDocument()
      })
    })
  })

  describe("actor names", () => {
    it("shows actor name and time ago in dropdown", async () => {
      const user = userEvent.setup()
      renderBell()
      await waitFor(() => {
        expect(screen.getByText("2")).toBeInTheDocument()
      })
      await user.click(screen.getByRole("button", { name: /notifications/i }))
      await waitFor(() => {
        expect(screen.getByText(/assigned to task/)).toBeInTheDocument()
      })
      expect(screen.getAllByText(/Admin Test ·/).length).toBeGreaterThanOrEqual(1)
    })
  })
})
