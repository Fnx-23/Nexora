import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { CommandPalette } from "../command/CommandPalette"
import * as authHook from "@/hooks/useAuth"
import * as searchApi from "@/features/search/api"
import type { SearchResponse } from "@/types/search"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/search/api", () => ({
  fetchSearchResults: vi.fn(),
}))

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

const MOCK_RESULTS: SearchResponse = {
  query: "cloud",
  projects: [
    {
      id: "p1",
      name: "Cloud Migration",
      status: "IN_PROGRESS",
      manager_name: "Sara Alami",
      link: "/projects/p1",
    },
  ],
  customers: [
    {
      id: "c1",
      name: "Atlas Logistics",
      company_name: "Atlas Logistics Ltd",
      link: "/customers",
    },
  ],
  tasks: [
    {
      id: "t1",
      title: "Cloud Migration",
      status: "TODO",
      project_name: "Cloud Migration",
      assignee_name: "Amina Tazi",
      link: "/tasks/t1",
    },
    {
      id: "t2",
      title: "Configure SSO",
      status: "TODO",
      project_name: "Cloud Migration",
      assignee_name: null,
      link: "/tasks/t2",
    },
  ],
  members: [
    {
      id: "m1",
      name: "Sara Alami",
      email: "sara@nexora.demo",
      role: "ADMIN",
      link: "/team",
    },
  ],
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

function LocationProbe() {
  const { pathname } = useLocation()
  return <span data-testid="location">{pathname}</span>
}

function renderPalette(open = true, onClose = vi.fn(), queryClient?: QueryClient) {
  const qc = queryClient ?? makeQueryClient()
  render(
    <MemoryRouter initialEntries={["/"]}>
      <QueryClientProvider client={qc}>
        <Routes>
          <Route
            path="*"
            element={
              <>
                <CommandPalette open={open} onClose={onClose} />
                <LocationProbe />
              </>
            }
          />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  )
  return { user: userEvent.setup(), onClose }
}

async function typeQuery(user: ReturnType<typeof userEvent.setup>, text: string) {
  await user.type(screen.getByRole("combobox"), text)
  await waitFor(() => {
    expect(screen.getAllByRole("option").length).toBeGreaterThan(0)
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(searchApi.fetchSearchResults).mockImplementation(async (query) => ({
    ...MOCK_RESULTS,
    query,
  }))
})

afterEach(() => {
  vi.clearAllMocks()
})

describe("CommandPalette", () => {
  describe("rendering", () => {
    it("renders nothing when closed", () => {
      renderPalette(false)
      expect(screen.queryByRole("combobox")).not.toBeInTheDocument()
    })

    it("shows grouped results with headers and metadata", async () => {
      const { user } = renderPalette()
      await typeQuery(user, "cloud")

      expect(screen.getByText("Projects", { selector: "p" })).toBeInTheDocument()
      expect(screen.getByText("Tasks", { selector: "p" })).toBeInTheDocument()
      expect(screen.getByText("Customers", { selector: "p" })).toBeInTheDocument()
      expect(screen.getByText("Members", { selector: "p" })).toBeInTheDocument()

      expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
      expect(screen.getByText("Configure SSO")).toBeInTheDocument()
      expect(screen.getByText("Atlas Logistics")).toBeInTheDocument()
      expect(screen.getAllByText("Sara Alami").length).toBeGreaterThan(0)

      expect(screen.getByText(/ADMIN · sara@nexora.demo/)).toBeInTheDocument()
      expect(screen.getByText(/Cloud Migration · Amina Tazi/)).toBeInTheDocument()
      expect(screen.getByText(/Atlas Logistics Ltd/)).toBeInTheDocument()
    })

    it("shows empty state when nothing matches", async () => {
      vi.mocked(searchApi.fetchSearchResults).mockResolvedValue({
        query: "zzz",
        projects: [],
        customers: [],
        tasks: [],
        members: [],
      })
      const { user } = renderPalette()
      await user.type(screen.getByRole("combobox"), "zzz")
      await waitFor(() => {
        expect(screen.getByText(/No results for/)).toBeInTheDocument()
      })
    })
  })

  describe("query behavior", () => {
    it("debounces and sends the final query once", async () => {
      const { user } = renderPalette()
      await user.type(screen.getByRole("combobox"), "cloud")
      await waitFor(() => {
        expect(searchApi.fetchSearchResults).toHaveBeenCalledTimes(1)
      })
      expect(searchApi.fetchSearchResults).toHaveBeenCalledWith("cloud")
    })

    it("does not search for queries shorter than two characters", async () => {
      const { user } = renderPalette()
      await user.type(screen.getByRole("combobox"), "a")
      expect(screen.getByText(/Type at least 2 characters/)).toBeInTheDocument()
      expect(searchApi.fetchSearchResults).not.toHaveBeenCalled()
    })

    it("passes special characters through unchanged", async () => {
      const { user } = renderPalette()
      vi.mocked(searchApi.fetchSearchResults).mockResolvedValue({
        query: "100%",
        projects: [{ id: "p2", name: "100% done board", status: "PLANNING", manager_name: null, link: "/projects/p2" }],
        customers: [],
        tasks: [],
        members: [],
      })
      await user.type(screen.getByRole("combobox"), "100%")
      await waitFor(() => {
        expect(searchApi.fetchSearchResults).toHaveBeenCalledWith("100%")
      })
      expect(screen.getByText("100% done board")).toBeInTheDocument()
    })
  })

  describe("keyboard navigation", () => {
    it("moves selection with ArrowDown and opens the item with Enter", async () => {
      const { user, onClose } = renderPalette()
      await typeQuery(user, "cloud")

      await user.keyboard("{ArrowDown}")
      expect(screen.getAllByRole("option")[1]).toHaveAttribute("aria-selected", "true")

      await user.keyboard("{Enter}")
      await waitFor(() => {
        expect(screen.getByTestId("location")).toHaveTextContent("/tasks/t1")
      })
      expect(onClose).toHaveBeenCalled()
    })

    it("opens the first result with Enter when nothing is selected", async () => {
      const { user, onClose } = renderPalette()
      await typeQuery(user, "cloud")

      await user.keyboard("{Enter}")
      await waitFor(() => {
        expect(screen.getByTestId("location")).toHaveTextContent("/projects/p1")
      })
      expect(onClose).toHaveBeenCalled()
    })

    it("wraps ArrowUp from the first to the last option", async () => {
      const { user } = renderPalette()
      await typeQuery(user, "cloud")

      await user.keyboard("{ArrowUp}")
      const options = screen.getAllByRole("option")
      expect(options[options.length - 1]).toHaveAttribute("aria-selected", "true")
    })

    it("wraps back to the first option after the last one", async () => {
      const { user } = renderPalette()
      await typeQuery(user, "cloud")

      const options = () => screen.getAllByRole("option")
      for (let i = 0; i < options().length; i++) {
        await user.keyboard("{ArrowDown}")
      }
      expect(options()[0]).toHaveAttribute("aria-selected", "true")
    })

    it("closes on Escape", async () => {
      const { user, onClose } = renderPalette()
      await user.type(screen.getByRole("combobox"), "cloud")
      await waitFor(() => {
        expect(screen.queryByText(/Type at least 2 characters/)).not.toBeInTheDocument()
      })
      await user.keyboard("{Escape}")
      expect(onClose).toHaveBeenCalled()
    })
  })

  describe("mouse interaction", () => {
    it("opens a result on click", async () => {
      const { user } = renderPalette()
      await typeQuery(user, "cloud")

      await user.click(screen.getByText("Configure SSO"))
      await waitFor(() => {
        expect(screen.getByTestId("location")).toHaveTextContent("/tasks/t2")
      })
    })
  })
})