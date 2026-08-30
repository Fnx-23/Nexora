import { useState } from "react"
import { Outlet } from "react-router-dom"

import { Navbar } from "@/components/layout/Navbar"
import { Sidebar } from "@/components/layout/Sidebar"
import { XIcon } from "@/components/icons"

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <Sidebar />
      </aside>

      {/* Mobile sidebar drawer */}
      {sidebarOpen && (
        <div role="presentation" className="fixed inset-0 z-40 lg:hidden">
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-64 shadow-xl">
            <button
              type="button"
              aria-label="Close navigation"
              onClick={() => setSidebarOpen(false)}
              className="absolute top-4 right-3 z-10 rounded-md p-1 text-slate-400 hover:bg-slate-100"
            >
              <XIcon className="size-5" />
            </button>
            <Sidebar onNavigate={() => setSidebarOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-h-screen flex-col lg:pl-64">
        <Navbar onOpenSidebar={() => setSidebarOpen(true)} />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
