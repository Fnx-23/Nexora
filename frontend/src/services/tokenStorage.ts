const ACCESS_KEY = "nexora.access"
const REFRESH_KEY = "nexora.refresh"

export const tokenStorage = {
  getAccess(): string | null {
    return localStorage.getItem(ACCESS_KEY)
  },
  getRefresh(): string | null {
    return localStorage.getItem(REFRESH_KEY)
  },
  save(access: string, refresh?: string): void {
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) {
      localStorage.setItem(REFRESH_KEY, refresh)
    }
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}
