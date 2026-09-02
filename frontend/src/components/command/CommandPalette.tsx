import { useEffect, useMemo, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"

import { SearchIcon } from "@/components/icons"
import { fetchSearchResults } from "@/features/search/api"
import { useAuth } from "@/hooks/useAuth"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"
import type { SearchResponse } from "@/types/search"

const MIN_QUERY_LENGTH = 2
const DEBOUNCE_MS = 150

export interface CommandPaletteProps {
  open: boolean
  onClose: () => void
}

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(timer)
  }, [value, delay])
  return debounced
}

type EntityKind = "project" | "task" | "customer" | "member"

interface ResultRow {
  key: string
  title: string
  subtitle: string | null
  link: string
  entity: EntityKind
}

interface ResultGroup {
  label: string
  rows: ResultRow[]
}

const GROUP_ORDER: { key: keyof SearchResponse; label: string; entity: EntityKind }[] = [
  { key: "projects", label: "Projects", entity: "project" },
  { key: "tasks", label: "Tasks", entity: "task" },
  { key: "customers", label: "Customers", entity: "customer" },
  { key: "members", label: "Members", entity: "member" },
]

function projectSubtitle(project: SearchResponse["projects"][number]): string | null {
  return project.manager_name ?? null
}

function taskSubtitle(task: SearchResponse["tasks"][number]): string | null {
  const parts = [task.project_name, task.assignee_name]
  const joined = parts.filter(Boolean).join(" · ")
  return joined || null
}

function customerSubtitle(customer: SearchResponse["customers"][number]): string | null {
  return customer.company_name || null
}

function memberSubtitle(member: SearchResponse["members"][number]): string | null {
  return `${member.role} · ${member.email}`
}

function buildGroups(data: SearchResponse | undefined): ResultGroup[] {
  if (!data) return []
  const groups: ResultGroup[] = []
  for (const def of GROUP_ORDER) {
    const rows: ResultRow[] = []
    for (const item of data[def.key]) {
      if (def.entity === "project") {
        const project = item as SearchResponse["projects"][number]
        rows.push({
          key: `project-${project.id}`,
          title: project.name,
          subtitle: projectSubtitle(project),
          link: project.link,
          entity: "project",
        })
      } else if (def.entity === "task") {
        const task = item as SearchResponse["tasks"][number]
        rows.push({
          key: `task-${task.id}`,
          title: task.title,
          subtitle: taskSubtitle(task),
          link: task.link,
          entity: "task",
        })
      } else if (def.entity === "customer") {
        const customer = item as SearchResponse["customers"][number]
        rows.push({
          key: `customer-${customer.id}`,
          title: customer.name,
          subtitle: customerSubtitle(customer),
          link: customer.link,
          entity: "customer",
        })
      } else {
        const member = item as SearchResponse["members"][number]
        rows.push({
          key: `member-${member.id}`,
          title: member.name,
          subtitle: memberSubtitle(member),
          link: member.link,
          entity: "member",
        })
      }
    }
    if (rows.length > 0) {
      groups.push({ label: def.label, rows })
    }
  }
  return groups
}

function entityGlyph(entity: EntityKind): string {
  switch (entity) {
    case "project":
      return "P"
    case "task":
      return "T"
    case "customer":
      return "C"
    case "member":
      return "M"
  }
}

