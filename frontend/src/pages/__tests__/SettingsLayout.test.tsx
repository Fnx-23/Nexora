import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it, vi } from "vitest"

import { SettingsLayout } from "../SettingsLayout"

vi.mock("@/pages/AccountPage", () => ({
  AccountPage: () => <div data-testid="account-page">Account Page Content</div>,
}))
vi.mock("@/pages/SecurityPage", () => ({
  SecurityPage: () => <div data-testid="security-page">Security Page Content</div>,
}))
vi.mock("@/pages/WorkspacePage", () => ({
  WorkspacePage: () => <div data-testid="workspace-page">Workspace Page Content</div>,
}))
vi.mock("@/pages/MembersPage", () => ({
  MembersPage: () => <div data-testid="members-page">Members Page Content</div>,
}))
vi.mock("@/pages/NotificationSettingsPage", () => ({
  NotificationSettingsPage: () => <div data-testid="notifications-page">Notifications Page Content</div>,
}))

function renderWithRouter(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/settings" element={<SettingsLayout />} />
        <Route path="/settings/:tab" element={<SettingsLayout />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("SettingsLayout", () => {
  it("renders all navigation tabs", () => {
    renderWithRouter("/settings")

    expect(screen.getByRole("link", { name: "Account" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Security" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Workspace" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Members" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Notifications" })).toBeInTheDocument()
  })

  it("defaults to account page when navigating to /settings", () => {
    renderWithRouter("/settings")

    expect(screen.getByTestId("account-page")).toBeInTheDocument()
    const accountTab = screen.getByRole("link", { name: "Account" })
    expect(accountTab.className).toContain("text-brand-600")
  })

  it("renders account page when navigating to /settings/account", () => {
    renderWithRouter("/settings/account")

    expect(screen.getByTestId("account-page")).toBeInTheDocument()
    const accountTab = screen.getByRole("link", { name: "Account" })
    expect(accountTab.className).toContain("text-brand-600")
  })

  it("renders security page when navigating to /settings/security", () => {
    renderWithRouter("/settings/security")

    expect(screen.getByTestId("security-page")).toBeInTheDocument()
    const securityTab = screen.getByRole("link", { name: "Security" })
    expect(securityTab.className).toContain("text-brand-600")
  })

  it("renders workspace page when navigating to /settings/workspace", () => {
    renderWithRouter("/settings/workspace")

    expect(screen.getByTestId("workspace-page")).toBeInTheDocument()
    const workspaceTab = screen.getByRole("link", { name: "Workspace" })
    expect(workspaceTab.className).toContain("text-brand-600")
  })

  it("renders members page when navigating to /settings/members", () => {
    renderWithRouter("/settings/members")

    expect(screen.getByTestId("members-page")).toBeInTheDocument()
    const membersTab = screen.getByRole("link", { name: "Members" })
    expect(membersTab.className).toContain("text-brand-600")
  })

  it("renders notifications page when navigating to /settings/notifications", () => {
    renderWithRouter("/settings/notifications")

    expect(screen.getByTestId("notifications-page")).toBeInTheDocument()
    const notificationsTab = screen.getByRole("link", { name: "Notifications" })
    expect(notificationsTab.className).toContain("text-brand-600")
  })

  it("redirects invalid tab to account page", () => {
    renderWithRouter("/settings/invalid-tab")

    expect(screen.getByTestId("account-page")).toBeInTheDocument()
  })

  it("switches content and active tab styling when clicking tabs without page reload", async () => {
    const user = userEvent.setup()
    renderWithRouter("/settings/account")

    expect(screen.getByTestId("account-page")).toBeInTheDocument()
    expect(screen.queryByTestId("security-page")).not.toBeInTheDocument()

    await user.click(screen.getByRole("link", { name: "Security" }))

    expect(screen.getByTestId("security-page")).toBeInTheDocument()
    expect(screen.queryByTestId("account-page")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Security" }).className).toContain("text-brand-600")

    await user.click(screen.getByRole("link", { name: "Workspace" }))

    expect(screen.getByTestId("workspace-page")).toBeInTheDocument()
    expect(screen.queryByTestId("security-page")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Workspace" }).className).toContain("text-brand-600")

    await user.click(screen.getByRole("link", { name: "Members" }))

    expect(screen.getByTestId("members-page")).toBeInTheDocument()
    expect(screen.queryByTestId("workspace-page")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Members" }).className).toContain("text-brand-600")

    await user.click(screen.getByRole("link", { name: "Notifications" }))

    expect(screen.getByTestId("notifications-page")).toBeInTheDocument()
    expect(screen.queryByTestId("members-page")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Notifications" }).className).toContain("text-brand-600")

    await user.click(screen.getByRole("link", { name: "Account" }))

    expect(screen.getByTestId("account-page")).toBeInTheDocument()
    expect(screen.queryByTestId("notifications-page")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Account" }).className).toContain("text-brand-600")
  })
})
