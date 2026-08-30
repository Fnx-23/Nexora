import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import { Modal } from "../Modal"

beforeEach(() => {
  document.body.style.overflow = ""
})
afterEach(() => {
  document.body.style.overflow = ""
})

function getLatestDialog() {
  const dialogs = screen.getAllByRole("dialog")
  return dialogs[dialogs.length - 1]
}

describe("Modal", () => {
  it("renders title and children when open", () => {
    render(
      <Modal open onClose={() => {}} title="Test dialog">
        <p>Body content</p>
      </Modal>,
    )
    const dialog = getLatestDialog()
    expect(dialog).toBeInTheDocument()
    expect(within(dialog).getByText("Test dialog")).toBeInTheDocument()
    expect(within(dialog).getByText("Body content")).toBeInTheDocument()
  })

  it("renders nothing when closed", () => {
    render(
      <Modal open={false} onClose={() => {}} title="Hidden">
        <p>Body</p>
      </Modal>,
    )
    const dialogs = screen.queryAllByRole("dialog")
    const hasHidden = dialogs.some((d) => within(d).queryByText("Hidden"))
    expect(hasHidden).toBe(false)
  })

  it("calls onClose on Escape", async () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Esc test">
        <span />
      </Modal>,
    )
    await userEvent.keyboard("{Escape}")
    expect(onClose).toHaveBeenCalledOnce()
  })

  it("calls onClose on backdrop click", async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Backdrop click">
        <span />
      </Modal>,
    )
    const dialog = getLatestDialog()
    const backdrop = (dialog.parentElement as HTMLElement).querySelector("[role='presentation']") as HTMLElement
    await user.click(backdrop)
    expect(onClose).toHaveBeenCalledOnce()
  })

  it("locks body scroll while open", () => {
    render(
      <Modal open onClose={() => void 0} title="Scroll lock">
        <span />
      </Modal>,
    )
    expect(document.body.style.overflow).toBe("hidden")
  })

  it("restores body scroll on unmount", () => {
    const { unmount } = render(
      <Modal open onClose={() => void 0} title="Scroll restore">
        <span />
      </Modal>,
    )
    unmount()
    expect(document.body.style.overflow).toBe("")
  })

  it("has accessible dialog role with aria-labelledby when titled", () => {
    render(
      <Modal open onClose={() => void 0} title="Labeled dialog">
        <span />
      </Modal>,
    )
    const dialog = getLatestDialog()
    expect(dialog).toHaveAttribute("aria-modal", "true")
    expect(dialog).toHaveAttribute("aria-labelledby")
  })

  it("uses aria-label fallback when no title provided", () => {
    render(
      <Modal open onClose={() => void 0}>
        <span />
      </Modal>,
    )
    const dialogs = screen.getAllByRole("dialog")
    const noLabel = dialogs.find((d) => d.getAttribute("aria-label") === "Dialog")
    expect(noLabel).toBeDefined()
  })

  it("renders footer when provided", () => {
    render(
      <Modal open onClose={() => void 0} title="F" footer={<button type="button">OK</button>}>
        <span />
      </Modal>,
    )
    const dialog = getLatestDialog()
    expect(within(dialog).getByRole("button", { name: "OK" })).toBeInTheDocument()
  })

  it("close button is accessible", () => {
    render(
      <Modal open onClose={() => void 0} title="Close test">
        <span />
      </Modal>,
    )
    const dialog = getLatestDialog()
    expect(within(dialog).getByRole("button", { name: "Close dialog" })).toBeInTheDocument()
  })
})
