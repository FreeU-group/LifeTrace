'use client';

import { useMemo, useState } from 'react';
import { Circle, CircleDot, CheckCircle2, XCircle, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { Task, TaskStatus } from '@/lib/types';
import { cn } from '@/lib/utils';
import Button from '@/components/common/Button';

interface TaskRoadMapProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
}

interface TaskNode {
  task: Task;
  level: number;
  column: number;
  children: TaskNode[];
}

const statusConfig = {
  completed: {
    icon: CheckCircle2,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
  },
  in_progress: {
    icon: CircleDot,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
  pending: {
    icon: Circle,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/30',
    borderColor: 'border-muted-foreground/20',
  },
  cancelled: {
    icon: XCircle,
    color: 'text-destructive',
    bgColor: 'bg-destructive/10',
    borderColor: 'border-destructive/30',
  },
};

const mockTasks: Task[] = [
  {
    id: 1,
    project_id: 101,
    name: "Project Setup",
    description: "Initialize repository and project structure.",
    status: 'completed' as TaskStatus,
    parent_task_id: undefined,
    created_at: "2025-01-10T09:00:00Z",
    updated_at: "2025-01-10T12:00:00Z",
  },
  {
    id: 2,
    project_id: 101,
    name: "Design Database Schema",
    description: "Define tables and relations for the core system.",
    status: 'in_progress' as TaskStatus,
    parent_task_id: 1,
    created_at: "2025-01-11T08:30:00Z",
    updated_at: "2025-01-12T15:20:00Z",
  },
  {
    id: 3,
    project_id: 101,
    name: "API Foundation",
    description: "Setup routing, controllers, and base modules.",
    status: 'pending' as TaskStatus,
    parent_task_id: 1,
    created_at: "2025-01-12T10:00:00Z",
    updated_at: "2025-01-12T10:00:00Z",
  },
  {
    id: 4,
    project_id: 101,
    name: "Auth Implementation",
    description: "Implement JWT auth and permissions.",
    status: 'pending' as TaskStatus,
    parent_task_id: 3, // depends on API Foundation
    created_at: "2025-01-13T08:00:00Z",
    updated_at: "2025-01-13T08:00:00Z",
  },
  {
    id: 5,
    project_id: 101,
    name: "Core Feature A",
    description: "Main feature development based on schema.",
    status: 'pending' as TaskStatus,
    parent_task_id: 2, // depends on DB schema
    created_at: "2025-01-14T09:00:00Z",
    updated_at: "2025-01-14T09:00:00Z",
  },
  {
    id: 6,
    project_id: 101,
    name: "Core Feature B",
    description: "Secondary core module.",
    status: 'pending' as TaskStatus,
    parent_task_id: 2, // also depends on DB schema
    created_at: "2025-01-14T09:30:00Z",
    updated_at: "2025-01-14T09:30:00Z",
  },
  {
    id: 7,
    project_id: 101,
    name: "Integration Tests",
    description: "Test interactions between modules.",
    status: 'pending' as TaskStatus,
    parent_task_id: 5, // depends on Feature A
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T10:00:00Z",
  },
  {
    id: 8,
    project_id: 101,
    name: "Deployment Setup",
    description: "Setup CI/CD pipeline.",
    status: 'pending' as TaskStatus,
    parent_task_id: 4, // depends on Auth
    created_at: "2025-01-16T11:00:00Z",
    updated_at: "2025-01-16T11:00:00Z",
  },
  {
    id: 9,
    project_id: 101,
    name: "Final QA Review",
    description: "Quality assurance before release.",
    status: 'pending' as TaskStatus,
    parent_task_id: 7, // depends on integration tests
    created_at: "2025-01-17T12:00:00Z",
    updated_at: "2025-01-17T12:00:00Z",
  },
  {
    id: 10,
    project_id: 101,
    name: "Core Feaature C",
    description: "Quality assurance before release.",
    status: 'pending' as TaskStatus,
    parent_task_id: 2, // depends on integration tests
    created_at: "2025-01-17T12:00:00Z",
    updated_at: "2025-01-17T12:00:00Z",
  },
    {
    id: 11,
    project_id: 101,
    name: "Core Feaature D",
    description: "Quality assurance before release.",
    status: 'pending' as TaskStatus,
    parent_task_id: 2, // depends on integration tests
    created_at: "2025-01-17T12:00:00Z",
    updated_at: "2025-01-17T12:00:00Z",
  },
];


export default function TaskRoadMap({ tasks, onTaskClick }: TaskRoadMapProps) {
  tasks = mockTasks;
  const [zoom, setZoom] = useState(1);
  const [hoveredTaskId, setHoveredTaskId] = useState<number | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 构建任务树结构
  const taskTree = useMemo(() => {
    const taskMap = new Map<number, Task>();
    tasks.forEach((task) => taskMap.set(task.id, task));

    // 找到根任务（没有父任务的）
    const rootTasks = tasks.filter((task) => !task.parent_task_id);

    // 递归构建树（先构建层级信息，column 会在后续布局中分配）
    const buildTree = (task: Task, level: number = 0): TaskNode => {
      const children = tasks
        .filter((t) => t.parent_task_id === task.id)
        .map((childTask) => buildTree(childTask, level + 1));

      return {
        task,
        level,
        column: 0,
        children,
      };
    };

    const roots = rootTasks.map((task) => buildTree(task, 0));

    // 分配横向列号，避免同一父节点的子任务重叠
    // 使用叶子优先的顺序为每个叶子节点分配一个递增的列号，
    // 然后将父节点列号设置为其子节点列号范围的中点。
    let nextColumn = 0;
    const assignColumns = (node: TaskNode) => {
      if (node.children.length === 0) {
        node.column = nextColumn++;
        return;
      }

      node.children.forEach(assignColumns);
      const first = node.children[0].column;
      const last = node.children[node.children.length - 1].column;
      node.column = Math.floor((first + last) / 2);
    };

    roots.forEach(assignColumns);

    return roots;
  }, [tasks]);

  // 扁平化树结构用于渲染
  const flattenTree = (nodes: TaskNode[]): TaskNode[] => {
    const result: TaskNode[] = [];
    nodes.forEach((node) => {
      result.push(node);
      if (node.children.length > 0) {
        result.push(...flattenTree(node.children));
      }
    });
    return result;
  };

  const flatTasks = flattenTree(taskTree);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.2, 2));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.2, 0.5));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // 鼠标滚轮缩放
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = -e.deltaY * 0.001;
    setZoom((prev) => Math.min(Math.max(prev + delta, 0.5), 2));
  };

  // 鼠标拖拽平移
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) { // 左键
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
  };

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-muted-foreground">暂无任务数据</p>
      </div>
    );
  }

  return (
    <div 
      className="w-full h-full overflow-hidden p-8 relative"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
    >
      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 z-10 flex gap-2 bg-card border border-border rounded-lg p-2 shadow-lg">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          disabled={zoom <= 0.5}
          className="h-8 w-8 p-0"
          title="缩小"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleResetZoom}
          className="h-8 px-3 text-xs"
          title="重置缩放"
        >
          {Math.round(zoom * 100)}%
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          disabled={zoom >= 2}
          className="h-8 w-8 p-0"
          title="放大"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <div className="w-px bg-border" />
        <Button
          variant="ghost"
          size="sm"
          onClick={handleResetZoom}
          className="h-8 w-8 p-0"
          title="适应屏幕"
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>

      <div 
        className="min-w-max" 
        style={{ 
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, 
          transformOrigin: 'top left',
          transition: isDragging ? 'none' : 'transform 0.2s ease-out',
          pointerEvents: isDragging ? 'none' : 'auto',
        }}
      >

        {/* 路线图 */}
        <div className="relative">
          {flatTasks.map((node) => {
            const config = statusConfig[node.task.status as TaskStatus];
            const Icon = config.icon;

            // 计算位置 - 垂直布局
            const top = node.level * 300; // 垂直层级间距
            const left = node.column * 360; // 水平列间距

            // 查找子任务用于绘制连接线
            const hasChildren = node.children.length > 0;
            const childIndices = node.children.map((child) =>
              flatTasks.findIndex((n) => n.task.id === child.task.id)
            );

            return (
              <div key={node.task.id}>
            {/* 连接线 */}
                {hasChildren &&
                  childIndices.map((childIndex) => {
                    const childNode = flatTasks[childIndex];
                    const childTop = childNode.level * 300;
                    const childLeft = childNode.column * 360;

                    // Calculate node dimensions (base width is 256px = w-64)
                    const nodeWidth = 256;
                    const nodeHeight = 50; // Approximate height for non-hovered state

                    const parentCenterX = left + nodeWidth / 2;
                    const parentBottomY = top + nodeHeight;
                    const childCenterX = childLeft + nodeWidth / 2;
                    const childTopY = childTop;

                    // Calculate SVG container bounds
                    const svgLeft = Math.min(parentCenterX, childCenterX);
                    const svgTop = parentBottomY;
                    const svgWidth = Math.max(Math.abs(childCenterX - parentCenterX), 1);
                    const svgHeight = childTopY - parentBottomY;

                    // Calculate relative coordinates within SVG
                    const startX = parentCenterX - svgLeft;
                    const startY = 0;
                    const endX = childCenterX - svgLeft;
                    const endY = svgHeight;
                    const midY = svgHeight / 2;

                    return (
                      <svg
                        key={`line-${node.task.id}-${childNode.task.id}`}
                        className="absolute pointer-events-none"
                        style={{
                          left: svgLeft,
                          top: svgTop,
                          width: svgWidth,
                          height: svgHeight,
                          overflow: 'visible',
                        }}
                      >
                        <path
                          d={`M ${startX} ${startY} L ${startX} ${midY} L ${endX} ${midY} L ${endX} ${endY}`}
                          stroke="currentColor"
                          strokeWidth="2"
                          fill="none"
                          className="text-border"
                        />
                      </svg>
                    );
                  })}

                {/* 任务节点 */}
                <div
                  className="absolute transition-all duration-200"
                  style={{ 
                    top: `${top}px`, 
                    left: `${left}px`,
                    zIndex: hoveredTaskId === node.task.id ? 50 : 1,
                    cursor: 'pointer',
                  }}
                  onMouseEnter={() => setHoveredTaskId(node.task.id)}
                  onMouseLeave={() => setHoveredTaskId(null)}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <div
                    onClick={() => onTaskClick?.(node.task)}
                    className={cn(
                      'rounded-lg border-2 bg-card cursor-pointer transition-all duration-200',
                      config.borderColor,
                      config.bgColor,
                      hoveredTaskId === node.task.id
                        ? 'w-80 p-4 shadow-2xl scale-110'
                        : 'w-64 p-3 shadow-sm hover:shadow-md'
                    )}
                  >
                    {/* 任务名称 - 始终显示 */}
                    <div className="flex items-center gap-2">
                      <Icon className={cn('h-4 w-4 shrink-0', config.color)} />
                      <h4 className={cn(
                        'font-semibold text-foreground transition-colors flex-1',
                        hoveredTaskId === node.task.id ? 'text-primary' : '',
                        hoveredTaskId === node.task.id ? 'line-clamp-2' : 'line-clamp-1 text-sm'
                      )}>
                        {node.task.name}
                      </h4>
                    </div>

                    {/* 详细信息 - 仅悬停时显示 */}
                    {hoveredTaskId === node.task.id && (
                      <div className="mt-3 space-y-2 animate-in fade-in duration-200">
                        {/* 状态 */}
                        <div className="flex items-center gap-2 pb-2 border-b border-border">
                          <span className={cn('text-xs font-medium', config.color)}>
                            {node.task.status === 'completed'
                              ? '已完成'
                              : node.task.status === 'in_progress'
                              ? '进行中'
                              : node.task.status === 'pending'
                              ? '待办'
                              : '已取消'}
                          </span>
                        </div>

                        {/* 任务描述 */}
                        {node.task.description && (
                          <p className="text-xs text-muted-foreground line-clamp-3">
                            {node.task.description}
                          </p>
                        )}

                        {/* 子任务数量 */}
                        {node.children.length > 0 && (
                          <div className="pt-2 border-t border-border">
                            <span className="text-xs text-muted-foreground">
                              {node.children.length} 个依赖任务
                            </span>
                          </div>
                        )}

                        {/* 时间信息 */}
                        <div className="pt-2 border-t border-border text-xs text-muted-foreground">
                          <div>创建: {new Date(node.task.created_at).toLocaleDateString('zh-CN')}</div>
                          <div>更新: {new Date(node.task.updated_at).toLocaleDateString('zh-CN')}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}