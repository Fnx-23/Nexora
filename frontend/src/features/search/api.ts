import { api } from "@/services/api"
import type { SearchResponse } from "@/types/search"

export async function fetchSearchResults(query: string): Promise<SearchResponse> {
  const { data } = await api.get<SearchResponse>("/search/", { params: { q: query } })
  return data
}