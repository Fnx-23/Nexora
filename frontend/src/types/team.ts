import type { Role } from "@/types/auth"

/** A company member as returned by GET /api/v1/users/. */
export interface Member {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: Role | ""
}
