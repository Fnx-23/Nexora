import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"

import { BellIcon } from "@/components/icons"
import { useAuth } from "@/hooks/useAuth"
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from "@/features/notifications/api"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"
import type { Notification } from "@/types/notification"

function timeAgo(isoDate: string): string {
  const now = Date.now()
  const then = new Date(isoDate).getTime()
  const diffMin = Math.floor((now - then) / 60_000)
  if (diffMin < 1) return "Just now"
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 30) return `${diffDay}d ago`
  return `${Math.floor(diffDay / 30)}mo ago`
}

function entityIcon(type: string): string {
  switch (type) {
    case "task":
      return "T"
    case "project":
      return "P"
    case "membership":
      return "M"
    case "invitation":
      return "I"
    default:
      return "N"
  }
}

function entityColor(type: string): string {
  switch (type) {
    case "task":
      return "bg-emerald-50 text-emerald-700"
    case "project":
      return "bg-brand-50 text-brand-700"
    case "membership":
      return "bg-amber-50 text-amber-700"
    case "invitation":
      return "bg-violet-50 text-violet-700"
    default:
      return "bg-slate-100 text-slate-600"
  }
}

type Grouped = { label: string; items: Notification[] }[]

function groupNotifications(items: Notification[]): Grouped {
  const now = new Date()
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const startOfWeek = startOfDay - 6 * 86_400_000
  const groups: Grouped = [
    { label: "Today", items: [] },
    { label: "This week", items: [] },
    { label: "Earlier", items: [] },
  ]
  for (const n of items) {
    const ts = new Date(n.created_at).getTime()
    if (ts >= startOfDay) groups[0].items.push(n)
    else if (ts >= startOfWeek) groups[1].items.push(n)
    else groups[2].items.push(n)
  }
  return groups.filter((g) => g.items.length > 0)
}

export function NotificationBell() {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const unreadQuery = useQuery({
    queryKey: [...queryKeys.notifications(companyId), "unread-count"],
    queryFn: fetchUnreadCount,
    enabled: companyId !== null,
    refetchInterval: 30_000,
  })

  const notificationsQuery = useQuery({
    queryKey: [...queryKeys.notifications(companyId), "list"],
    queryFn: () => fetchNotifications({ page_size: 20 }),
    enabled: companyId !== null && open,
  })

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.notifications(companyId) })
    },
  })

  const markAllMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.notifications(companyId) })
    },
  })

  const handleClickOutside = useCallback(
    (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    },
    [],
  )

  useEffect(() => {
    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      return () => document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [open, handleClickOutside])

  const unreadCount = unreadQuery.data?.count ?? 0
  const notifications = useMemo(
    () => notificationsQuery.data?.results ?? [],
    [notificationsQuery.data],
  )
  const grouped = useMemo(() => groupNotifications(notifications), [notifications])

  function handleNotificationClick(notification: Notification) {
    if (!notification.is_read) {
      markReadMutation.mutate(notification.id)
    }
    setOpen(false)
  }

  function handleMarkAllRead() {
    markAllMutation.mutate()
  }

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-md p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
      >
        <BellIcon className="size-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          ref={dropdownRef}
          role="menu"
          className="absolute right-0 z-50 mt-1.5 w-80 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
              {unreadCount > 0 && (
                <p className="text-xs text-slate-400">
                  {unreadCount} unread notification{unreadCount === 1 ? "" : "s"}
                </p>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-xs font-medium text-brand-600 hover:text-brand-700"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notificationsQuery.isPending && (
              <div className="px-4 py-6 text-center text-sm text-slate-500">Loading…</div>
            )}

            {!notificationsQuery.isPending && notifications.length === 0 && (
              <div className="px-4 py-6 text-center text-sm text-slate-500">
                No notifications yet.
              </div>
            )}

            {grouped.map((group) => (
              <div key={group.label}>
                <p className="bg-slate-50 px-4 py-1.5 text-[11px] font-semibold tracking-wide text-slate-400 uppercase">
                  {group.label}
                </p>
                {group.items.map((n) => (
                  <Link
                    key={n.id}
                    to={n.link || "#"}
                    onClick={() => handleNotificationClick(n)}
                    className={cn(
                      "flex gap-3 border-b border-slate-50 px-4 py-2.5 transition-colors hover:bg-slate-50",
                      !n.is_read && "bg-brand-50/40",
                    )}
                  >
                    <span
                      className={cn(
                        "flex size-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold",
                        entityColor(n.entity_type),
                      )}
                    >
                      {entityIcon(n.entity_type)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p
                        className={cn(
                          "text-sm leading-snug",
                          n.is_read ? "text-slate-600" : "font-medium text-slate-900",
                        )}
                      >
                        {n.verb}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {n.actor_name} · {timeAgo(n.created_at)}
                      </p>
                    </div>
                    {!n.is_read && (
                      <span className="mt-0.5 size-1.5 shrink-0 rounded-full bg-brand-500" />
                    )}
                  </Link>
                ))}
              </div>
            ))}
          </div>

          {notifications.length > 0 && (
            <div className="border-t border-slate-100 px-4 py-2 text-center">
              <Link
                to="/dashboard"
                onClick={() => setOpen(false)}
                className="text-xs font-medium text-brand-600 hover:text-brand-700"
              >
                View all
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}