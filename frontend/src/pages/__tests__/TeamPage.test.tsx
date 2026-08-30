import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { TeamPage } from "../TeamPage"
import * as authHook from "@/hooks/useAuth"
import * as teamApi from "@/features/team/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
}))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

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

  it("renders member table on success", async () => {
    vi.mocked(teamApi.fetchMembers).mockResolvedValue([
      {
        id: "u1",
        email: "alice@acme.test",
        first_name: "Alice",
        last_name: "Smith",
        full_name: "Alice Smith",
        role: "ADMIN",
      },
      {
        id: "u2",
        email: "bob@acme.test",
        first_name: "Bob",
        last_name: "Jones",
        full_name: "Bob Jones",
        role: "EMPLOYEE",
      },
    ])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })
    expect(screen.getByText("Bob Jones")).toBeInTheDocument()
    expect(screen.getByText("alice@acme.test")).toBeInTheDocument()
    expect(screen.getByText("bob@acme.test")).toBeInTheDocument()
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
