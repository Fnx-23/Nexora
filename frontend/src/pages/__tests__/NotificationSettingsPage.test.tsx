import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { NotificationSettingsPage } from "../NotificationSettingsPage"
import type { NotificationPreference } from "@/types/notification"
import * as authHook from "@/hooks/useAuth"
import * as notificationsApi from "@/features/notifications/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/notifications/api", () => ({
  fetchNotificationPreferences: vi.fn(),
  updateNotificationPreferences: vi.fn(),
}))

const MOCK_PREFERENCES: NotificationPreference = {
  id: "p1",
  task_assigned: true,
  task_due_soon: true,
  task_overdue: true,
  task_comment: true,
  project_assigned: true,
  project_deadline: true,
  invitation_received: true,
  role_changed: true,
  email_task_assigned: true,
  email_task_due_soon: true,
  email_task_overdue: true,
  email_task_comment: true,
  email_project_assigned: true,
  email_project_deadline: true,
  email_invitation_received: true,
  email_role_changed: true,
}

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

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  return render(
    <QueryClientProvider client={makeQueryClient()}>
      <NotificationSettingsPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(notificationsApi.fetchNotificationPreferences).mockResolvedValue(MOCK_PREFERENCES)
  vi.mocked(notificationsApi.updateNotificationPreferences).mockImplementation(
    async (updates) => ({ ...MOCK_PREFERENCES, ...updates }),
  )
})

describe("NotificationSettingsPage", () => {
  it("renders both in-app and email preference groups", async () => {
    renderPage()
    await screen.findByRole("switch", { name: "In-app: Task assignments" })
    expect(screen.getByText(/In-app Notifications/)).toBeInTheDocument()
    expect(screen.getByText(/Email Notifications/)).toBeInTheDocument()
    expect(screen.getAllByText(/TestCo/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Task assignments/).length).toBeGreaterThanOrEqual(2)
  })

  it("toggles an in-app preference off and calls the API", async () => {
    const user = userEvent.setup()
    renderPage()
    const taskDueSwitch = await screen.findByRole("switch", { name: "In-app: Task due soon" })
    expect(taskDueSwitch).toHaveAttribute("aria-checked", "true")
    await user.click(taskDueSwitch)
    await waitFor(() => {
      expect(notificationsApi.updateNotificationPreferences).toHaveBeenCalledWith(
        { task_due_soon: false },
        expect.anything(),
      )
    })
  })

  it("toggles an email preference off and calls the API", async () => {
    const user = userEvent.setup()
    renderPage()
    const emailOverdueSwitch = await screen.findByRole("switch", { name: "Email: Task overdue" })
    expect(emailOverdueSwitch).toHaveAttribute("aria-checked", "true")
    await user.click(emailOverdueSwitch)
    await waitFor(() => {
      expect(notificationsApi.updateNotificationPreferences).toHaveBeenCalledWith(
        { email_task_overdue: false },
        expect.anything(),
      )
    })
  })

  it("reflects updated value after toggle", async () => {
    const user = userEvent.setup()
    renderPage()
    const taskOverdueSwitch = await screen.findByRole("switch", { name: "In-app: Task overdue" })
    await user.click(taskOverdueSwitch)
    await waitFor(() => {
      expect(taskOverdueSwitch).toHaveAttribute("aria-checked", "false")
    })
  })

  it("shows an error state when preferences fail to load", async () => {
    vi.mocked(notificationsApi.fetchNotificationPreferences).mockRejectedValue(new Error("nope"))
    renderPage()
    await waitFor(() => {
      const errors = screen.getAllByText(/Failed to load notification preferences/)
      expect(errors.length).toBeGreaterThan(0)
    })
  })
})