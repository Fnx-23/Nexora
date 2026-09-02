import { describe, it, expect, vi } from "vitest"
import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import { ConfirmDialog } from "../ConfirmDialog"

function getLatestDialog() {
  const dialogs = screen.getAllByRole("dialog")
  return dialogs[dialogs.length - 1]
}

describe("ConfirmDialog", () => {
  it("renders nothing when closed", () => {
    render(<ConfirmDialog open={false} onConfirm={() => {}} onCancel={() => {}} title="Hidden" />)
    expect(screen.queryAllByRole("dialog")).toHaveLength(0)
  })

  it("renders title, description and action buttons", () => {
    render(
      <ConfirmDialog
        open
        onConfirm={() => {}}
        onCancel={() => {}}
        title="Delete workspace?"
        description="This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
      />,
    )
    const dialog = getLatestDialog()
    expect(within(dialog).getByText("Delete workspace?")).toBeInTheDocument()
    expect(within(dialog).getByText("This action cannot be undone.")).toBeInTheDocument()
    expect(within(dialog).getByRole("button", { name: "Delete" })).toBeInTheDocument()
    expect(within(dialog).getByRole("button", { name: "Cancel" })).toBeInTheDocument()
  })

  it("calls onConfirm when the confirm button is clicked", async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    render(
      <ConfirmDialog
        open
        onConfirm={onConfirm}
        onCancel={() => {}}
        title="Confirm?"
        confirmLabel="Yes"
      />,
    )
    await user.click(screen.getByRole("button", { name: "Yes" }))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it("calls onCancel when the cancel button is clicked", async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()
    render(
      <ConfirmDialog
        open
        onConfirm={() => {}}
        onCancel={onCancel}
        title="Confirm?"
        cancelLabel="No"
      />,
    )
    await user.click(screen.getByRole("button", { name: "No" }))
    expect(onCancel).toHaveBeenCalledOnce()
  })
})