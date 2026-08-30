import { api } from "@/services/api"
import type { AuthTokens, SessionResponse, User } from "@/types/auth"

interface LoginResponse extends AuthTokens {
  user: User
}

export async function loginRequest(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/token/", { email, password })
  return data
}

export async function fetchSession(): Promise<SessionResponse> {
  const { data } = await api.get<SessionResponse>("/auth/me/")
  return data
}
