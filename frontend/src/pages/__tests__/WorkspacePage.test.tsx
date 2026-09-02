import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { WorkspacePage } from "../WorkspacePage"
import * as authHook from "@/hooks/useAuth"
import * as companyApi from "@/features/company/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/company/api", () => ({
  fetchWorkspace: vi.fn(),
  updateWorkspace: vi.fn(),
}))

const MOCK_WORKSPACE: companyApi.Workspace = {
  id: "c1",
  name: "Acme Inc",
  slug: "acme",
  description: "Building things.",
  is_active: true,
  timezone: "UTC",
  locale: "en",
  logo: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
}

function mockAuth(role: "ADMIN" | "MANAGER" | "EMPLOYEE" = "ADMIN") {
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user: {
      id: "u1",
      email: "admin@acme.test",
      first_name: "Admin",
      last_name: "Test",
      avatar: null,
      full_name: "Admin Test",
    },
    activeCompany: { id: "c1", name: "Acme Inc", slug: "acme" },
    role,
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn().mockResolvedValue(undefined),
  })
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage(role: "ADMIN" | "MANAGER" | "EMPLOYEE" = "ADMIN") {
  mockAuth(role)
  return render(
    <MemoryRouter initialEntries={["/settings/workspace"]}>
      <a href="/settings/account">Settings</a>
      <QueryClientProvider client={makeQueryClient()}>
        <WorkspacePage />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(companyApi.fetchWorkspace).mockResolvedValue(MOCK_WORKSPACE)
})

describe("WorkspacePage", () => {
  it("shows workspace name for admins", async () => {
    renderPage()
    expect(await screen.findByLabelText("Workspace name")).toHaveValue("Acme Inc")
  })

  it("shows read-only workspace details to non-admins", async () => {
    renderPage("MANAGER")
    await screen.findByText("Acme Inc")
    expect(screen.queryByLabelText("Workspace name")).not.toBeInTheDocument()
    expect(screen.getByText(/only be edited by an administrator/i)).toBeInTheDocument()
    expect(screen.queryByLabelText("Timezone")).not.toBeInTheDocument()
  })

  it("enables the save button only when form is dirty", async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByLabelText("Workspace name")

    const saveButton = screen.getByRole("button", { name: /save changes/i })
    expect(saveButton).toBeDisabled()

    await user.clear(screen.getByLabelText("Workspace name"))
    await user.type(screen.getByLabelText("Workspace name"), "Acme Corp")
    expect(saveButton).toBeEnabled()
  })

  it("persists updated workspace settings", async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByLabelText("Workspace name")

    await user.clear(screen.getByLabelText("Workspace name"))
    await user.type(screen.getByLabelText("Workspace name"), "Acme Corp")
    await user.selectOptions(screen.getByLabelText("Timezone"), "Europe/Paris")
    await user.selectOptions(screen.getByLabelText("Language"), "fr")
    await user.click(screen.getByRole("button", { name: /save changes/i }))

    await waitFor(() => {
      expect(companyApi.updateWorkspace).toHaveBeenCalledWith({
        name: "Acme Corp",
        description: "Building things.",
        timezone: "Europe/Paris",
        locale: "fr",
        logo: undefined,
      })
    })
    expect(await screen.findByText(/Workspace updated successfully/)).toBeInTheDocument()
  })

  it("shows an error when saving fails", async () => {
    const user = userEvent.setup()
    vi.mocked(companyApi.updateWorkspace).mockRejectedValue(new Error("nope"))
    renderPage()
    await screen.findByLabelText("Workspace name")

    await user.clear(screen.getByLabelText("Workspace name"))
    await user.type(screen.getByLabelText("Workspace name"), "Acme Corp")
    await user.click(screen.getByRole("button", { name: /save changes/i }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/Failed to save workspace settings/)
  })

  it("renders an upload control for the logo for admins", async () => {
    renderPage()
    expect(await screen.findByRole("button", { name: /upload logo/i })).toBeInTheDocument()
  })

  it("asks for confirmation before leaving with unsaved changes", async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByLabelText("Workspace name")

    await user.clear(screen.getByLabelText("Workspace name"))
    await user.type(screen.getByLabelText("Workspace name"), "Acme Corp")

    await user.click(screen.getByRole("link", { name: "Settings" }))
    const dialog = await screen.findByRole("dialog")
    expect(dialog).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /stay/i }))
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
  })
})