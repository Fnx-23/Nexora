import { api } from "@/services/api"
import type {
  CreateInvitationPayload,
  Invitation,
  InvitationValidation,
  Member,
} from "@/types/team"

export async function fetchMembers(): Promise<Member[]> {
  const { data } = await api.get<{ results: Member[] }>("/users/")
  return data.results
}

export async function fetchInvitations(): Promise<Invitation[]> {
  const { data } = await api.get<{ results: Invitation[] }>("/companies/invitations/")
  return data.results
}

export async function createInvitation(payload: CreateInvitationPayload): Promise<Invitation> {
  const { data } = await api.post<Invitation>("/companies/invitations/", payload)
  return data
}

export async function revokeInvitation(id: string): Promise<Invitation> {
  const { data } = await api.post<Invitation>(`/companies/invitations/${id}/revoke/`)
  return data
}

export async function resendInvitation(id: string): Promise<Invitation> {
  const { data } = await api.post<Invitation>(`/companies/invitations/${id}/resend/`)
  return data
}

export async function changeMemberRole(membershipId: string, role: string): Promise<Member> {
  const { data } = await api.patch<Member>(`/companies/members/${membershipId}/role/`, { role })
  return data
}

export async function deactivateMember(membershipId: string): Promise<Member> {
  const { data } = await api.post<Member>(`/companies/members/${membershipId}/deactivate/`)
  return data
}

export async function reactivateMember(membershipId: string): Promise<Member> {
  const { data } = await api.post<Member>(`/companies/members/${membershipId}/reactivate/`)
  return data
}

export async function removeMember(membershipId: string): Promise<void> {
  await api.delete(`/companies/members/${membershipId}/`)
}

export async function validateInvitation(token: string): Promise<InvitationValidation> {
  const { data } = await api.post<InvitationValidation>("/invitations/validate/", { token })
  return data
}

export async function acceptInvitation(token: string): Promise<Member> {
  const { data } = await api.post<Member>(`/invitations/accept/${token}/`)
  return data
}

export async function registerAndAcceptInvitation(payload: {
  token: string
  email: string
  first_name: string
  last_name: string
  password: string
}): Promise<{ tokens: { access: string; refresh: string } }> {
  const { data } = await api.post<{ tokens: { access: string; refresh: string } }>(
    "/invitations/register/",
    payload,
  )
  return data
}
