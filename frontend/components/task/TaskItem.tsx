'use client';

import { useRouter } from 'next/navigation';
import { Task, TaskStatus } from '@/lib/types';
import {
  Edit2,
  Trash2,
  Circle,
  CircleDot,
  CheckCircle2,
  XCircle,
  Clock,
  Square,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface TaskItemProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  onStatusChange: (taskId: number, newStatus: string) => void;
  projectId?: number;
  isSelected?: boolean;
  onToggleSelect?: (task: Task, selected: boolean) => void;
}

const statusConfig = {
  pending: {
    label: '待办',
    icon: Circle,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/50',
    borderColor: 'border-muted-foreground/20',
  },
  in_progress: {
    label: '进行中',
    icon: CircleDot,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
  completed: {
    label: '已完成',
    icon: CheckCircle2,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
  },
  cancelled: {
    label: '已取消',
    icon: XCircle,
    color: 'text-destructive',
    bgColor: 'bg-destructive/10',
    borderColor: 'border-destructive/30',
  },
};

export default function TaskItem({
  task,
  onEdit,
  onDelete,
  onStatusChange,
  projectId,
  isSelected = false,
  onToggleSelect,
}: TaskItemProps) {
  const router = useRouter();
  const config = statusConfig[task.status as TaskStatus];
  const StatusIcon = config.icon;

  const handleTaskClick = () => {
    if (projectId) {
      router.push(`/project-management/${projectId}/tasks/${task.id}`);
    }
  };

  // 格式化时间
  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return '已逾期';
    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '明天';
    if (diffDays <= 7) return `${diffDays}天后`;
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <div>
      {/* 任务卡片 - 符合 shadcn 标准 */}
      <div
        className={cn(
          'group relative rounded-lg border bg-card text-card-foreground shadow-sm transition-all duration-200',
          projectId && 'cursor-pointer',
          isSelected && [
            'border-primary ring-2 ring-primary/20',
            'shadow-md',
          ],
          !isSelected && 'border-border hover:border-primary/50 hover:shadow-md'
        )}
      >
        {/* 主内容区 */}
        <div className="p-3">
          {/* 顶部：标题和状态/选择框 */}
          <div className="flex items-start gap-2 mb-2">
            {/* 状态指示器/复选框 - 悬停时变为复选框 */}
            <button
              className={cn(
                'flex-shrink-0 hover:bg-accent rounded transition-all p-0.5 -ml-0.5',
                onToggleSelect && 'cursor-pointer',
                !onToggleSelect && 'cursor-default'
              )}
              onClick={(e) => {
                e.stopPropagation();
                if (onToggleSelect) {
                  onToggleSelect(task, !isSelected);
                }
              }}
              aria-label={isSelected ? '取消选择' : '选择'}
            >
              {/* 已选中时始终显示勾选图标 */}
              {isSelected ? (
                <Check className="h-4 w-4 text-primary" />
              ) : (
                <>
                  {/* 未悬停时显示状态图标 */}
                  <StatusIcon className={cn('h-4 w-4', config.color, onToggleSelect && 'group-hover:hidden')} />
                  {/* 悬停时显示复选框（仅在支持选择时） */}
                  {onToggleSelect && (
                    <Square className="h-4 w-4 text-primary/60 transition-colors hidden group-hover:block" />
                  )}
                </>
              )}
            </button>

            {/* 任务标题 */}
            <h3
              className={cn(
                'font-medium text-sm leading-snug transition-colors flex-1 text-foreground',
                projectId && 'group-hover:text-primary'
              )}
              onClick={handleTaskClick}
            >
              {task.name}
            </h3>
          </div>

          {/* 任务描述 */}
          {task.description && (
            <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed mb-2" onClick={handleTaskClick}>
              {task.description}
            </p>
          )}

          {/* 底部元信息 */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {/* 时间信息 */}
              {task.created_at && (
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>{formatDate(task.created_at)}</span>
                </div>
              )}
            </div>

            {/* 操作按钮组 - 悬停时显示 */}
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => onEdit(task)}
                className={cn(
                  'inline-flex items-center justify-center rounded-md',
                  'h-6 w-6',
                  'hover:bg-accent transition-colors'
                )}
                title="编辑任务"
              >
                <Edit2 className="h-3 w-3 text-muted-foreground" />
              </button>
              <button
                onClick={() => onDelete(task.id)}
                className={cn(
                  'inline-flex items-center justify-center rounded-md',
                  'h-6 w-6',
                  'hover:bg-destructive/10 transition-colors'
                )}
                title="删除任务"
              >
                <Trash2 className="h-3 w-3 text-destructive" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
