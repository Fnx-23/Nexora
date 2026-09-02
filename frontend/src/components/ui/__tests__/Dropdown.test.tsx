import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import { Dropdown, DropdownItem } from "../Dropdown"

function setup() {
  return render(
    <Dropdown
      trigger={({ triggerProps }) => (
        <button type="button" {...triggerProps}>
          Actions
        </button>
      )}
    >
      <DropdownItem>Edit</DropdownItem>
      <DropdownItem danger>Delete</DropdownItem>
    </Dropdown>,
  )
}

describe("Dropdown", () => {
  it("menu is hidden initially", () => {
    setup()
    expect(screen.queryByRole("menu")).not.toBeInTheDocument()
  })

  it("opens menu on trigger click and renders menuitems", async () => {
    const user = userEvent.setup()
    setup()
    await user.click(screen.getByRole("button", { name: "Actions" }))
    expect(screen.getByRole("menu")).toBeInTheDocument()
    expect(screen.getAllByRole("menuitem")).toHaveLength(2)
  })

  it("closes menu after clicking an item and triggers onClick", async () => {
    const user = userEvent.setup()
    const handleEdit = vi.fn()
    render(
      <Dropdown
        trigger={({ triggerProps }) => (
          <button type="button" {...triggerProps}>
            Actions
          </button>
        )}
      >
        <DropdownItem onClick={handleEdit}>Edit</DropdownItem>
      </Dropdown>,
    )
    await user.click(screen.getByRole("button", { name: "Actions" }))
    await user.click(screen.getByText("Edit"))
    expect(handleEdit).toHaveBeenCalledTimes(1)
    expect(screen.queryByRole("menu")).not.toBeInTheDocument()
  })

  it("trigger has aria-expanded toggled", async () => {
    const user = userEvent.setup()
    setup()
    const trigger = screen.getByRole("button", { name: "Actions" })
    expect(trigger).toHaveAttribute("aria-expanded", "false")
    await user.click(trigger)
    expect(trigger).toHaveAttribute("aria-expanded", "true")
  })

  it("trigger has aria-haspopup=menu", () => {
    setup()
    expect(screen.getByRole("button", { name: "Actions" })).toHaveAttribute("aria-haspopup", "menu")
  })

  it("opens on ArrowDown key", async () => {
    const user = userEvent.setup()
    setup()
    const trigger = screen.getByRole("button", { name: "Actions" })
    trigger.focus()
    await user.keyboard("{ArrowDown}")
    expect(screen.getByRole("menu")).toBeInTheDocument()
  })

  it("closes on Escape", async () => {
    const user = userEvent.setup()
    setup()
    await user.click(screen.getByRole("button", { name: "Actions" }))
    await user.keyboard("{Escape}")
    expect(screen.queryByRole("menu")).not.toBeInTheDocument()
  })

  it("closes on outside click", async () => {
    const user = userEvent.setup()
    render(
      <div>
        <p>Outside</p>
        <Dropdown
          trigger={({ triggerProps }) => (
            <button type="button" {...triggerProps}>
              Open
            </button>
          )}
        >
          <DropdownItem>Item</DropdownItem>
        </Dropdown>
      </div>,
    )
    await user.click(screen.getByRole("button", { name: "Open" }))
    expect(screen.getByRole("menu")).toBeInTheDocument()
    await user.click(screen.getByText("Outside"))
    expect(screen.queryByRole("menu")).not.toBeInTheDocument()
  })
})
