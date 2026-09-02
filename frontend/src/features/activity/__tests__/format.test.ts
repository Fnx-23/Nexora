import { describe, expect, it } from "vitest"

import { ACTION_OPTIONS, ENTITY_TYPE_OPTIONS } from "../format"

describe("format helpers", () => {
  it("exports action options", () => {
    expect(Array.isArray(ACTION_OPTIONS)).toBe(true)
    expect(ACTION_OPTIONS.length).toBeGreaterThan(0)
  })

  it("exports entity type options", () => {
    expect(ENTITY_TYPE_OPTIONS.length).toBeGreaterThan(0)
  })
})
