import { describe, it, expect } from "vitest"
import { render } from "@testing-library/react"

import { NexoraLogo } from "../NexoraLogo"

describe("NexoraLogo", () => {
  it("renders with default size class", () => {
    const { container } = render(<NexoraLogo />)
    const svg = container.querySelector("svg")
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveClass("size-9")
  })

  it("applies custom className", () => {
    const { container } = render(<NexoraLogo className="size-12 text-brand-600" />)
    const svg = container.querySelector("svg")
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveClass("size-12")
    expect(svg).toHaveClass("text-brand-600")
  })
})
