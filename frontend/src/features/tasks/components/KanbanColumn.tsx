import { useDroppable } from "@dnd-kit/core"
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"

import { TaskCard } from "./TaskCard"
import type { Task, TaskStatus } from "@/types/task"
import { KANBAN_COLUMN_LABELS } from "@/types/task"

const COLUMN_ACCENT: Record<TaskStatus, string> = {
  TODO: "border-slate-400",
  IN_PROGRESS: "border-amber-500",
  IN_REVIEW: "border-sky-500",
  DONE: "border-emerald-500",
  CANCELLED: "border-red-400",
}

const COLUMN_DOT: Record<TaskStatus, string> = {
  TODO: "bg-slate-400",
  IN_PROGRESS: "bg-amber-500",
  IN_REVIEW: "bg-sky-500",
  DONE: "bg-emerald-500",
  CANCELLED: "bg-red-400",
}

interface KanbanColumnProps {
  status: TaskStatus
  tasks: Task[]
  onTaskClick: (task: Task) => void
}

export function KanbanColumn({ status, tasks, onTaskClick }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: { status },
  })

  return (
    <div className="flex min-w-[260px] flex-1 flex-col">
      <div
        className={`mb-3 flex items-center gap-2 border-b-2 pb-2 ${COLUMN_ACCENT[status]}`}
      >
        <div className={`h-2 w-2 rounded-full ${COLUMN_DOT[status]}`} />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {KANBAN_COLUMN_LABELS[status]}
        </h3>
        <span className="ml-auto text-xs font-medium text-slate-400">
          {tasks.length}
        </span>
      </div>

      <div
        ref={setNodeRef}
        className={`flex-1 rounded-lg p-1.5 transition-colors ${
          isOver ? "bg-brand-50/60 ring-1 ring-brand-300" : "bg-slate-50/50"
        }`}
      >
        <SortableContext
          items={tasks.map((t) => t.id)}
          strategy={verticalListSortingStrategy}
        >
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} onClick={onTaskClick} />
          ))}
        </SortableContext>

        {tasks.length === 0 && (
          <div className="flex h-20 items-center justify-center rounded-lg border border-dashed border-slate-200 text-xs text-slate-400">
            Drop here
          </div>
        )}
      </div>
    </div>
  )
}
