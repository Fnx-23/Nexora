import { MenuIcon } from "@/components/icons"
import { NotificationBell } from "@/components/layout/NotificationBell"
import { UserMenu } from "@/components/layout/UserMenu"

interface NavbarProps {
  onOpenSidebar: () => void
}

export function Navbar({ onOpenSidebar }: NavbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenSidebar}
          aria-label="Open navigation"
          className="rounded-md p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 lg:hidden"
        >
          <MenuIcon className="size-5" />
        </button>
        <span className="text-sm font-medium text-slate-400 lg:hidden">Nexora</span>
      </div>

      <div className="flex items-center gap-1.5">
        <NotificationBell />
        <UserMenu />
      </div>
    </header>
  )
}
