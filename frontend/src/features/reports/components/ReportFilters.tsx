import { useCallback } from "react"

import { Button } from "@/components/ui/Button"
import { DownloadIcon, PrinterIcon } from "@/components/icons"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import type { ReportFilterParams, ReportType } from "@/types/report"

interface OptionItem {
  id: string
  name: string
}

interface ReportFiltersProps {
  filters: ReportFilterParams
  activeTab: ReportType
  onFilterChange: (updates: Partial<ReportFilterParams>) => void
  onReset: () => void
  onExportCsv: () => void
  isExporting?: boolean
  projects?: OptionItem[]
  members?: OptionItem[]
  customers?: OptionItem[]
}

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0]
}

export function ReportFilters({
  filters,
  activeTab,
  onFilterChange,
  onReset,
  onExportCsv,
  isExporting = false,
  projects = [],
  members = [],
  customers = [],
}: ReportFiltersProps) {
  const hasActiveFilters = Boolean(
    filters.date_from ||
      filters.date_to ||
      filters.project ||
      filters.user ||
      filters.customer ||
      filters.status,
  )

  const applyPreset = useCallback(
    (preset: "all" | "30days" | "thisMonth" | "thisQuarter" | "thisYear") => {
      const now = new Date()
      if (preset === "all") {
        onFilterChange({ date_from: "", date_to: "" })
        return
      }

      if (preset === "30days") {
        const past = new Date()
        past.setDate(past.getDate() - 29)
        onFilterChange({ date_from: formatDate(past), date_to: formatDate(now) })
        return
      }

      if (preset === "thisMonth") {
        const start = new Date(now.getFullYear(), now.getMonth(), 1)
        onFilterChange({ date_from: formatDate(start), date_to: formatDate(now) })
        return
      }

      if (preset === "thisQuarter") {
        const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3
        const start = new Date(now.getFullYear(), quarterStartMonth, 1)
        onFilterChange({ date_from: formatDate(start), date_to: formatDate(now) })
        return
      }

      if (preset === "thisYear") {
        const start = new Date(now.getFullYear(), 0, 1)
        onFilterChange({ date_from: formatDate(start), date_to: formatDate(now) })
        return
      }
    },
    [onFilterChange],
  )

  const handlePrint = useCallback(() => {
    window.print()
  }, [])

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-xs print:hidden">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Range:
          </span>
          <button
            type="button"
            onClick={() => applyPreset("all")}
            className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 active:bg-slate-100"
          >
            All time
          </button>
          <button
            type="button"
            onClick={() => applyPreset("30days")}
            className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 active:bg-slate-100"
          >
            Last 30 days
          </button>
          <button
            type="button"
            onClick={() => applyPreset("thisMonth")}
            className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 active:bg-slate-100"
          >
            This month
          </button>
          <button
            type="button"
            onClick={() => applyPreset("thisQuarter")}
            className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 active:bg-slate-100"
          >
            This quarter
          </button>
          <button
            type="button"
            onClick={() => applyPreset("thisYear")}
            className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 active:bg-slate-100"
          >
            This year
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onExportCsv}
            disabled={isExporting}
            className="flex items-center gap-1.5"
          >
            <DownloadIcon className="size-4" />
            {isExporting ? "Exporting..." : "Export CSV"}
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handlePrint}
            className="flex items-center gap-1.5"
            title="Print or Save PDF"
          >
            <PrinterIcon className="size-4" />
            Print / PDF
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <div>
          <label htmlFor="report-filter-date-from" className="mb-1 block text-xs font-medium text-slate-600">
            From
          </label>
          <Input
            id="report-filter-date-from"
            aria-label="From date"
            type="date"
            value={filters.date_from || ""}
            onChange={(e) => onFilterChange({ date_from: e.target.value })}
            className="w-full text-xs"
          />
        </div>

        <div>
          <label htmlFor="report-filter-date-to" className="mb-1 block text-xs font-medium text-slate-600">
            To
          </label>
          <Input
            id="report-filter-date-to"
            aria-label="To date"
            type="date"
            value={filters.date_to || ""}
            onChange={(e) => onFilterChange({ date_to: e.target.value })}
            className="w-full text-xs"
          />
        </div>

        <div>
          <label htmlFor="report-filter-project" className="mb-1 block text-xs font-medium text-slate-600">
            Project
          </label>
          <Select
            id="report-filter-project"
            aria-label="Filter by project"
            value={filters.project || ""}
            onChange={(e) => onFilterChange({ project: e.target.value })}
            className="w-full text-xs"
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="report-filter-member" className="mb-1 block text-xs font-medium text-slate-600">
            Team Member
          </label>
          <Select
            id="report-filter-member"
            aria-label="Filter by team member"
            value={filters.user || ""}
            onChange={(e) => onFilterChange({ user: e.target.value })}
            className="w-full text-xs"
          >
            <option value="">All members</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="report-filter-customer" className="mb-1 block text-xs font-medium text-slate-600">
            Customer
          </label>
          <Select
            id="report-filter-customer"
            aria-label="Filter by customer"
            value={filters.customer || ""}
            onChange={(e) => onFilterChange({ customer: e.target.value })}
            className="w-full text-xs"
          >
            <option value="">All customers</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="report-filter-status" className="mb-1 block text-xs font-medium text-slate-600">
            Status
          </label>
          {activeTab === "customer-overview" ? (
            <Select
              id="report-filter-status"
              aria-label="Filter by status"
              value={filters.status || ""}
              onChange={(e) => onFilterChange({ status: e.target.value })}
              className="w-full text-xs"
            >
              <option value="">All customer statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
              <option value="ARCHIVED">Archived</option>
            </Select>
          ) : (
            <Select
              id="report-filter-status"
              aria-label="Filter by status"
              value={filters.status || ""}
              onChange={(e) => onFilterChange({ status: e.target.value })}
              className="w-full text-xs"
            >
              <option value="">All project statuses</option>
              <option value="PLANNING">Planning</option>
              <option value="IN_PROGRESS">In progress</option>
              <option value="ON_HOLD">On hold</option>
              <option value="COMPLETED">Completed</option>
              <option value="ARCHIVED">Archived</option>
            </Select>
          )}
        </div>
      </div>

      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-1 text-xs">
          <span className="text-slate-500">
            Filtered results are displayed.
          </span>
          <button
            type="button"
            onClick={onReset}
            className="font-medium text-brand-600 hover:text-brand-700 underline"
          >
            Reset all filters
          </button>
        </div>
      )}
    </div>
  )
}
