import { createContext } from "react"

import type { CompanyRef, Role } from "@/types/auth"

export type AuthStatus = "loading" | "authenticated" | "unauthenticated"

export interface AuthContextValue {
  status: AuthStatus
  user: {
    id: string
    email: string
    first_name: string
    last_name: string
    avatar: string | null
    full_name: string
  } | null
  activeCompany: CompanyRef | null
  role: Role | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshSession: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
