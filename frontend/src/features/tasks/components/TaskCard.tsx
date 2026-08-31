import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

import { Badge, StatusBadge } from "@/components/ui/Badge"
import { Avatar } from "@/components/ui/Avatar"
import type { Task } from "@/types/task"

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  })
}

interface TaskCardProps {
  task: Task
  onClick: (task: Task) => void
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: task.id,
    data: { task },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const isOverdue =
    task.due_date && new Date(task.due_date) < new Date() && task.status !== "DONE"

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onClick(task)}
      className={`group cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition-all hover:shadow-md active:cursor-grabbing ${
        isDragging ? "opacity-50 shadow-lg ring-1 ring-brand-400" : ""
      }`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-slate-900 line-clamp-2 leading-snug">
          {task.title}
        </h4>
        <StatusBadge value={task.priority} className="shrink-0" />
      </div>

      {task.description && (
        <p className="mb-2 text-xs text-slate-500 line-clamp-2 leading-relaxed">
          {task.description}
        </p>
      )}

      {task.project_name && (
        <div className="mb-2">
          <Badge variant="brand" className="text-[10px]">
            {task.project_name}
          </Badge>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {task.assignee_name && (
            <div className="flex items-center gap-1.5">
              <Avatar name={task.assignee_name} size="xs" />
              <span className="text-xs text-slate-500">{task.assignee_name}</span>
            </div>
          )}
        </div>
        {task.due_date && (
          <span
            className={`text-[11px] font-medium ${
              isOverdue ? "text-red-500" : "text-slate-400"
            }`}
          >
            {formatDate(task.due_date)}
          </span>
        )}
      </div>
    </div>
  )
}
