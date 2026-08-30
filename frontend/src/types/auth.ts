/** Auth/domain types mirroring the backend serializers (snake_case on purpose). */

export type Role = "ADMIN" | "MANAGER" | "EMPLOYEE"

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  avatar: string | null
  full_name: string
}

export interface CompanyRef {
  id: string
  name: string
  slug: string
}

export interface Membership {
  id: string
  company: CompanyRef
  role: Role
  is_active: boolean
}

export interface SessionResponse extends User {
  memberships: Membership[]
  active_company: CompanyRef | null
}

export interface AuthTokens {
  access: string
  refresh: string
}
