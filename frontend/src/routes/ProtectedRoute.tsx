import { Navigate, Outlet } from "react-router-dom"

import { LoadingState } from "@/components/ui/LoadingState"
import { useAuth } from "@/hooks/useAuth"

/** Gate for authenticated areas; renders the child route tree when signed in. */
export function ProtectedRoute() {
  const { status } = useAuth()

  if (status === "loading") {
    return <LoadingState className="min-h-screen" label="Preparing your workspace…" />
  }
  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
