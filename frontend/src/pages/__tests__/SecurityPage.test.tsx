import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { SecurityPage } from "../SecurityPage"
import type { SessionResponse } from "@/types/auth"
import * as authHook from "@/hooks/useAuth"
import * as securityApi from "@/features/auth/securityApi"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/auth/securityApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/auth/securityApi")>()
  return {
    ...actual,
    fetchSessions: vi.fn(),
    fetchSecurityEvents: vi.fn(),
    revokeSession: vi.fn(),
    revokeAllOtherSessions: vi.fn(),
    verifyEmail: vi.fn(),
    changePassword: vi.fn(),
  }
})

const MOCK_USER: SessionResponse = {
  id: "u1",
  email: "test@example.com",
  first_name: "Test",
  last_name: "User",
  avatar: null,
  full_name: "Test User",
  memberships: [],
  active_company: null,
  is_email_verified: false,
}

function mockAuth(user = MOCK_USER) {
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user,
    activeCompany: null,
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn().mockResolvedValue(undefined),
  })
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  return render(
    <QueryClientProvider client={makeQueryClient()}>
      <SecurityPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(securityApi.fetchSessions).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(securityApi.fetchSecurityEvents).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
})

describe("SecurityPage", () => {
  it("shows email verification prompt when not verified", () => {
    mockAuth({ ...MOCK_USER, is_email_verified: false })
    renderPage()
    expect(screen.getByText(/verify your email to unlock all features/i)).toBeInTheDocument()
  })

  it("shows sessions heading", () => {
    mockAuth()
    renderPage()
    expect(screen.getByText(/^Active Sessions$/i)).toBeInTheDocument()
  })

  it("shows logout all others button", () => {
    mockAuth()
    renderPage()
    expect(screen.getByRole("button", { name: /logout all others/i })).toBeInTheDocument()
  })

  it("shows security activity section and events", async () => {
    vi.mocked(securityApi.fetchSecurityEvents).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: "e1",
          event_type: "password_changed",
          ip_address: "203.0.113.5",
          metadata: {},
          created_at: "2026-01-01T10:00:00Z",
        },
      ],
    })
    mockAuth()
    renderPage()
    await screen.findByText(/Password changed/)
    expect(screen.getByText(/Security Activity/)).toBeInTheDocument()
    expect(screen.getByText("203.0.113.5")).toBeInTheDocument()
  })

  it("shows an empty state when no security events exist", async () => {
    mockAuth()
    renderPage()
    await screen.findByText(/No security activity recorded yet/)
  })

  it("confirms before logging out all other sessions", async () => {
    const user = userEvent.setup()
    vi.mocked(securityApi.fetchSessions).mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: "s1",
          browser: "Chrome",
          device: "Windows",
          ip_address: "127.0.0.1",
          created_at: "2026-01-01T00:00:00Z",
          last_activity: "2026-01-01T00:00:00Z",
          is_current: true,
        },
        {
          id: "s2",
          browser: "Firefox",
          device: "Linux",
          ip_address: "127.0.0.2",
          created_at: "2026-01-02T00:00:00Z",
          last_activity: "2026-01-02T00:00:00Z",
          is_current: false,
        },
      ],
    })
    mockAuth()
    renderPage()

    await user.click(await screen.findByRole("button", { name: /^logout all others$/i }))

    const dialog = await screen.findByRole("dialog")
    expect(within(dialog).getByText(/Logout all other sessions\?/i)).toBeInTheDocument()
    await user.click(within(dialog).getByRole("button", { name: /logout all others/i }))
    expect(securityApi.revokeAllOtherSessions).toHaveBeenCalledTimes(1)
  })

  it("shows a loading state while security events load", async () => {
    vi.mocked(securityApi.fetchSecurityEvents).mockImplementation(
      () => new Promise(() => {}),
    )
    mockAuth()
    renderPage()
    expect(screen.getByText(/Recent security events on your account/i)).toBeInTheDocument()
  })
})