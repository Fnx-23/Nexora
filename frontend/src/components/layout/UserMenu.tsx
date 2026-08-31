import { useNavigate } from "react-router-dom"

import { useAuth } from "@/hooks/useAuth"

import { Avatar } from "@/components/ui/Avatar"
import {
  Dropdown,
  DropdownItem,
  DropdownLabel,
  DropdownSeparator,
} from "@/components/ui/Dropdown"
import { ChevronDownIcon, LogOutIcon, SettingsIcon } from "@/components/icons"

export function UserMenu() {
  const { user, activeCompany, role, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null

  return (
    <Dropdown
      trigger={({ toggle, triggerProps }) => (
        <button
          type="button"
          {...triggerProps}
          onClick={toggle}
          aria-label="Open user menu"
          className="flex items-center gap-2 rounded-md p-1.5 transition-colors hover:bg-slate-100"
        >
          <Avatar name={user.full_name || user.email} src={user.avatar} size="sm" />
          <span className="hidden text-left sm:block">
            <span className="block max-w-36 truncate text-sm font-medium text-slate-900">
              {user.first_name || user.email}
            </span>
            {role && activeCompany && (
              <span className="block text-xs text-slate-500">{activeCompany.name}</span>
            )}
          </span>
          <ChevronDownIcon className="hidden size-3.5 text-slate-400 sm:block" />
        </button>
      )}
    >
      <DropdownLabel>
        <span className="block truncate font-medium text-slate-700">
          {user.full_name || user.email}
        </span>
        <span className="mt-0.5 block truncate text-xs text-slate-500">{user.email}</span>
      </DropdownLabel>
      <DropdownSeparator />
      <DropdownItem onClick={() => void navigate("/settings")}>
        <SettingsIcon className="size-3.5" />
        Account settings
      </DropdownItem>
      <DropdownSeparator />
      <DropdownItem danger onClick={logout}>
        <LogOutIcon className="size-3.5" />
        Sign out
      </DropdownItem>
    </Dropdown>
  )
}
