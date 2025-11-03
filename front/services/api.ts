// API基础配置
const API_BASE_URL = ''; // 使用相对路径，通过Vite代理访问后端

// API响应数据类型
export interface ScreenshotData {
  id: number;
  file_path: string;
  app_name?: string;
  window_title?: string;
  created_at: string;
  text_content?: string;
  width: number;
  height: number;
}

export interface OCRResult {
  text_content: string;
  confidence: number;
  language: string;
  processing_time: number;
}

export interface ScreenshotDetail extends ScreenshotData {
  ocr_result?: OCRResult;
}

// 事件类型
export interface EventData {
  id: number;
  app_name?: string;
  window_title?: string;
  start_time: string;
  end_time?: string;
  screenshot_count: number;
  first_screenshot_id?: number;
}

export interface EventDetailData {
  id: number;
  app_name?: string;
  window_title?: string;
  start_time: string;
  end_time?: string;
  screenshots: ScreenshotData[];
}

// 语义搜索请求
export interface SemanticSearchRequest {
  query: string;
  top_k?: number;
  use_rerank?: boolean;
  retrieve_k?: number;
  filters?: Record<string, any>;
}

// 语义搜索结果
export interface SemanticSearchResult {
  text: string;
  score: number;
  metadata: Record<string, any>;
  ocr_result?: OCRResult;
  screenshot?: ScreenshotData;
}

// API客户端
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  // 获取截图列表
  async getScreenshots(params?: {
    limit?: number;
    offset?: number;
    start_date?: string;
    end_date?: string;
    app_name?: string;
  }): Promise<ScreenshotData[]> {
    const searchParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const endpoint = `/api/screenshots${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return this.request<ScreenshotData[]>(endpoint);
  }

  // 获取单个截图详情
  async getScreenshotDetail(id: number): Promise<ScreenshotDetail> {
    return this.request<ScreenshotDetail>(`/api/screenshots/${id}`);
  }

  // 获取截图图片URL
  getScreenshotImageUrl(id: number): string {
    return `${this.baseURL}/api/screenshots/${id}/image`;
  }

  // 搜索截图
  async searchScreenshots(query: string, params?: {
    start_date?: string;
    end_date?: string;
    app_name?: string;
    limit?: number;
  }): Promise<ScreenshotData[]> {
    return this.request<ScreenshotData[]>('/api/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        ...params,
      }),
    });
  }

  // 简单文本搜索（硬查询）- 使用传统搜索接口
  async simpleTextSearch(query: string, limit: number = 10): Promise<ScreenshotData[]> {
    return this.request<ScreenshotData[]>('/api/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit,
      }),
    });
  }

  // 语义搜索
  async semanticSearch(request: SemanticSearchRequest): Promise<SemanticSearchResult[]> {
    return this.request<SemanticSearchResult[]>('/api/semantic-search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // 事件列表
  async listEvents(params?: {
    limit?: number;
    offset?: number;
    start_date?: string;
    end_date?: string;
    app_name?: string;
  }): Promise<EventData[]> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value));
      });
    }
    const endpoint = `/api/events${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return this.request<EventData[]>(endpoint);
  }

  // 事件详情
  async getEventDetail(eventId: number): Promise<EventDetailData> {
    return this.request<EventDetailData>(`/api/events/${eventId}`);
  }

  // 事件简单搜索（按OCR聚合）
  async searchEvents(query: string, limit: number = 20): Promise<EventData[]> {
    return this.request<EventData[]>('/api/event-search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  // 事件语义搜索
  async semanticSearchEvents(query: string, top_k: number = 10): Promise<EventData[]> {
    return this.request<EventData[]>('/api/event-semantic-search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    });
  }

  // 健康检查
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }
}

// 导出单例
export const apiClient = new ApiClient();
export default apiClient;
