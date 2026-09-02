import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { InvitePage } from "../InvitePage"
import * as authHook from "@/hooks/useAuth"
import * as teamApi from "@/features/team/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  validateInvitation: vi.fn(),
  acceptInvitation: vi.fn(),
  registerAndAcceptInvitation: vi.fn(),
}))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

function renderInvite(token: string) {
  return render(
    <MemoryRouter initialEntries={[`/invite/${token}`]}>
      <QueryClientProvider client={queryClient}>
        <Routes>
          <Route path="/invite/:token" element={<InvitePage />} />
        </Routes>
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
      email: "carol@acme.test",
      first_name: "Carol",
      last_name: "Test",
      avatar: null,
      full_name: "Carol Test",
    },
    activeCompany: { id: "c1", name: "Acme", slug: "acme" },
    role: "EMPLOYEE",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn().mockResolvedValue(undefined),
  })
})

describe("InvitePage", () => {
  it("shows invalid state for a bad token", async () => {
    vi.mocked(teamApi.validateInvitation).mockRejectedValue(new Error("invalid"))
    renderInvite("badtoken")
    await waitFor(() => {
      expect(screen.getByText(/no longer valid/i)).toBeInTheDocument()
    })
  })

  it("offers acceptance to an existing logged-in user with matching email", async () => {
    vi.mocked(teamApi.validateInvitation).mockResolvedValue({
      email: "carol@acme.test",
      company_name: "Acme",
      role: "MANAGER",
      user_exists: true,
    })
    renderInvite("goodtoken")
    await waitFor(() => {
      expect(screen.getByText(/You're invited to/)).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: "Accept invitation" })).toBeInTheDocument()
  })

  it("shows a registration form for a brand-new invitee", async () => {
    vi.mocked(teamApi.validateInvitation).mockResolvedValue({
      email: "new@acme.test",
      company_name: "Acme",
      role: "EMPLOYEE",
      user_exists: false,
    })
    renderInvite("goodtoken")
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /create account & accept/i }),
      ).toBeInTheDocument()
    })
    expect(screen.getByLabelText(/First name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Last name/i)).toBeInTheDocument()
  })
})
