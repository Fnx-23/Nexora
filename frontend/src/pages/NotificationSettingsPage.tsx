import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { Card, CardContent, CardDescription, CardDivider, CardHeader, CardTitle } from "@/components/ui/Card"
import { LoadingState } from "@/components/ui/LoadingState"
import { useAuth } from "@/hooks/useAuth"
import { fetchNotificationPreferences, updateNotificationPreferences } from "@/features/notifications/api"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"
import type { NotificationPreferenceKey } from "@/types/notification"

const IN_APP_CATEGORIES: {
  key: NotificationPreferenceKey
  title: string
  description: string
}[] = [
  {
    key: "task_assigned",
    title: "Task assignments",
    description: "When a task is assigned or reassigned to you.",
  },
  {
    key: "task_due_soon",
    title: "Task due soon",
    description: "When one of your tasks is due within 3 days.",
  },
  {
    key: "task_overdue",
    title: "Task overdue",
    description: "When one of your tasks becomes overdue.",
  },
  {
    key: "task_comment",
    title: "Task comments",
    description: "When someone comments on a task you are assigned to.",
  },
  {
    key: "project_assigned",
    title: "Project assignments",
    description: "When you are made a manager of, or added to, a project.",
  },
  {
    key: "project_deadline",
    title: "Project deadlines",
    description: "When a project deadline is approaching.",
  },
  {
    key: "invitation_received",
    title: "Invitations",
    description: "When you are invited to join a company.",
  },
  {
    key: "role_changed",
    title: "Role changes",
    description: "When your role within the company changes.",
  },
]

const EMAIL_CATEGORIES: {
  key: NotificationPreferenceKey
  title: string
  description: string
}[] = [
  {
    key: "email_task_assigned",
    title: "Task assignments",
    description: "Receive an email when a task is assigned or reassigned to you.",
  },
  {
    key: "email_task_due_soon",
    title: "Task due soon",
    description: "Receive an email when one of your tasks is due within 3 days.",
  },
  {
    key: "email_task_overdue",
    title: "Task overdue",
    description: "Receive an email when one of your tasks becomes overdue.",
  },
  {
    key: "email_task_comment",
    title: "Task comments",
    description: "Receive an email when someone comments on a task you are assigned to.",
  },
  {
    key: "email_project_assigned",
    title: "Project assignments",
    description: "Receive an email when you are added to a project.",
  },
  {
    key: "email_project_deadline",
    title: "Project deadlines",
    description: "Receive an email when a project deadline is approaching.",
  },
  {
    key: "email_invitation_received",
    title: "Invitations",
    description: "Receive an email when you are invited to join a company.",
  },
  {
    key: "email_role_changed",
    title: "Role changes",
    description: "Receive an email when your role within the company changes.",
  },
]

export function NotificationSettingsPage() {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null
  const queryClient = useQueryClient()

  const preferencesQuery = useQuery({
    queryKey: queryKeys.notificationPreferences(companyId),
    queryFn: fetchNotificationPreferences,
    enabled: companyId !== null,
  })

  const mutation = useMutation({
    mutationFn: updateNotificationPreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.notificationPreferences(companyId), data)
    },
  })

  function handleToggle(key: NotificationPreferenceKey, value: boolean) {
    mutation.mutate({ [key]: value })
  }

  const preferences = preferencesQuery.data
  const pendingKey = mutation.isPending
    ? (mutation.variables && Object.keys(mutation.variables)[0]) ?? null
    : null

  return (
    <div className="space-y-4 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>In-app Notifications</CardTitle>
          <CardDescription>
            Choose which notifications you want to see for {activeCompany?.name ?? "this company"}.
          </CardDescription>
        </CardHeader>
        <CardDivider />
        <CardContent>
          {preferencesQuery.isPending && <LoadingState label="Loading preferences…" />}

          {preferencesQuery.isError && (
            <p className="text-sm text-red-600">Failed to load notification preferences.</p>
          )}

          {preferences && (
            <ul className="divide-y divide-slate-100">
              {IN_APP_CATEGORIES.map(({ key, title, description }) => (
                <li key={key} className="flex items-center justify-between gap-4 py-4">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{title}</p>
                    <p className="text-sm text-slate-500">{description}</p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={preferences[key]}
                    aria-label={`In-app: ${title}`}
                    disabled={mutation.isPending}
                    onClick={() => handleToggle(key, !preferences[key])}
                    className={cn(
                      "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors",
                      preferences[key] ? "bg-brand-600" : "bg-slate-300",
                      mutation.isPending && "opacity-60",
                    )}
                  >
                    <span
                      className={cn(
                        "inline-block size-4 transform rounded-full bg-white shadow transition-transform",
                        preferences[key] ? "translate-x-6" : "translate-x-1",
                      )}
                    />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Email Notifications</CardTitle>
          <CardDescription>
            Choose which notifications you want to receive by email for {activeCompany?.name ?? "this company"}.
          </CardDescription>
        </CardHeader>
        <CardDivider />
        <CardContent>
          {preferencesQuery.isPending && <LoadingState label="Loading email preferences…" />}

          {preferencesQuery.isError && (
            <p className="text-sm text-red-600">Failed to load notification preferences.</p>
          )}

          {preferences && (
            <ul className="divide-y divide-slate-100">
              {EMAIL_CATEGORIES.map(({ key, title, description }) => (
                <li key={key} className="flex items-center justify-between gap-4 py-4">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{title}</p>
                    <p className="text-sm text-slate-500">{description}</p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={preferences[key]}
                    aria-label={`Email: ${title}`}
                    disabled={mutation.isPending}
                    onClick={() => handleToggle(key, !preferences[key])}
                    className={cn(
                      "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors",
                      preferences[key] ? "bg-brand-600" : "bg-slate-300",
                      mutation.isPending && "opacity-60",
                    )}
                  >
                    <span
                      className={cn(
                        "inline-block size-4 transform rounded-full bg-white shadow transition-transform",
                        preferences[key] ? "translate-x-6" : "translate-x-1",
                      )}
                    />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {pendingKey && (
        <p className="text-xs text-slate-400 text-right">Saving…</p>
      )}
    </div>
  )
}