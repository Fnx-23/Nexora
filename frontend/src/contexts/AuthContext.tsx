import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import { useNavigate } from "react-router-dom"

import { fetchSession, loginRequest } from "@/features/auth/api"
import { tokenStorage } from "@/services/tokenStorage"
import type { SessionResponse } from "@/types/auth"

import { AuthContext, type AuthContextValue, type AuthStatus } from "./authContext"

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [status, setStatus] = useState<AuthStatus>("loading")
  const [session, setSession] = useState<SessionResponse | null>(null)

  const reset = useCallback(() => {
    setSession(null)
    setStatus("unauthenticated")
  }, [])

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      if (!tokenStorage.getAccess()) {
        if (!cancelled) setStatus("unauthenticated")
        return
      }
      try {
        const data = await fetchSession()
        if (cancelled) return
        setSession(data)
        setStatus("authenticated")
      } catch {
        if (cancelled) return
        tokenStorage.clear()
        reset()
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [reset])

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginRequest(email, password)
    tokenStorage.save(tokens.access, tokens.refresh)
    setSession(await fetchSession())
    setStatus("authenticated")
  }, [])

  const logout = useCallback(() => {
    tokenStorage.clear()
    reset()
    navigate("/login", { replace: true })
  }, [navigate, reset])

  const refreshSession = useCallback(async () => {
    const data = await fetchSession()
    setSession(data)
    setStatus("authenticated")
  }, [])

  const activeCompany = session?.active_company ?? null

  const role = useMemo(() => {
    if (!session || !activeCompany) return null
    return (
      session.memberships.find((membership) => membership.company.id === activeCompany.id)
        ?.role ?? null
    )
  }, [session, activeCompany])

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user: session,
      activeCompany,
      role,
      login,
      logout,
      refreshSession,
    }),
    [status, session, activeCompany, role, login, logout, refreshSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
