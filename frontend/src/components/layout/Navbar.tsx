import { MenuIcon } from "@/components/icons"
import { NotificationBell } from "@/components/layout/NotificationBell"
import { UserMenu } from "@/components/layout/UserMenu"

interface NavbarProps {
  onOpenSidebar: () => void
}

export function Navbar({ onOpenSidebar }: NavbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-5 md:px-8 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenSidebar}
          aria-label="Open navigation"
          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 lg:hidden"
        >
          <MenuIcon className="size-5" />
        </button>
      </div>

      <div className="flex items-center gap-1">
        <NotificationBell />
        <UserMenu />
      </div>
    </header>
  )
}
