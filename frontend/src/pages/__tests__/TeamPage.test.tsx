import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { TeamPage } from "../TeamPage"
import * as authHook from "@/hooks/useAuth"
import * as teamApi from "@/features/team/api"
import type { Member } from "@/types/team"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
  fetchInvitations: vi.fn(),
  createInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
  resendInvitation: vi.fn(),
  changeMemberRole: vi.fn(),
  deactivateMember: vi.fn(),
  reactivateMember: vi.fn(),
  removeMember: vi.fn(),
}))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

const members: Member[] = [
  {
    id: "u1",
    email: "alice@acme.test",
    first_name: "Alice",
    last_name: "Smith",
    full_name: "Alice Smith",
    role: "ADMIN",
    membership_id: "m1",
    membership_active: true,
    joined_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "u2",
    email: "bob@acme.test",
    first_name: "Bob",
    last_name: "Jones",
    full_name: "Bob Jones",
    role: "EMPLOYEE",
    membership_id: "m2",
    membership_active: true,
    joined_at: "2026-02-01T00:00:00Z",
  },
]

function renderPage() {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <TeamPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  queryClient.clear()
  vi.mocked(teamApi.fetchInvitations).mockResolvedValue([])
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user: {
      id: "1",
      email: "owner@acme.test",
      first_name: "Owner",
      last_name: "Test",
      avatar: null,
      full_name: "Owner Test",
    },
    activeCompany: { id: "c1", name: "Acme", slug: "acme" },
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
})

describe("TeamPage", () => {
  it("shows loading state initially", () => {
    vi.mocked(teamApi.fetchMembers).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it("renders member table and invite button on success", async () => {
    vi.mocked(teamApi.fetchMembers).mockResolvedValue(members)
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })
    expect(screen.getByText("Bob Jones")).toBeInTheDocument()
    expect(screen.getByText("alice@acme.test")).toBeInTheDocument()
    expect(screen.getByText("bob@acme.test")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Invite member" })).toBeInTheDocument()
  })

  it("renders pending invitations for admins", async () => {
    vi.mocked(teamApi.fetchMembers).mockResolvedValue(members)
    vi.mocked(teamApi.fetchInvitations).mockResolvedValue([
      {
        id: "inv1",
        email: "carol@acme.test",
        role: "MANAGER",
        status: "PENDING",
        invited_by: "u1",
        invited_by_name: "Alice Smith",
        created_at: "2026-03-01T00:00:00Z",
        expires_at: "2026-03-08T00:00:00Z",
      },
    ])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("carol@acme.test")).toBeInTheDocument()
    })
    expect(screen.getByText("Pending invitations")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Resend" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Revoke" })).toBeInTheDocument()
  })

  it("does not show member management for employees", async () => {
    vi.mocked(teamApi.fetchMembers).mockResolvedValue(members)
    vi.mocked(authHook.useAuth).mockReturnValue({
      status: "authenticated",
      user: {
        id: "1",
        email: "owner@acme.test",
        first_name: "Owner",
        last_name: "Test",
        avatar: null,
        full_name: "Owner Test",
      },
      activeCompany: { id: "c1", name: "Acme", slug: "acme" },
      role: "EMPLOYEE",
      login: vi.fn(),
      logout: vi.fn(),
      refreshSession: vi.fn(),
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })
    expect(screen.queryByRole("button", { name: "Invite member" })).not.toBeInTheDocument()
    expect(screen.queryByText("Pending invitations")).not.toBeInTheDocument()
  })

  it("shows error state on failure", async () => {
    vi.mocked(teamApi.fetchMembers).mockRejectedValue(new Error("Network"))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Could not load your team")).toBeInTheDocument()
    })
  })

  it("shows empty state when no members", async () => {
    vi.mocked(teamApi.fetchMembers).mockResolvedValue([])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("No members yet")).toBeInTheDocument()
    })
  })
})
