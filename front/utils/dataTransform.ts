import { ScreenshotData, SemanticSearchResult, EventData } from '../services/api';

// 前端组件数据类型
export interface ResultItem {
  id: string;
  title: string;
  subtitle?: string;
  category: string;
  icon: string;
  timeRange?: {
    start: string;
    end: string;
  };
  description?: string;
  // 新增字段用于存储原始API数据
  apiData?: ScreenshotData;
}

// 根据应用名称生成图标
function getIconForApp(appName?: string): string {
  if (!appName) return '📷';

  const lowerApp = appName.toLowerCase();

  // 常见应用图标映射
  const iconMap: { [key: string]: string } = {
    'chrome': '🌐',
    'firefox': '🦊',
    'edge': '🌐',
    'vscode': '💻',
    'visual studio code': '💻',
    'notepad': '📝',
    'notepad++': '📄',
    'word': '📄',
    'excel': '📊',
    'powerpoint': '📋',
    'onenote': '📓',
    'notion': '📋',
    'photoshop': '🎨',
    'illustrator': '🎨',
    'figma': '🎨',
    'steam': '🎮',
    'discord': '💬',
    'qq': '💬',
    'wechat': '💬',
    'explorer': '📁',
    'file': '📁',
    'music': '🎵',
    'video': '🎬',
  };

  // 查找匹配的图标
  for (const [key, icon] of Object.entries(iconMap)) {
    if (lowerApp.includes(key)) {
      return icon;
    }
  }

  return '📷'; // 默认图标
}

// 格式化时间
function formatDateTime(dateString: string): string {
  if (!dateString) {
    return '未知时间';
  }

  try {
    // 尝试解析日期
    const date = new Date(dateString);

    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      // 如果是无效日期，尝试其他格式
      const isoDate = dateString.includes('T') ? dateString : dateString + 'T00:00:00.000Z';
      const retryDate = new Date(isoDate);

      if (isNaN(retryDate.getTime())) {
        return dateString; // 返回原始字符串
      }

      return retryDate.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    }

    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    console.warn('日期格式化失败:', dateString, error);
    return dateString; // 返回原始字符串
  }
}

// 将API截图数据转换为前端结果项
export function transformScreenshotToResultItem(screenshot: ScreenshotData): ResultItem {
  const icon = getIconForApp(screenshot.app_name);
  const formattedTime = formatDateTime(screenshot.created_at);

  // 生成标题
  let title = screenshot.window_title || screenshot.app_name || '未知应用';
  if (title.length > 50) {
    title = title.substring(0, 50) + '...';
  }

  // 生成描述 - 直接使用OCR文本内容
  let description = screenshot.text_content || '无文本内容';

  return {
    id: `screenshot-${screenshot.id}`,
    title,
    subtitle: screenshot.app_name,
    category: '时光机',
    icon,
    timeRange: {
      start: formattedTime,
      end: formattedTime
    },
    description,
    apiData: screenshot
  };
}

// 批量转换截图数据
export function transformScreenshots(screenshots: ScreenshotData[]): ResultItem[] {
  return screenshots.map(transformScreenshotToResultItem);
}

// 事件 -> 结果项（以事件为粒度）
export function transformEventToResultItem(event: EventData): ResultItem {
  const icon = getIconForApp(event.app_name);
  const start = formatDateTime(event.start_time);
  const end = event.end_time ? formatDateTime(event.end_time) : start;
  const title = event.window_title || event.app_name || '事件';
  const desc = `包含 ${event.screenshot_count} 张截图`;
  return {
    id: `event-${event.id}`,
    title: title.length > 50 ? title.substring(0, 50) + '...' : title,
    subtitle: event.app_name,
    category: '时光机',
    icon,
    timeRange: { start, end },
    description: desc,
  };
}

export function transformEventsToResultItems(events: EventData[]): ResultItem[] {
  return events.map(transformEventToResultItem);
}

// 将语义搜索结果转换为前端结果项
export function transformSemanticSearchResult(searchResult: SemanticSearchResult): ResultItem {
  // 优先使用关联的截图数据，如果没有则使用元数据
  const screenshot = searchResult.screenshot;
  const metadata = searchResult.metadata;

  if (screenshot) {
    // 如果有截图数据，使用截图转换函数
    const resultItem = transformScreenshotToResultItem(screenshot);
    // 添加搜索相关信息
    // resultItem.description = `相关度: ${(searchResult.score * 100).toFixed(1)}% | ${resultItem.description}`;
    return resultItem;
  } else {
    // 如果没有截图数据，从元数据构建结果项
    const icon = getIconForApp(metadata.app_name);
    const formattedTime = metadata.created_at ? formatDateTime(metadata.created_at) : '未知时间';

    let title = metadata.window_title || metadata.app_name || '搜索结果';
    if (title.length > 50) {
      title = title.substring(0, 50) + '...';
    }

    let description = searchResult.text || '无文本内容';

    return {
      id: `search-result-${metadata.id || Math.random()}`,
      title,
      subtitle: metadata.app_name,
      category: '时光机',
      icon,
      timeRange: {
        start: formattedTime !== '未知时间' ? formattedTime : '数字记录',
        end: formattedTime !== '未知时间' ? formattedTime : '数字记录'
      },
      description,
      apiData: metadata as any
    };
  }
}

// 批量转换语义搜索结果
export function transformSemanticSearchResults(searchResults: SemanticSearchResult[]): ResultItem[] {
  return searchResults.map(transformSemanticSearchResult);
}
