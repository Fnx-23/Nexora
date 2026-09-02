import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi } from "vitest"

import { AccountPage } from "../AccountPage"
import type { SessionResponse } from "@/types/auth"
import * as authHook from "@/hooks/useAuth"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/services/api", () => ({
  api: {
    patch: vi.fn().mockResolvedValue({}),
  },
}))

const MOCK_USER: SessionResponse = {
  id: "u1",
  email: "test@example.com",
  first_name: "Jane",
  last_name: "Doe",
  avatar: null,
  full_name: "Jane Doe",
  memberships: [],
  active_company: null,
  is_email_verified: true,
  created_at: "2025-01-01T00:00:00Z",
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
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

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/settings/account"]}>
      <QueryClientProvider client={makeQueryClient()}>
        <AccountPage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe("AccountPage", () => {
  it("displays the user's name and email", () => {
    mockAuth()
    renderPage()
    expect(screen.getByText("Jane")).toBeInTheDocument()
    expect(screen.getByText("Doe")).toBeInTheDocument()
    expect(screen.getByText("test@example.com")).toBeInTheDocument()
  })

  it("shows email verified status", () => {
    mockAuth()
    renderPage()
    expect(screen.getByText("Verified")).toBeInTheDocument()
  })

  it("renders edit name inputs", () => {
    mockAuth()
    renderPage()
    expect(screen.getByLabelText("First name")).toBeInTheDocument()
    expect(screen.getByLabelText("Last name")).toBeInTheDocument()
  })

  it("shows a save button", () => {
    mockAuth()
    renderPage()
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument()
  })
})