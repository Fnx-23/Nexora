import { api } from "@/services/api"
import type {
  ChangePasswordForm,
  ForgotPasswordForm,
  ResetPasswordForm,
  SecurityEvent,
  SecurityResponse,
  SessionDeviceInfo,
} from "@/features/auth/securityTypes"
import type { Paginated } from "@/types/api"

export async function changePassword(data: ChangePasswordForm): Promise<SecurityResponse> {
  const { data: result } = await api.post<SecurityResponse>("/auth/change-password/", data)
  return result
}

export async function forgotPassword(data: ForgotPasswordForm): Promise<SecurityResponse> {
  const { data: result } = await api.post<SecurityResponse>("/auth/forgot-password/", data)
  return result
}

export async function resetPassword(data: ResetPasswordForm & { token_id: string }): Promise<SecurityResponse> {
  const { data: result } = await api.post<SecurityResponse>(`/auth/reset-password/${data.token_id}/`, {
    token: data.token,
    new_password: data.new_password,
    confirm_password: data.confirm_password,
  })
  return result
}

export async function verifyEmail(): Promise<SecurityResponse> {
  const { data: result } = await api.post<SecurityResponse>("/auth/verify-email/")
  return result
}

export async function fetchSessions(): Promise<Paginated<SessionDeviceInfo>> {
  const { data } = await api.get<Paginated<SessionDeviceInfo>>("/auth/sessions/")
  return data
}

export async function fetchSecurityEvents(): Promise<Paginated<SecurityEvent>> {
  const { data } = await api.get<Paginated<SecurityEvent>>("/auth/security-events/")
  return data
}

export async function revokeSession(sessionId: string): Promise<SecurityResponse> {
  const { data } = await api.post<SecurityResponse>(`/auth/sessions/${sessionId}/revoke/`)
  return data
}

export async function revokeAllOtherSessions(): Promise<SecurityResponse> {
  const { data } = await api.post<SecurityResponse>("/auth/sessions/revoke-others/")
  return data
}
