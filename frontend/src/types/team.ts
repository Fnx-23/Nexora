import type { Role } from "@/types/auth"

export interface Member {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: Role | ""
  membership_id: string
  membership_active: boolean
  joined_at: string | null
}

export type InvitationStatus = "PENDING" | "ACCEPTED" | "EXPIRED" | "REVOKED"

export interface Invitation {
  id: string
  email: string
  role: Role | ""
  status: InvitationStatus
  invited_by: string | null
  invited_by_name: string | null
  created_at: string
  expires_at: string
}

export interface CreateInvitationPayload {
  email: string
  role: Role
}

export interface InvitationValidation {
  email: string
  company_name: string
  role: Role
  user_exists: boolean
}
