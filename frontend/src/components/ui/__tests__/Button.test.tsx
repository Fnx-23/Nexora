import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import { Button } from "../Button"

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Submit</Button>)
    expect(screen.getByRole("button")).toHaveTextContent("Submit")
  })

  it("calls onClick when clicked", async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click</Button>)
    await user.click(screen.getByRole("button"))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it("is disabled while loading", async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(
      <Button isLoading onClick={onClick}>
        Save
      </Button>,
    )
    const btn = screen.getByRole("button")
    expect(btn).toBeDisabled()
    await user.click(btn)
    expect(onClick).not.toHaveBeenCalled()
  })

  it("is disabled when disabled prop is set", async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(
      <Button disabled onClick={onClick}>
        No-op
      </Button>,
    )
    await user.click(screen.getByRole("button"))
    expect(onClick).not.toHaveBeenCalled()
  })
})
