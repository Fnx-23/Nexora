import { api } from "@/services/api"
import type { Member } from "@/types/team"

export async function fetchMembers(): Promise<Member[]> {
  const { data } = await api.get<{ results: Member[] }>("/users/")
  return data.results
}
