/** Shared API response types matching the backend envelope. */

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiErrorDetail {
  detail?: string
  [field: string]: string | string[] | undefined
}