function entityColor(entity: EntityKind): string {
  switch (entity) {
    case "project":
      return "bg-brand-50 text-brand-700"
    case "task":
      return "bg-emerald-50 text-emerald-700"
    case "customer":
      return "bg-sky-50 text-sky-700"
    case "member":
      return "bg-amber-50 text-amber-700"
  }
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const { activeCompany } = useAuth()
  const navigate = useNavigate()
  const companyId = activeCompany?.id ?? null
  const [query, setQuery] = useState("")
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const debouncedQuery = useDebouncedValue(query.trim(), DEBOUNCE_MS)
  const canSearch = debouncedQuery.length >= MIN_QUERY_LENGTH

  useEffect(() => {
    if (!open) {
      setQuery("")
      setActiveIndex(0)
    }
  }, [open])

  useEffect(() => {
    if (open) {
      inputRef.current?.focus()
    }
  }, [open])

  const searchQuery = useQuery({
    queryKey: queryKeys.search(companyId, debouncedQuery),
    queryFn: () => fetchSearchResults(debouncedQuery),
    enabled: open && companyId !== null && canSearch,
    placeholderData: (previous) => previous,
  })

  const groups = useMemo(() => buildGroups(searchQuery.data), [searchQuery.data])
  const rows = useMemo(() => groups.flatMap((group) => group.rows), [groups])

  useEffect(() => {
    setActiveIndex(0)
  }, [rows])

  useEffect(() => {
    const activeRow = rows[activeIndex]
    if (!activeRow) return
    const el = document.getElementById(`palette-item-${activeRow.key}`)
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ block: "nearest" })
    }
  }, [activeIndex, rows])

  useEffect(() => {
    if (!open) return

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault()
        onClose()
        return
      }
      if (rows.length === 0) return
      if (event.key === "ArrowDown") {
        event.preventDefault()
        setActiveIndex((index) => (index + 1) % rows.length)
      } else if (event.key === "ArrowUp") {
        event.preventDefault()
        setActiveIndex((index) => (index - 1 + rows.length) % rows.length)
      } else if (event.key === "Enter") {
        event.preventDefault()
        const row = rows[activeIndex]
        if (row) {
          navigate(row.link)
          onClose()
        }
      }
    }

    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [open, onClose, rows, activeIndex, navigate])

  if (!open) return null

  let globalIndex = 0
  const activeRow = rows[activeIndex]

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[12vh]">
      <div
        role="presentation"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
          <SearchIcon className="size-5 shrink-0 text-slate-400" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search projects, tasks, customers, members…"
            aria-label="Search"
            role="combobox"
            aria-expanded="true"
            aria-controls="command-palette-results"
            aria-activedescendant={
              activeRow ? `palette-item-${activeRow.key}` : undefined
            }
            className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
          />
          <kbd className="hidden rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 sm:block">
            ESC
          </kbd>
        </div>

        <div
          id="command-palette-results"
          role="listbox"
          aria-label="Search results"
          className="max-h-96 overflow-y-auto"
        >
          {!canSearch && (
            <div className="px-4 py-10 text-center text-sm text-slate-400">
              Type at least {MIN_QUERY_LENGTH} characters to search.
            </div>
          )}

          {canSearch && searchQuery.isPending && (
            <div className="px-4 py-10 text-center text-sm text-slate-500">Searching…</div>
          )}

          {canSearch && !searchQuery.isPending && searchQuery.isError && (
            <div className="px-4 py-10 text-center text-sm text-red-500">
              Something went wrong. Please try again.
            </div>
          )}

          {canSearch &&
            !searchQuery.isPending &&
            !searchQuery.isError &&
            rows.length === 0 && (
              <div className="px-4 py-10 text-center text-sm text-slate-400">
                No results for “{debouncedQuery}”.
              </div>
            )}

          {canSearch && rows.length > 0 && (
            <div>
              {groups.map((group) => (
                <div key={group.label}>
                  <p className="bg-slate-50 px-4 py-1.5 text-[11px] font-semibold tracking-wide text-slate-400 uppercase">
                    {group.label}
                  </p>
                  {group.rows.map((row) => {
                    const index = globalIndex++
                    const active = index === activeIndex
                    return (
                      <button
                        key={row.key}
                        id={`palette-item-${row.key}`}
                        type="button"
                        role="option"
                        aria-selected={active}
                        onMouseEnter={() => setActiveIndex(index)}
                        onClick={() => {
                          navigate(row.link)
                          onClose()
                        }}
                        className={cn(
                          "flex w-full items-center gap-3 border-b border-slate-50 px-4 py-2.5 text-left transition-colors",
                          active ? "bg-brand-50" : "hover:bg-slate-50",
                        )}
                      >
                        <span
                          className={cn(
                            "flex size-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold",
                            entityColor(row.entity),
                          )}
                        >
                          {entityGlyph(row.entity)}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span
                            className={cn(
                              "block truncate text-sm",
                              active ? "font-medium text-brand-900" : "text-slate-800",
                            )}
                          >
                            {row.title}
                          </span>
                          {row.subtitle && (
                            <span className="block truncate text-xs text-slate-400">
                              {row.subtitle}
                            </span>
                          )}
                        </span>
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 border-t border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] text-slate-400">
          <span>
            <kbd className="rounded border border-slate-200 bg-white px-1">↑</kbd>{" "}
            <kbd className="rounded border border-slate-200 bg-white px-1">↓</kbd> Navigate
          </span>
          <span>
            <kbd className="rounded border border-slate-200 bg-white px-1">↵</kbd> Open
          </span>
          <span className="ml-auto">
            <kbd className="rounded border border-slate-200 bg-white px-1">Esc</kbd> Close
          </span>
        </div>
      </div>
    </div>,
    document.body,
  )
}