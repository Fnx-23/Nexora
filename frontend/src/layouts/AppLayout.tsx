import { useCallback, useEffect, useState } from "react"
import { Outlet } from "react-router-dom"

import { CommandPalette } from "@/components/command/CommandPalette"
import { Navbar } from "@/components/layout/Navbar"
import { Sidebar } from "@/components/layout/Sidebar"
import { XIcon } from "@/components/icons"

function useKeyboardShortcuts(togglePalette: () => void) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        togglePalette()
      }
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [togglePalette])
}

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)

  const togglePalette = useCallback(() => setPaletteOpen((open) => !open), [])
  useKeyboardShortcuts(togglePalette)

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[256px] lg:block">
        <Sidebar />
      </aside>

      {sidebarOpen && (
        <div role="presentation" className="fixed inset-0 z-40 lg:hidden">
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-[256px] shadow-lg">
            <button
              type="button"
              aria-label="Close navigation"
              onClick={() => setSidebarOpen(false)}
              className="absolute top-3 right-3 z-10 rounded-md p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            >
              <XIcon className="size-5" />
            </button>
            <Sidebar onNavigate={() => setSidebarOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-h-screen lg:pl-[256px]">
        <div className="flex flex-1 flex-col">
          <Navbar
            onOpenSidebar={() => setSidebarOpen(true)}
            onOpenSearch={() => setPaletteOpen(true)}
          />
          <main className="flex-1 bg-slate-50 px-5 py-7 md:px-8 md:py-8 xl:px-10">
      <div className="mx-auto w-full">
              <Outlet />
            </div>
          </main>
        </div>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  )
}
