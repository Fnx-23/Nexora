import { NavLink, Navigate, useParams } from "react-router-dom"

import { AccountPage } from "@/pages/AccountPage"
import { MembersPage } from "@/pages/MembersPage"
import { NotificationSettingsPage } from "@/pages/NotificationSettingsPage"
import { SecurityPage } from "@/pages/SecurityPage"
import { WorkspacePage } from "@/pages/WorkspacePage"

type Tab = "account" | "security" | "workspace" | "members" | "notifications"

const TABS: { key: Tab; label: string }[] = [
  { key: "account", label: "Account" },
  { key: "security", label: "Security" },
  { key: "workspace", label: "Workspace" },
  { key: "members", label: "Members" },
  { key: "notifications", label: "Notifications" },
]

export function SettingsLayout() {
  const { tab } = useParams<{ tab?: string }>()
  const currentTab = (tab ?? "account").toLowerCase()

  const renderTabContent = () => {
    switch (currentTab) {
      case "account":
        return <AccountPage />
      case "security":
        return <SecurityPage />
      case "workspace":
        return <WorkspacePage />
      case "members":
        return <MembersPage />
      case "notifications":
        return <NotificationSettingsPage />
      default:
        return <Navigate to="/settings/account" replace />
    }
  }

  return (
    <div>
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex gap-8 px-1" aria-label="Settings tabs">
          {TABS.map(({ key, label }) => {
            const isActive = currentTab === key
            return (
              <NavLink
                key={key}
                to={`/settings/${key}`}
                className={`border-b-2 px-1 pb-3 text-sm font-medium transition-colors ${
                  isActive
                    ? "border-brand-600 text-brand-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {label}
              </NavLink>
            )
          })}
        </nav>
      </div>

      <div className="py-6">
        {renderTabContent()}
      </div>
    </div>
  )
}