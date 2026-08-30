import { NavLink } from "react-router-dom"

import {
  ActivityIcon,
  BriefcaseIcon,
  CheckSquareIcon,
  ClockIcon,
  DashboardIcon,
  FolderIcon,
  SettingsIcon,
  UsersIcon,
} from "@/components/icons"
import { cn } from "@/utils/cn"

export const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: DashboardIcon },
  { to: "/projects", label: "Projects", icon: FolderIcon },
  { to: "/customers", label: "Customers", icon: BriefcaseIcon },
  { to: "/tasks", label: "Tasks", icon: CheckSquareIcon },
  { to: "/time-tracking", label: "Time Tracking", icon: ClockIcon },
  { to: "/team", label: "Team", icon: UsersIcon },
  { to: "/activity", label: "Activity", icon: ActivityIcon },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
] as const

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <div className="flex h-full flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 shrink-0 items-center gap-2.5 border-b border-slate-100 px-5">
        <span className="flex size-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
          N
        </span>
        <span className="text-lg font-semibold tracking-tight text-slate-900">Nexora</span>
      </div>

      <nav aria-label="Main navigation" className="flex-1 space-y-1.5 overflow-y-auto px-3 py-5">
        {NAV_ITEMS.map(({ to, label, icon: ItemIcon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 font-semibold text-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
              )
            }
          >
            <ItemIcon className="size-5 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-100 px-5 py-5">
        <p className="text-xs text-slate-400">Nexora v0.1.0</p>
      </div>
    </div>
  )
}
