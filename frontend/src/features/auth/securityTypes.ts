export interface ChangePasswordForm {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface ForgotPasswordForm {
  email: string
}

export interface ResetPasswordForm {
  token: string
  new_password: string
  confirm_password: string
}

export interface SessionDeviceInfo {
  id: string
  browser: string
  device: string
  ip_address: string | null
  created_at: string
  last_activity: string
  is_current: boolean
}

export type SecurityEventType =
  | "login"
  | "login_failed"
  | "password_changed"
  | "password_reset"
  | "email_verified"
  | "profile_updated"
  | "session_revoked"
  | "sessions_revoked_others"

export interface SecurityEvent {
  id: string
  event_type: SecurityEventType
  ip_address: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface SecurityResponse {
  detail: string
}
