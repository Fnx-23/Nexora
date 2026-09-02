import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { Navbar } from "../layout/Navbar"
import * as authHook from "@/hooks/useAuth"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

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
    activeCompany: null,
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function renderNavbar(onOpenSearch = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <Navbar onOpenSidebar={vi.fn()} onOpenSearch={onOpenSearch} />
      </QueryClientProvider>
    </MemoryRouter>,
  )
  return { user: userEvent.setup(), onOpenSearch }
}

describe("Navbar", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuth()
  })

  it("renders the search pill with keyboard hint", () => {
    renderNavbar()
    expect(screen.getByRole("button", { name: /^Search$/ })).toBeInTheDocument()
    expect(screen.getByText("⌘K")).toBeInTheDocument()
  })

  it("opens search when the pill is clicked", async () => {
    const { user, onOpenSearch } = renderNavbar()
    await user.click(screen.getByRole("button", { name: /^Search$/ }))
    expect(onOpenSearch).toHaveBeenCalledTimes(1)
  })

  it("renders an icon-only search trigger for mobile", async () => {
    const { user, onOpenSearch } = renderNavbar()
    await user.click(screen.getByRole("button", { name: "Open search" }))
    expect(onOpenSearch).toHaveBeenCalledTimes(1)
  })
})