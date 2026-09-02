import type { User } from "./auth"

export interface SessionResponse extends User {
  memberships: import("./auth").Membership[]
  active_company: import("./auth").CompanyRef | null
  is_email_verified?: boolean
  created_at?: string
}
