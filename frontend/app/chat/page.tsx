'use client';

import { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import { Send, Trash2, Plus, User, Bot, X } from 'lucide-react';
import { ChatMessage, Conversation } from '@/lib/types';
import { api, API_BASE_URL } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { useSelectedEvents } from '@/lib/context/SelectedEventsContext';

export default function ChatPage() {
  const { selectedEventsData, setSelectedEventsData } = useSelectedEvents();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [useRAG, setUseRAG] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 加载会话列表
  const loadConversations = async () => {
    try {
      const response = await api.getConversations();
      setConversations(response.data);
    } catch (error) {
      console.error('加载会话列表失败:', error);
    }
  };

  // 发送消息（支持事件上下文和流式响应）
  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setLoading(true);

    try {
      // 调试日志
      console.log('发送消息，选中的事件数量:', selectedEventsData.length);
      console.log('选中的事件数据:', selectedEventsData);

      // 如果有选中的事件，使用流式接口并附带上下文
      if (selectedEventsData.length > 0) {
        const eventContext = selectedEventsData.map((event) => ({
          event_id: event.id,
          text: event.ai_summary || event.summary || '',
        }));

        console.log('构建的事件上下文:', eventContext);
        console.log('请求URL:', `${API_BASE_URL}/api/chat/stream-with-context`);

        // 使用流式接口
        const response = await fetch(`${API_BASE_URL}/api/chat/stream-with-context`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: currentInput,
            event_context: eventContext,
          }),
        });

        if (!response.ok) {
          throw new Error('请求失败');
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let assistantContent = '';

        // 创建助手消息占位
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // 读取流式响应
        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            assistantContent += chunk;

            // 更新消息内容
            setMessages((prev) => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = {
                ...newMessages[newMessages.length - 1],
                content: assistantContent,
              };
              return newMessages;
            });
          }
        }
      } else {
        // 没有选中事件，使用普通接口
        const response = await api.sendChatMessage({
          message: currentInput,
          conversation_id: currentConversationId || undefined,
          use_rag: useRAG,
        });

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.data.response || response.data.message,
          timestamp: new Date().toISOString(),
          sources: response.data.sources,
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // 更新当前会话ID
        if (response.data.conversation_id) {
          setCurrentConversationId(response.data.conversation_id);
        }

        // 重新加载会话列表
        loadConversations();
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '抱歉，发送消息失败，请重试。',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // 新建会话
  const createNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  // 删除会话
  const deleteConversation = async (id: string) => {
    try {
      await api.deleteConversation(id);
      if (currentConversationId === id) {
        createNewConversation();
      }
      loadConversations();
    } catch (error) {
      console.error('删除会话失败:', error);
    }
  };

  // 加载会话消息
  const loadConversation = (conversation: Conversation) => {
    setCurrentConversationId(conversation.id);
    setMessages(conversation.messages || []);
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 调试：监控选中的事件变化
  useEffect(() => {
    console.log('选中的事件数据已更新:', selectedEventsData);
  }, [selectedEventsData]);

  return (
    <div className="container mx-auto h-[calc(100vh-4rem)] px-4 py-4">
      <div className="flex h-full gap-4">
        {/* 左侧区域 - 占2/3 */}
        <div className="flex w-2/3 gap-4">
          {/* 会话列表 */}
          <Card className="w-64 flex-shrink-0">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">会话历史</CardTitle>
                <Button variant="ghost" size="sm" onClick={createNewConversation}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group flex items-center justify-between rounded-lg p-2 hover:bg-muted/50 ${
                      currentConversationId === conv.id ? 'bg-muted' : ''
                    }`}
                  >
                    <button
                      className="flex-1 truncate text-left text-sm font-medium text-foreground"
                      onClick={() => loadConversation(conv)}
                    >
                      {conv.title || '新会话'}
                    </button>
                    <button
                      className="opacity-0 transition-opacity group-hover:opacity-100"
                      onClick={() => deleteConversation(conv.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 中间内容区域 - 显示选中的事件 */}
          <Card className="flex flex-1 flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>
                  事件上下文
                  {selectedEventsData.length > 0 && (
                    <span className="ml-2 text-sm text-muted-foreground">
                      ({selectedEventsData.length} 个事件)
                    </span>
                  )}
                </CardTitle>
                {selectedEventsData.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedEventsData([])}
                  >
                    清空
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col overflow-y-auto">
              {selectedEventsData.length === 0 ? (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <p className="text-lg font-semibold">未选择事件</p>
                    <p className="mt-2 text-sm font-medium">
                      从事件页面选择事件作为对话上下文
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedEventsData.map((event) => (
                    <div
                      key={event.id}
                      className="group relative rounded-lg border-2 border-primary/50 bg-card p-3 hover:bg-primary/5 hover:border-primary transition-all shadow-sm"
                    >
                      <button
                        onClick={() => {
                          setSelectedEventsData((prev) =>
                            prev.filter((e) => e.id !== event.id)
                          );
                        }}
                        className="absolute right-2 top-2 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-destructive/10 rounded p-1"
                      >
                        <X className="h-4 w-4 text-primary/60 hover:text-destructive" />
                      </button>

                      <div className="mb-2 flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold text-primary">
                          📌 事件 #{event.id}
                        </span>
                        {event.app_name && (
                          <span className="rounded bg-primary/10 border border-primary/30 px-2 py-0.5 text-xs text-primary font-medium">
                            {event.app_name}
                          </span>
                        )}
                        <span className="rounded bg-primary/10 border border-primary/30 px-2 py-0.5 text-xs text-primary/70 font-medium">
                          🖼️ {event.screenshot_count || 0}张
                        </span>
                      </div>

                      <p className="text-sm text-primary line-clamp-3 font-semibold">
                        {event.ai_summary || event.summary || '无摘要'}
                      </p>

                      <p className="mt-2 text-xs text-primary/70">
                        {new Date(event.start_time).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 右侧聊天区域 - 占1/3 */}
        <Card className="flex w-1/3 flex-col">
          <CardContent className="flex flex-1 flex-col pt-6">
            {/* 消息列表 */}
            <div className="flex-1 space-y-3 overflow-y-auto pb-4">
              {messages.length === 0 ? (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <p className="text-sm font-semibold">欢迎使用助手</p>
                    <p className="mt-2 text-xs font-medium">
                      询问关于截图的问题
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex gap-2 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {/* 机器人头像 - 靠左 */}
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-white flex items-center justify-center shadow-sm border border-border">
                        <Bot className="w-4 h-4 text-gray-700" />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-foreground'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <div
                          className="prose prose-sm max-w-none text-xs"
                          dangerouslySetInnerHTML={{
                            __html: marked(message.content),
                          }}
                        />
                      ) : (
                        <p className="whitespace-pre-wrap text-xs">{message.content}</p>
                      )}

                      {/* 来源信息 */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-2 border-t border-border pt-2 text-xs">
                          <p className="font-medium text-xs">相关截图:</p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {message.sources.slice(0, 2).map((source, i: number) => (
                              <span
                                key={i}
                                className="rounded bg-background px-1.5 py-0.5 text-[10px] text-foreground dark:bg-card"
                              >
                                {(source as { app_name?: string }).app_name || '未知应用'}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 用户头像 - 靠右 */}
                    {message.role === 'user' && (
                      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-white flex items-center justify-center shadow-sm border border-border">
                        <User className="w-4 h-4 text-gray-700" />
                      </div>
                    )}
                  </div>
                ))
              )}

              {loading && <Loading text="正在思考..." size="sm" />}

              <div ref={messagesEndRef} />
            </div>

            {/* 输入框 */}
            <div className="border-t border-border pt-4">
              {selectedEventsData.length > 0 && (
                <div className="mb-2 rounded-md bg-primary/10 px-3 py-2 text-xs text-primary">
                  <span className="font-semibold">
                    📌 已选择 {selectedEventsData.length} 个事件作为上下文
                  </span>
                  <span className="ml-2 text-muted-foreground">
                    (将使用流式响应)
                  </span>
                </div>
              )}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder={
                    selectedEventsData.length > 0
                      ? '基于选中的事件提问...'
                      : '输入消息...'
                  }
                  className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
                  disabled={loading}
                />
                <Button onClick={sendMessage} disabled={loading || !inputMessage.trim()} size="sm">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
