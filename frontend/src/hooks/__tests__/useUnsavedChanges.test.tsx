import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes, Link } from "react-router-dom"

import { useUnsavedChanges } from "../useUnsavedChanges"

vi.mock("@/components/ui/ConfirmDialog", () => {
  return {
    ConfirmDialog: ({
      open,
      onConfirm,
      onCancel,
      title,
    }: {
      open: boolean
      onConfirm: () => void
      onCancel: () => void
      title: string
    }) =>
      open ? (
        <div role="dialog">
          <h2>{title}</h2>
          <button onClick={onConfirm}>Leave</button>
          <button onClick={onCancel}>Stay</button>
        </div>
      ) : null,
  }
})

function Harness({ dirty }: { dirty: boolean }) {
  const { showConfirm, handleConfirm, handleCancel } = useUnsavedChanges(dirty)
  return (
    <div>
      <h1>Current</h1>
      <Link to="/other">Go other</Link>
      <Link to="/current">Stay here</Link>
      <a href="https://example.com">External</a>
      {showConfirm && (
        <div role="dialog">
          <h2>Confirm navigation</h2>
          <button onClick={handleConfirm}>Leave</button>
          <button onClick={handleCancel}>Stay</button>
        </div>
      )}
    </div>
  )
}

function renderHarness(dirty: boolean) {
  return render(
    <MemoryRouter initialEntries={["/current"]}>
      <Routes>
        <Route path="/current" element={<Harness dirty={dirty} />} />
        <Route path="/other" element={<h1>Other</h1>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("useUnsavedChanges", () => {
  let beforeUnloadSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    beforeUnloadSpy = vi.spyOn(window, "addEventListener")
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("registers a beforeunload listener when dirty", () => {
    renderHarness(true)
    expect(beforeUnloadSpy).toHaveBeenCalledWith("beforeunload", expect.any(Function))
  })

  it("does not register beforeunload when clean", () => {
    renderHarness(false)
    const calls = beforeUnloadSpy.mock.calls.filter(
      ([type]: [string, ...unknown[]]) => type === "beforeunload",
    )
    expect(calls).toHaveLength(0)
  })

  it("blocks same-app navigation when dirty and confirms on Leave", async () => {
    const user = userEvent.setup()
    renderHarness(true)

    await user.click(screen.getByText("Go other"))
    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getByText("Current")).toBeInTheDocument()

    await user.click(screen.getByText("Leave"))
    expect(screen.getByText("Other")).toBeInTheDocument()
  })

  it("keeps the user on the page when they choose Stay", async () => {
    const user = userEvent.setup()
    renderHarness(true)

    await user.click(screen.getByText("Go other"))
    await user.click(screen.getByText("Stay"))

    expect(screen.queryByText("Other")).not.toBeInTheDocument()
    expect(screen.getByText("Current")).toBeInTheDocument()
  })

  it("does not block navigation to the same path", async () => {
    const user = userEvent.setup()
    renderHarness(true)

    await user.click(screen.getByText("Stay here"))
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    expect(screen.getByText("Current")).toBeInTheDocument()
  })

  it("does not intercept external links", () => {
    renderHarness(true)

    const extLink = screen.getByText("External")
    const click = new MouseEvent("click", { bubbles: true, cancelable: true })
    const notPrevented = extLink.dispatchEvent(click)
    click.preventDefault()

    expect(notPrevented).toBe(true)
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    expect(screen.getByText("Current")).toBeInTheDocument()
  })

  it("does not block navigation when clean", async () => {
    const user = userEvent.setup()
    renderHarness(false)

    await user.click(screen.getByText("Go other"))
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    expect(screen.getByText("Other")).toBeInTheDocument()
  })
})