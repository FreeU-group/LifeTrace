'use client';

import { Task, TaskStatus } from '@/lib/types';
import TaskItem from './TaskItem';
import { cn } from '@/lib/utils';
import { Circle, CircleDot, CheckCircle2, XCircle } from 'lucide-react';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  useSensor,
  useSensors,
  PointerSensor,
  closestCorners,
  useDroppable,
  useDraggable,
} from '@dnd-kit/core';
import { useState } from 'react';

interface TaskBoardProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  onStatusChange: (taskId: number, newStatus: string) => void;
  projectId?: number;
  selectedTaskIds?: Set<number>;
  onToggleSelect?: (task: Task, selected: boolean) => void;
  className?: string;
}

const columns = [
  {
    status: 'pending' as TaskStatus,
    label: '待办',
    icon: Circle,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/30',
    borderColor: 'border-muted-foreground/20',
  },
  {
    status: 'in_progress' as TaskStatus,
    label: '进行中',
    icon: CircleDot,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-500/5',
    borderColor: 'border-blue-500/20',
  },
  {
    status: 'completed' as TaskStatus,
    label: '已完成',
    icon: CheckCircle2,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-500/5',
    borderColor: 'border-green-500/20',
  },
  {
    status: 'cancelled' as TaskStatus,
    label: '已取消',
    icon: XCircle,
    color: 'text-destructive',
    bgColor: 'bg-destructive/5',
    borderColor: 'border-destructive/20',
  },
];

export default function TaskBoard({
  tasks,
  onEdit,
  onDelete,
  onStatusChange,
  projectId,
  selectedTaskIds,
  onToggleSelect,
  className,
}: TaskBoardProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  // 配置拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 需要拖动 8px 才激活，避免误触
      },
    })
  );

  // 按状态分组任务
  const groupTasksByStatus = (tasks: Task[]) => {
    const grouped: Record<TaskStatus, Task[]> = {
      pending: [],
      in_progress: [],
      completed: [],
      cancelled: [],
    };

    tasks.forEach((task) => {
      const status = task.status as TaskStatus;
      if (grouped[status]) {
        grouped[status].push(task);
      }
    });

    return grouped;
  };

  const groupedTasks = groupTasksByStatus(tasks);

  // 拖拽开始
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const taskId = active.id as number;
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      setActiveTask(task);
    }
  };

  // 拖拽结束
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const taskId = active.id as number;
    const newStatus = over.id as TaskStatus;

    // 找到当前任务
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;

    // 如果状态没有变化，不需要更新
    if (task.status === newStatus) return;

    // 调用状态更改回调
    onStatusChange(taskId, newStatus);
  };

  // 拖拽取消
  const handleDragCancel = () => {
    setActiveTask(null);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className={cn('grid grid-cols-4 gap-4 h-full', className)}>
        {columns.map((column) => {
          const Icon = column.icon;
          const columnTasks = groupedTasks[column.status];

          return (
            <div
              key={column.status}
              className="flex flex-col min-h-0"
            >
              {/* 列头 */}
              <div className={cn(
                'flex items-center gap-2 px-4 py-3 border-b bg-card rounded-t-lg',
                'border-border shadow-sm'
              )}>
                <Icon className={cn('h-4 w-4 flex-shrink-0', column.color)} />
                <h3 className={cn('font-medium text-sm', column.color)}>
                  {column.label}
                </h3>
                <span className={cn(
                  'ml-auto text-xs font-medium px-2 py-0.5 rounded-full',
                  column.bgColor,
                  column.color
                )}>
                  {columnTasks.length}
                </span>
              </div>

              {/* 任务列表 - 可滚动且可放置 */}
              <DroppableColumn
                id={column.status}
                tasks={columnTasks}
                onEdit={onEdit}
                onDelete={onDelete}
                onStatusChange={onStatusChange}
                projectId={projectId}
                selectedTaskIds={selectedTaskIds}
                onToggleSelect={onToggleSelect}
              />
            </div>
          );
        })}
      </div>

      {/* 拖拽时显示的覆盖层 */}
      <DragOverlay>
        {activeTask ? (
          <div className="opacity-80 rotate-3 scale-105">
            <TaskItem
              task={activeTask}
              onEdit={onEdit}
              onDelete={onDelete}
              onStatusChange={onStatusChange}
              projectId={projectId}
              isSelected={false}
            />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

// 可放置的列组件
function DroppableColumn({
  id,
  tasks,
  onEdit,
  onDelete,
  onStatusChange,
  projectId,
  selectedTaskIds,
  onToggleSelect,
}: {
  id: TaskStatus;
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  onStatusChange: (taskId: number, newStatus: string) => void;
  projectId?: number;
  selectedTaskIds?: Set<number>;
  onToggleSelect?: (task: Task, selected: boolean) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex-1 overflow-y-auto p-3 space-y-2 rounded-b-lg border-x border-b',
        'bg-muted/10',
        'scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent',
        'border-border transition-colors',
        isOver && 'bg-primary/5 border-primary/30'
      )}
    >
      {tasks.length === 0 ? (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
          {isOver ? '放在这里' : '暂无任务'}
        </div>
      ) : (
        tasks.map((task) => (
          <DraggableTask
            key={task.id}
            task={task}
            onEdit={onEdit}
            onDelete={onDelete}
            onStatusChange={onStatusChange}
            projectId={projectId}
            isSelected={selectedTaskIds?.has(task.id)}
            onToggleSelect={onToggleSelect}
          />
        ))
      )}
    </div>
  );
}

// 可拖拽的任务组件
function DraggableTask({
  task,
  onEdit,
  onDelete,
  onStatusChange,
  projectId,
  isSelected,
  onToggleSelect,
}: {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  onStatusChange: (taskId: number, newStatus: string) => void;
  projectId?: number;
  isSelected?: boolean;
  onToggleSelect?: (task: Task, selected: boolean) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.id,
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(isDragging && 'opacity-50')}
    >
      <TaskItem
        task={task}
        onEdit={onEdit}
        onDelete={onDelete}
        onStatusChange={onStatusChange}
        projectId={projectId}
        isSelected={isSelected}
        onToggleSelect={onToggleSelect}
      />
    </div>
  );
}
