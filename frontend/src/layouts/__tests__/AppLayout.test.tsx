import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { AppLayout } from "../AppLayout"
import * as authHook from "@/hooks/useAuth"
import * as searchApi from "@/features/search/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/search/api", () => ({
  fetchSearchResults: vi.fn(),
}))

vi.mock("@/components/layout/Navbar", () => ({
  Navbar: (props: { onOpenSearch: () => void }) => (
    <button type="button" onClick={props.onOpenSearch}>
      nav-search
    </button>
  ),
}))

vi.mock("@/components/layout/Sidebar", () => ({
  Sidebar: () => <aside>sidebar</aside>,
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
    activeCompany: { id: "c1", name: "TestCo", slug: "testco" },
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function renderAppLayout() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <AppLayout />
      </QueryClientProvider>
    </MemoryRouter>,
  )
  return userEvent.setup()
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(searchApi.fetchSearchResults).mockResolvedValue({
    query: "cloud",
    projects: [],
    customers: [],
    tasks: [],
    members: [],
  })
})

describe("AppLayout global search shortcut", () => {
  it("opens the command palette with Ctrl+K", async () => {
    const user = renderAppLayout()
    await user.keyboard("{Control>}k{/Control}")
    expect(screen.getByRole("combobox")).toBeInTheDocument()
  })

  it("opens the command palette with Cmd+K", async () => {
    const user = renderAppLayout()
    await user.keyboard("{Meta>}k{/Meta}")
    expect(screen.getByRole("combobox")).toBeInTheDocument()
  })

  it("toggles the palette closed with a second Ctrl+K", async () => {
    const user = renderAppLayout()
    await user.keyboard("{Control>}k{/Control}")
    expect(screen.getByRole("combobox")).toBeInTheDocument()
    await user.keyboard("{Control>}k{/Control}")
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument()
  })

  it("closes the palette with Escape", async () => {
    const user = renderAppLayout()
    await user.keyboard("{Control>}k{/Control}")
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument()
    })
    await user.keyboard("{Escape}")
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument()
  })

  it("opens the palette from the topbar search trigger", async () => {
    const user = renderAppLayout()
    await user.click(screen.getByRole("button", { name: "nav-search" }))
    expect(screen.getByRole("combobox")).toBeInTheDocument()
  })
})