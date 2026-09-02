import { isAxiosError, type AxiosError } from "axios"

export function isAxiosErrorWithDetail(err: unknown): err is AxiosError {
  return isAxiosError(err) && err.response?.data !== undefined
}
