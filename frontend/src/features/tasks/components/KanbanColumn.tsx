import { useDroppable } from "@dnd-kit/core"
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"

import { TaskCard } from "./TaskCard"
import type { Task, TaskStatus } from "@/types/task"
import { KANBAN_COLUMN_LABELS } from "@/types/task"

const COLUMN_COLORS: Record<TaskStatus, string> = {
  TODO: "border-slate-300",
  IN_PROGRESS: "border-amber-400",
  IN_REVIEW: "border-sky-400",
  DONE: "border-emerald-400",
  CANCELLED: "border-red-300",
}

const COLUMN_DOT_COLORS: Record<TaskStatus, string> = {
  TODO: "bg-slate-400",
  IN_PROGRESS: "bg-amber-400",
  IN_REVIEW: "bg-sky-400",
  DONE: "bg-emerald-400",
  CANCELLED: "bg-red-300",
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
    <div className="flex min-w-[280px] flex-1 flex-col">
      <div
        className={`mb-3 flex items-center gap-2 border-b-2 pb-2.5 ${COLUMN_COLORS[status]}`}
      >
        <div className={`h-2 w-2 rounded-full ${COLUMN_DOT_COLORS[status]}`} />
        <h3 className="text-sm font-semibold text-slate-700">
          {KANBAN_COLUMN_LABELS[status]}
        </h3>
        <span className="ml-auto rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
          {tasks.length}
        </span>
      </div>

      <div
        ref={setNodeRef}
        className={`flex-1 space-y-3 rounded-lg p-1 transition-colors ${
          isOver ? "bg-brand-50 ring-2 ring-brand-300 ring-inset" : ""
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
          <div className="flex h-28 items-center justify-center rounded-lg border-2 border-dashed border-slate-200 text-xs text-slate-400">
            Drop tasks here
          </div>
        )}
      </div>
    </div>
  )
}
