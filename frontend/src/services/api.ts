import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios"

import { tokenStorage } from "@/services/tokenStorage"

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1"

export const api = axios.create({ baseURL })

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshInFlight: Promise<string> | null = null

async function requestNewAccessToken(): Promise<string> {
  const refresh = tokenStorage.getRefresh()
  if (!refresh) {
    throw new Error("No refresh token available.")
  }
  // Raw axios call: no interceptors, no retry loop.
  const response = await axios.post<{ access: string; refresh?: string }>(
    `${baseURL}/auth/token/refresh/`,
    { refresh },
  )
  const { access, refresh: rotated } = response.data
  tokenStorage.save(access, rotated ?? refresh)
  return access
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryableConfig | undefined
    const isAuthEndpoint = original?.url?.includes("/auth/token/") ?? false

    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      isAuthEndpoint ||
      !tokenStorage.getRefresh()
    ) {
      return Promise.reject(error)
    }

    try {
      refreshInFlight ??= requestNewAccessToken().finally(() => {
        refreshInFlight = null
      })
      const access = await refreshInFlight
      original._retry = true
      original.headers.Authorization = `Bearer ${access}`
      return api(original)
    } catch {
      tokenStorage.clear()
      window.location.assign("/login")
      return Promise.reject(error)
    }
  },
)
