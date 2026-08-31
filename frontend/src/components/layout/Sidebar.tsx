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

interface NavItem {
  to: string
  label: string
  icon: React.FC<React.SVGProps<SVGSVGElement>>
  section: string
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: DashboardIcon, section: "Overview" },
  { to: "/projects", label: "Projects", icon: FolderIcon, section: "Work" },
  { to: "/customers", label: "Customers", icon: BriefcaseIcon, section: "Work" },
  { to: "/tasks", label: "Tasks", icon: CheckSquareIcon, section: "Work" },
  { to: "/time-tracking", label: "Time Tracking", icon: ClockIcon, section: "Work" },
  { to: "/team", label: "Team", icon: UsersIcon, section: "Organization" },
  { to: "/activity", label: "Activity", icon: ActivityIcon, section: "Organization" },
  { to: "/settings", label: "Settings", icon: SettingsIcon, section: "Organization" },
] as const

const SECTION_ORDER = ["Overview", "Work", "Organization"] as const

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <aside className="flex h-full flex-col bg-slate-900">
      {/* Logo */}
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-800/80 px-5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white shadow-sm">
          N
        </div>
        <span className="text-base font-semibold tracking-tight text-white">Nexora</span>
      </div>

      {/* Navigation */}
      <nav aria-label="Main navigation" className="flex-1 overflow-y-auto px-3 py-5">
        {SECTION_ORDER.map((sectionLabel) => {
          const sectionItems = NAV_ITEMS.filter((item) => item.section === sectionLabel)
          return (
            <div key={sectionLabel} className="mb-6 last:mb-0">
              <p className="mb-2.5 px-3 text-[11px] font-semibold uppercase tracking-widest text-slate-500">
                {sectionLabel}
              </p>
              <div className="space-y-0.5">
                {sectionItems.map(({ to, label, icon: ItemIcon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    onClick={onNavigate}
                    end
                    className={({ isActive }) =>
                      cn(
                        "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                        "h-11",
                        isActive
                          ? "bg-brand-600/15 text-brand-400"
                          : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200",
                      )
                    }
                  >
                    <ItemIcon className="size-5 shrink-0 transition-colors" />
                    {label}
                  </NavLink>
                ))}
              </div>
            </div>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-800/80 px-5 py-4">
        <p className="text-xs text-slate-600">Nexora v0.1.0</p>
      </div>
    </aside>
  )
}
