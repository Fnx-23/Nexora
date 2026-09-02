import type { Activity } from "@/types/activity"
import { cn } from "@/utils/cn"

import { activityDetail, activitySubject, entityMeta, formatTimestamp, timeAgo } from "./format"

export function ActivityRow({ activity }: { activity: Activity }) {
  const meta = entityMeta(activity.entity_type)
  const subject = activitySubject(activity)
  const detail = activityDetail(activity)
  const actor = activity.actor_name ?? "System"

  return (
    <li className="flex items-start gap-3">
      <span
        aria-hidden="true"
        className={cn(
          "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
          meta.className,
        )}
      >
        {meta.initial}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900">{subject}</p>
        <p className="text-xs text-slate-500">
          {activity.action_display}
          {detail ? (
            <>
              {" · "}
              <span className="text-slate-600">{detail}</span>
            </>
          ) : null}
        </p>
        <p className="mt-0.5 text-xs text-slate-400">
          {actor}
          {" · "}
          <time dateTime={activity.timestamp} title={formatTimestamp(activity.timestamp)}>
            {timeAgo(activity.timestamp)}
          </time>
        </p>
      </div>
    </li>
  )
}
