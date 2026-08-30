import { describe, expect, it } from "vitest"

import type { Activity, ActivityAction } from "@/types/activity"
import {
  ACTION_OPTIONS,
  activityDetail,
  activitySubject,
  entityMeta,
  formatTimestamp,
  timeAgo,
} from "@/features/activity/format"

function mk(
  action: ActivityAction,
  metadata: Record<string, unknown>,
  overrides: Partial<Activity> = {},
): Activity {
  return {
    id: "a1",
    action,
    action_display: "Some action",
    entity_type: "customer",
    entity_id: "e1",
    actor: "u1",
    actor_name: "Admin Test",
    metadata,
    timestamp: "2025-08-20T14:00:00Z",
    ...overrides,
  }
}

describe("timeAgo", () => {
  it("labels very recent events as 'Just now'", () => {
    expect(timeAgo(new Date().toISOString())).toBe("Just now")
  })

  it("labels minutes, hours and days", () => {
    const now = Date.now()
    expect(timeAgo(new Date(now - 5 * 60_000).toISOString())).toBe("5m ago")
    expect(timeAgo(new Date(now - 3 * 3_600_000).toISOString())).toBe("3h ago")
    expect(timeAgo(new Date(now - 2 * 86_400_000).toISOString())).toBe("2d ago")
  })

  it("returns an empty string for an invalid date", () => {
    expect(timeAgo("not-a-date")).toBe("")
  })
})

describe("formatTimestamp", () => {
  it("produces an absolute, human timestamp", () => {
    const out = formatTimestamp("2025-08-20T14:00:00Z")
    expect(out).toContain("2025")
    expect(out).toMatch(/Aug/)
  })

  it("returns an empty string for an invalid date", () => {
    expect(formatTimestamp("nope")).toBe("")
  })
})

describe("entityMeta", () => {
  it("maps known entity types", () => {
    expect(entityMeta("customer").label).toBe("Customer")
    expect(entityMeta("project").initial).toBe("P")
    expect(entityMeta("membership").label).toBe("Team")
  })

  it("falls back safely for unknown types", () => {
    expect(entityMeta("something-else").label).toBe("Activity")
  })
})

describe("activitySubject", () => {
  it("prefers metadata.name", () => {
    expect(activitySubject(mk("customer.created", { name: "Acme Corp" }))).toBe("Acme Corp")
  })

  it("falls back to metadata.title", () => {
    expect(activitySubject(mk("task.created", { title: "Ship it" }))).toBe("Ship it")
  })

  it("falls back to the action label when neither is present", () => {
    const a = mk("team.role_changed", { old_role: "EMPLOYEE" }, { action_display: "Team role changed" })
    expect(activitySubject(a)).toBe("Team role changed")
  })
})

describe("activityDetail", () => {
  it("renders a status transition for status changes", () => {
    const a = mk("project.status_changed", { old_status: "PLANNING", new_status: "IN_PROGRESS" })
    expect(activityDetail(a)).toBe("Planning → In progress")
  })

  it("renders a role transition for role changes", () => {
    const a = mk("team.role_changed", { old_role: "EMPLOYEE", new_role: "MANAGER" })
    expect(activityDetail(a)).toBe("Employee → Manager")
  })

  it("lists humanized changed fields for updates", () => {
    const a = mk("customer.updated", { changed_fields: ["name", "email"] })
    expect(activityDetail(a)).toBe("Changed name, email")
    const b = mk("project.updated", { changed_fields: ["manager_id"] })
    expect(activityDetail(b)).toBe("Changed manager")
  })

  it("distinguishes assigned / reassigned / unassigned", () => {
    expect(activityDetail(mk("task.assigned", { new_assignee_id: "u2" }))).toBe("Assigned")
    expect(
      activityDetail(mk("task.assigned", { old_assignee_id: "u1", new_assignee_id: "u2" })),
    ).toBe("Reassigned")
    expect(activityDetail(mk("task.assigned", { old_assignee_id: "u1" }))).toBe("Unassigned")
  })

  it("returns null when there is nothing extra to say", () => {
    expect(activityDetail(mk("customer.created", { name: "Acme" }))).toBeNull()
    // Robust to missing metadata shapes.
    expect(activityDetail(mk("customer.updated", {}))).toBeNull()
    expect(activityDetail(mk("project.status_changed", {}))).toBeNull()
  })
})

describe("ACTION_OPTIONS", () => {
  it("offers an 'all' option plus every one of the ten audited actions", () => {
    // 10 audited events + the leading "All activity" entry.
    expect(ACTION_OPTIONS).toHaveLength(11)
    expect(ACTION_OPTIONS[0].value).toBe("")
    const values = ACTION_OPTIONS.slice(1).map((o) => o.value)
    expect(values).toEqual([
      "customer.created",
      "customer.updated",
      "customer.archived",
      "project.created",
      "project.updated",
      "project.status_changed",
      "task.created",
      "task.assigned",
      "task.status_changed",
      "team.role_changed",
    ])
  })
})
