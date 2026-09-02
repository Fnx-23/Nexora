import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { MembersPage } from "../MembersPage"
import type { Member } from "@/types/team"
import * as authHook from "@/hooks/useAuth"
import * as teamApi from "@/features/team/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
}))

const MOCK_MEMBERS: Member[] = [
  {
    id: "u1",
    email: "a@acme.test",
    first_name: "Ada",
    last_name: "Admin",
    full_name: "Ada Admin",
    role: "ADMIN",
    membership_id: "m1",
    membership_active: true,
    joined_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "u2",
    email: "m@acme.test",
    first_name: "Mary",
    last_name: "Manager",
    full_name: "Mary Manager",
    role: "MANAGER",
    membership_id: "m2",
    membership_active: true,
    joined_at: "2026-01-02T00:00:00Z",
  },
  {
    id: "u3",
    email: "e@acme.test",
    first_name: "Eve",
    last_name: "Employee",
    full_name: "Eve Employee",
    role: "EMPLOYEE",
    membership_id: "m3",
    membership_active: true,
    joined_at: "2026-01-03T00:00:00Z",
  },
]

function mockAuth() {
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user: {
      id: "u1",
      email: "a@acme.test",
      first_name: "Ada",
      last_name: "Admin",
      avatar: null,
      full_name: "Ada Admin",
    },
    activeCompany: { id: "c1", name: "Acme Inc", slug: "acme" },
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
    <MemoryRouter initialEntries={["/settings/members"]}>
      <QueryClientProvider client={makeQueryClient()}>
        <Routes>
          <Route path="/settings/members" element={<MembersPage />} />
          <Route path="/team" element={<h1>Team page</h1>} />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(teamApi.fetchMembers).mockResolvedValue(MOCK_MEMBERS)
})

describe("MembersPage", () => {
  it("shows member count summaries", async () => {
    renderPage()
    await screen.findByText("3")
    expect(screen.getByText("Total members")).toBeInTheDocument()
    expect(screen.getByText("Admins")).toBeInTheDocument()
    expect(screen.getByText("Managers")).toBeInTheDocument()
    expect(screen.getByText("Employees")).toBeInTheDocument()
  })

  it("renders role badges for each populated role", async () => {
    vi.mocked(teamApi.fetchMembers).mockResolvedValue([
      MOCK_MEMBERS[0],
      MOCK_MEMBERS[1],
      MOCK_MEMBERS[2],
    ])
    renderPage()
    await screen.findByText("3")
    expect(screen.getAllByText(/ADMIN/)).not.toHaveLength(0)
    expect(screen.getAllByText(/MANAGER/)).not.toHaveLength(0)
    expect(screen.getAllByText(/EMPLOYEE/)).not.toHaveLength(0)
  })

  it("navigates to the Team page via the CTA", async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText("3")

    await user.click(screen.getByRole("button", { name: /go to team management/i }))
    await waitFor(() => {
      expect(screen.getByText("Team page")).toBeInTheDocument()
    })
  })
})