import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import { ProtectedRoute } from "../ProtectedRoute"
import * as authHook from "@/hooks/useAuth"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

function renderWithRouter(initialEntry = "/app") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/app" element={<span>Dashboard</span>} />
        </Route>
        <Route path="/login" element={<span>Login page</span>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ProtectedRoute", () => {
  it("shows loading state while checking session", () => {
    vi.mocked(authHook.useAuth).mockReturnValue({
      status: "loading",
      user: null,
      activeCompany: null,
      role: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshSession: vi.fn(),
    })
    renderWithRouter()
    expect(screen.getByText("Preparing your workspace…")).toBeInTheDocument()
  })

  it("redirects to /login when unauthenticated", () => {
    vi.mocked(authHook.useAuth).mockReturnValue({
      status: "unauthenticated",
      user: null,
      activeCompany: null,
      role: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshSession: vi.fn(),
    })
    renderWithRouter()
    expect(screen.getByText("Login page")).toBeInTheDocument()
  })

  it("renders child routes when authenticated", () => {
    vi.mocked(authHook.useAuth).mockReturnValue({
      status: "authenticated",
      user: {
        id: "1",
        email: "test@test.com",
        first_name: "T",
        last_name: "E",
        avatar: null,
        full_name: "T E",
      },
      activeCompany: { id: "c1", name: "Acme", slug: "acme" },
      role: "ADMIN",
      login: vi.fn(),
      logout: vi.fn(),
      refreshSession: vi.fn(),
    })
    renderWithRouter()
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
  })
})
