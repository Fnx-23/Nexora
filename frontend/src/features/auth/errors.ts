import { isAxiosError, type AxiosError } from "axios"

/** True when `err` is an axios error carrying a parsed response body. */
export function isAxiosErrorWithDetail(err: unknown): err is AxiosError {
  return isAxiosError(err) && err.response?.data !== undefined
}
