import { MenuIcon, SearchIcon } from "@/components/icons"
import { NotificationBell } from "@/components/layout/NotificationBell"
import { UserMenu } from "@/components/layout/UserMenu"

interface NavbarProps {
  onOpenSidebar: () => void
  onOpenSearch: () => void
}

export function Navbar({ onOpenSidebar, onOpenSearch }: NavbarProps) {
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

        <button
          type="button"
          onClick={onOpenSearch}
          aria-label="Open search"
          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 lg:hidden"
        >
          <SearchIcon className="size-5" />
        </button>

        <button
          type="button"
          onClick={onOpenSearch}
          aria-label="Search"
          className="hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-400 transition-colors hover:border-slate-300 hover:bg-white hover:text-slate-600 lg:flex"
        >
          <SearchIcon className="size-4" />
          <span>Search</span>
          <kbd className="ml-1 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
            ⌘K
          </kbd>
        </button>
      </div>

      <div className="flex items-center gap-1">
        <NotificationBell />
        <UserMenu />
      </div>
    </header>
  )
}
