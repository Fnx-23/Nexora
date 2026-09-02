export const queryKeys = {
  members: (companyId: string | null) => ["members", companyId] as const,
  invitations: (companyId: string | null) => ["invitations", companyId] as const,
  customers: (companyId: string | null) => ["customers", companyId] as const,
  customer: (id: string) => ["customer", id] as const,
  projects: (companyId: string | null) => ["projects", companyId] as const,
  project: (id: string) => ["project", id] as const,
  projectMembers: (id: string) => ["projectMembers", id] as const,
  tasks: (companyId: string | null) => ["tasks", companyId] as const,
  task: (id: string) => ["task", id] as const,
  taskComments: (id: string) => ["taskComments", id] as const,
  taskChecklist: (id: string) => ["taskChecklist", id] as const,
  taskSubtasks: (id: string) => ["taskSubtasks", id] as const,
  labels: (companyId: string | null) => ["labels", companyId] as const,
  dashboard: (companyId: string | null) => ["dashboard", companyId] as const,
  timeEntries: (companyId: string | null) => ["timeEntries", companyId] as const,
  timeEntrySummary: (companyId: string | null) => ["timeEntrySummary", companyId] as const,
  notifications: (companyId: string | null) => ["notifications", companyId] as const,
  notificationPreferences: (companyId: string | null) =>
    ["notificationsPreferences", companyId] as const,
  documents: (companyId: string | null) => ["documents", companyId] as const,
  search: (companyId: string | null, query: string) =>
    ["search", companyId, "query", query] as const,
  workspace: (companyId: string | null) => ["workspace", companyId] as const,
  securityEvents: () => ["securityEvents"] as const,
  reports: {
    projectPerformance: (companyId: string | null, params?: unknown) =>
      ["reports", "projectPerformance", companyId, params] as const,
    teamWorkload: (companyId: string | null, params?: unknown) =>
      ["reports", "teamWorkload", companyId, params] as const,
    time: (companyId: string | null, params?: unknown) =>
      ["reports", "time", companyId, params] as const,
    customerOverview: (companyId: string | null, params?: unknown) =>
      ["reports", "customerOverview", companyId, params] as const,
    summary: (companyId: string | null, params?: unknown) =>
      ["reports", "summary", companyId, params] as const,
  },
} as const
