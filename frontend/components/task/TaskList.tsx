'use client';

import { Task } from '@/lib/types';
import TaskItem from './TaskItem';
import { cn } from '@/lib/utils';

interface TaskListProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  onStatusChange: (taskId: number, newStatus: string) => void;
  projectId?: number;
  selectedTaskIds?: Set<number>;
  onToggleSelect?: (task: Task, selected: boolean) => void;
  className?: string;
}

export default function TaskList({
  tasks,
  onEdit,
  onDelete,
  onStatusChange,
  projectId,
  selectedTaskIds,
  onToggleSelect,
  className,
}: TaskListProps) {
  return (
    <div className={cn('space-y-3', className)}>
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onEdit={onEdit}
          onDelete={onDelete}
          onStatusChange={onStatusChange}
          projectId={projectId}
          isSelected={selectedTaskIds?.has(task.id)}
          onToggleSelect={onToggleSelect}
        />
      ))}
    </div>
  );
}
