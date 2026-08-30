import { useCallback, useMemo, useState } from "react"
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core"
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable"

import { KanbanColumn } from "./KanbanColumn"
import { TaskCard } from "./TaskCard"
import type { Task, TaskStatus } from "@/types/task"
import { KANBAN_COLUMNS } from "@/types/task"

interface KanbanBoardProps {
  tasks: Task[]
  onStatusChange: (taskId: string, newStatus: TaskStatus) => void
  onTaskClick: (task: Task) => void
}

export function KanbanBoard({
  tasks,
  onStatusChange,
  onTaskClick,
}: KanbanBoardProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  const tasksByStatus = useMemo(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      TODO: [],
      IN_PROGRESS: [],
      IN_REVIEW: [],
      DONE: [],
      CANCELLED: [],
    }
    for (const task of tasks) {
      if (grouped[task.status]) {
        grouped[task.status].push(task)
      }
    }
    return grouped
  }, [tasks])

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      const { active } = event
      const task = tasks.find((t) => t.id === active.id)
      if (task) {
        setActiveTask(task)
      }
    },
    [tasks],
  )

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event
      setActiveTask(null)

      if (!over) return

      const taskId = active.id as string
      const overId = over.id as string

      // Dropped over a column header
      if (KANBAN_COLUMNS.includes(overId as TaskStatus)) {
        const newStatus = overId as TaskStatus
        const task = tasks.find((t) => t.id === taskId)
        if (task && task.status !== newStatus) {
          onStatusChange(taskId, newStatus)
        }
        return
      }

      // Dropped over another task — find which column that task is in
      const overTask = tasks.find((t) => t.id === overId)
      if (overTask) {
        const newStatus = overTask.status
        const task = tasks.find((t) => t.id === taskId)
        if (task && task.status !== newStatus) {
          onStatusChange(taskId, newStatus)
        }
      }
    },
    [tasks, onStatusChange],
  )

  const handleDragCancel = useCallback(() => {
    setActiveTask(null)
  }, [])

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="flex gap-5 overflow-x-auto pb-4">
        {KANBAN_COLUMNS.map((status) => (
          <KanbanColumn
            key={status}
            status={status}
            tasks={tasksByStatus[status]}
            onTaskClick={onTaskClick}
          />
        ))}
      </div>

      <DragOverlay>
        {activeTask && (
          <div className="w-[280px] rotate-2 opacity-90">
            <TaskCard task={activeTask} onClick={() => {}} />
          </div>
        )}
      </DragOverlay>
    </DndContext>
  )
}
