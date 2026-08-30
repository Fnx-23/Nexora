/**
 * TanStack Query key factory scoped to the active company.
 *
 * Every server entity is owned by a company; caches must be invalidated
 * independently when the active company changes (multi-company switching).
 *
 * Usage in components:
 *   const { activeCompany } = useAuth()
 *   const query = useQuery({
 *     queryKey: queryKeys.members(activeCompany?.id ?? null),
 *     queryFn: fetchMembers,
 *   })
 */
export const queryKeys = {
  members: (companyId: string | null) => ["members", companyId] as const,
  customers: (companyId: string | null) => ["customers", companyId] as const,
  customer: (id: string) => ["customer", id] as const,
  projects: (companyId: string | null) => ["projects", companyId] as const,
  project: (id: string) => ["project", id] as const,
  tasks: (companyId: string | null) => ["tasks", companyId] as const,
  task: (id: string) => ["task", id] as const,
  dashboard: (companyId: string | null) => ["dashboard", companyId] as const,
  timeEntries: (companyId: string | null) => ["timeEntries", companyId] as const,
  timeEntrySummary: (companyId: string | null) => ["timeEntrySummary", companyId] as const,
  notifications: (companyId: string | null) => ["notifications", companyId] as const,
  documents: (companyId: string | null) => ["documents", companyId] as const,
} as const
