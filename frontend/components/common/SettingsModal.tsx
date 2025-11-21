'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import Input from './Input';
import Button from './Button';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ConfigSettings {
  llmKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  recordEnabled: boolean;
  recordInterval: number;
  blacklistEnabled: boolean;
  blacklistApps: string[];
  chatContextEnabled: boolean;
  chatContextRounds: number;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [settings, setSettings] = useState<ConfigSettings>({
    llmKey: '',
    baseUrl: '',
    model: 'qwen3-max',
    temperature: 0.7,
    maxTokens: 2048,
    recordEnabled: true,
    recordInterval: 5,
    blacklistEnabled: false,
    blacklistApps: [],
    chatContextEnabled: true,
    chatContextRounds: 3,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showScheduler, setShowScheduler] = useState(false);
  const [initialShowScheduler, setInitialShowScheduler] = useState(false); // 记录初始值
  const [showCostTracking, setShowCostTracking] = useState(false);
  const [initialShowCostTracking, setInitialShowCostTracking] = useState(false); // 记录初始值
  const [showProjectManagement, setShowProjectManagement] = useState(false);
  const [initialShowProjectManagement, setInitialShowProjectManagement] = useState(false); // 记录初始值
  const [blacklistInput, setBlacklistInput] = useState(''); // 黑名单输入框的值
  const [initialLlmConfig, setInitialLlmConfig] = useState<{ llmKey: string; baseUrl: string; model: string }>({
    llmKey: '',
    baseUrl: '',
    model: 'qwen3-max',
  }); // 记录初始 LLM 配置

  // 加载配置
  useEffect(() => {
    if (isOpen) {
      loadConfig();
      // 从 localStorage 读取定时任务显示设置
      const savedScheduler = localStorage.getItem('showScheduler');
      const savedSchedulerValue = savedScheduler === 'true';
      setShowScheduler(savedSchedulerValue);
      setInitialShowScheduler(savedSchedulerValue); // 记录初始值

      // 从 localStorage 读取费用统计显示设置
      const savedCostTracking = localStorage.getItem('showCostTracking');
      const savedCostTrackingValue = savedCostTracking === 'true';
      setShowCostTracking(savedCostTrackingValue);
      setInitialShowCostTracking(savedCostTrackingValue); // 记录初始值

      // 从 localStorage 读取项目管理显示设置
      const savedProjectManagement = localStorage.getItem('showProjectManagement');
      const savedProjectManagementValue = savedProjectManagement === 'true';
      setShowProjectManagement(savedProjectManagementValue);
      setInitialShowProjectManagement(savedProjectManagementValue); // 记录初始值
    }
  }, [isOpen]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await api.getConfig();
      if (response.data.success) {
        const config = response.data.config;
        // 处理黑名单应用列表
        const apps = config.blacklistApps || [];
        const blacklistAppsArray = Array.isArray(apps) ? apps : (typeof apps === 'string' ? apps.split(',').map((s: string) => s.trim()).filter((s: string) => s) : []);

        const newSettings = {
          llmKey: config.llmKey || '',
          baseUrl: config.baseUrl || '',
          model: config.model || 'qwen3-max',
          temperature: config.temperature || 0.7,
          maxTokens: config.maxTokens || 2048,
          recordEnabled: config.recordingEnabled ?? config.recordEnabled ?? config.record?.enabled ?? true,
          recordInterval: config.recordInterval || 5,
          blacklistEnabled: config.blacklistEnabled ?? false,
          blacklistApps: blacklistAppsArray,
          chatContextEnabled: config.chatContextEnabled ?? true,
          chatContextRounds: config.chatContextRounds || 3,
        };

        setSettings(newSettings);

        // 记录初始 LLM 配置
        setInitialLlmConfig({
          llmKey: newSettings.llmKey,
          baseUrl: newSettings.baseUrl,
          model: newSettings.model,
        });
      }
    } catch (error) {
      console.error('加载配置失败:', error);
      const errorMsg = error instanceof Error ? error.message : undefined;
      toast.configLoadFailed(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!settings.llmKey || !settings.baseUrl) {
      setMessage({ type: 'error', text: '请先填写 API Key 和 Base URL' });
      return;
    }

    setTesting(true);
    setMessage(null);
    try {
      const response = await api.testLlmConfig({
        llmKey: settings.llmKey,
        baseUrl: settings.baseUrl,
        model: settings.model,
      });

      if (response.data.success) {
        setMessage({ type: 'success', text: '✓ API 配置验证成功！' });
      } else {
        setMessage({
          type: 'error',
          text: `✗ API 配置验证失败: ${response.data.error || '未知错误'}`
        });
      }
    } catch (error) {
      console.error('测试配置失败:', error);
      const errorMsg = error instanceof Error ? error.message : '网络连接失败';
      setMessage({ type: 'error', text: `✗ 测试失败: ${errorMsg}` });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      // 检查是否有 LLM 配置
      const hasLlmConfig = settings.llmKey && settings.baseUrl;

      // 检查 LLM 配置是否发生变化
      const llmConfigChanged = hasLlmConfig && (
        settings.llmKey !== initialLlmConfig.llmKey ||
        settings.baseUrl !== initialLlmConfig.baseUrl ||
        settings.model !== initialLlmConfig.model
      );

      let response;
      if (hasLlmConfig) {
        // 如果有 LLM 配置，使用 save-and-init-llm 接口
        // 该接口会保存配置并重新初始化 LLM 客户端
        response = await api.saveAndInitLlm({
          llmKey: settings.llmKey,
          baseUrl: settings.baseUrl,
          model: settings.model,
        });

        // 同时保存其他配置
        await api.saveConfig({
          temperature: settings.temperature,
          maxTokens: settings.maxTokens,
          recordEnabled: settings.recordEnabled,
          recordInterval: settings.recordInterval,
          blacklistEnabled: settings.blacklistEnabled,
          blacklistApps: settings.blacklistApps,
          chatContextEnabled: settings.chatContextEnabled,
          chatContextRounds: settings.chatContextRounds,
        });
      } else {
        // 如果没有 LLM 配置，使用普通的保存接口
        response = await api.saveConfig(settings);
      }

      if (response.data.success) {
        // 保存定时任务显示设置
        const schedulerChanged = showScheduler !== initialShowScheduler;
        if (schedulerChanged) {
          localStorage.setItem('showScheduler', String(showScheduler));
          setInitialShowScheduler(showScheduler); // 更新初始值

          // 触发自定义事件通知其他组件
          const currentPath = window.location.pathname;
          window.dispatchEvent(new CustomEvent('schedulerVisibilityChange', {
            detail: {
              visible: showScheduler,
              currentPath: currentPath
            }
          }));
        }

        // 保存费用统计显示设置
        const costTrackingChanged = showCostTracking !== initialShowCostTracking;
        if (costTrackingChanged) {
          localStorage.setItem('showCostTracking', String(showCostTracking));
          setInitialShowCostTracking(showCostTracking); // 更新初始值

          // 触发自定义事件通知其他组件
          const currentPath = window.location.pathname;
          window.dispatchEvent(new CustomEvent('costTrackingVisibilityChange', {
            detail: {
              visible: showCostTracking,
              currentPath: currentPath
            }
          }));
        }

        // 保存项目管理显示设置
        const projectManagementChanged = showProjectManagement !== initialShowProjectManagement;
        if (projectManagementChanged) {
          localStorage.setItem('showProjectManagement', String(showProjectManagement));
          setInitialShowProjectManagement(showProjectManagement); // 更新初始值

          // 触发自定义事件通知其他组件
          const currentPath = window.location.pathname;
          window.dispatchEvent(new CustomEvent('projectManagementVisibilityChange', {
            detail: {
              visible: showProjectManagement,
              currentPath: currentPath
            }
          }));
        }

        toast.configSaved();
        onClose(); // 立即关闭弹窗

        // 只有在 LLM 配置实际发生变化时才刷新页面
        if (llmConfigChanged) {
          setTimeout(() => {
            window.location.reload();
          }, 500); // 延迟 500ms 以确保 toast 消息能显示
        }
      } else {
        // 如果返回了错误信息
        setMessage({
          type: 'error',
          text: response.data.error || '保存失败'
        });
      }
    } catch (error) {
      console.error('保存配置失败:', error);
      const errorMsg = error instanceof Error ? error.message : undefined;
      toast.configSaveFailed(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key: keyof ConfigSettings, value: string | number | string[] | boolean) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  // 添加黑名单应用
  const handleAddBlacklistApp = (app: string) => {
    const trimmedApp = app.trim();
    if (trimmedApp && !settings.blacklistApps.includes(trimmedApp)) {
      setSettings((prev) => ({
        ...prev,
        blacklistApps: [...prev.blacklistApps, trimmedApp]
      }));
    }
  };

  // 移除黑名单应用
  const handleRemoveBlacklistApp = (app: string) => {
    setSettings((prev) => ({
      ...prev,
      blacklistApps: prev.blacklistApps.filter(a => a !== app)
    }));
  };

  // 处理黑名单输入框的键盘事件
  const handleBlacklistKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && blacklistInput.trim()) {
      e.preventDefault();
      handleAddBlacklistApp(blacklistInput);
      setBlacklistInput('');
    } else if (e.key === 'Backspace' && !blacklistInput && settings.blacklistApps.length > 0) {
      // 如果输入框为空且按下 Backspace，删除最后一个标签
      const lastApp = settings.blacklistApps[settings.blacklistApps.length - 1];
      handleRemoveBlacklistApp(lastApp);
    }
  };

  // 处理定时任务显示开关（仅更新状态，不立即保存）
  const handleSchedulerToggle = (checked: boolean) => {
    setShowScheduler(checked);
  };

  // 处理费用统计显示开关（仅更新状态，不立即保存）
  const handleCostTrackingToggle = (checked: boolean) => {
    setShowCostTracking(checked);
  };

  // 处理项目管理显示开关（仅更新状态，不立即保存）
  const handleProjectManagementToggle = (checked: boolean) => {
    setShowProjectManagement(checked);
  };

  // 处理取消操作
  const handleCancel = () => {
    // 恢复定时任务开关到初始状态
    setShowScheduler(initialShowScheduler);
    // 恢复费用统计开关到初始状态
    setShowCostTracking(initialShowCostTracking);
    // 恢复项目管理开关到初始状态
    setShowProjectManagement(initialShowProjectManagement);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[300] flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg bg-background shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between border-b bg-background px-4 py-3">
          <h2 className="text-lg font-bold text-foreground">设置</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-foreground transition-colors hover:bg-muted"
            aria-label="关闭"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* 消息提示 */}
          {message && (
            <div
              className={`rounded-lg px-3 py-2 text-sm font-medium ${
                message.type === 'success'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
              }`}
            >
              {message.text}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">加载配置中...</div>
            </div>
          ) : (
            <>
              {/* LLM 配置 */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">LLM 配置</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-foreground">
                        API Key <span className="text-red-500">*</span>
                      </label>
                      <Input
                        type="password"
                        className="px-3 py-2 h-9"
                        placeholder="输入您的 API Key"
                        value={settings.llmKey}
                        onChange={(e) => handleChange('llmKey', e.target.value)}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        如何获取 API Key？请访问{' '}
                        <a
                          href="https://bailian.console.aliyun.com/?tab=api#/api"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          阿里云百炼控制台
                        </a>
                      </p>
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-foreground">
                        Base URL <span className="text-red-500">*</span>
                      </label>
                      <Input
                        type="text"
                        className="px-3 py-2 h-9"
                        placeholder="https://api.example.com/v1"
                        value={settings.baseUrl}
                        onChange={(e) => handleChange('baseUrl', e.target.value)}
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="col-span-1">
                        <label className="mb-1 block text-sm font-medium text-foreground">
                          模型
                        </label>
                        <Input
                          type="text"
                          className="px-3 py-2 h-9"
                          placeholder="qwen3-max"
                          value={settings.model}
                          onChange={(e) => handleChange('model', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium text-foreground">
                          Temperature
                        </label>
                        <Input
                          type="number"
                          step="0.1"
                          min="0"
                          max="2"
                          className="px-3 py-2 h-9"
                          value={settings.temperature}
                          onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium text-foreground">
                          Max Tokens
                        </label>
                        <Input
                          type="number"
                          className="px-3 py-2 h-9"
                          value={settings.maxTokens}
                          onChange={(e) => handleChange('maxTokens', parseInt(e.target.value))}
                        />
                      </div>
                    </div>

                    {/* 测试按钮 */}
                    <div className="pt-1">
                      <Button
                        variant="outline"
                        onClick={handleTest}
                        disabled={testing || !settings.llmKey || !settings.baseUrl}
                        className="w-full h-9"
                      >
                        {testing ? '测试中...' : '测试 API 连接'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 基础设置 */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">基础设置</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          启用录制
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          开启屏幕录制和截图功能
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={settings.recordEnabled}
                          onChange={(e) => handleChange('recordEnabled', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                    </div>

                    {settings.recordEnabled && (
                      <div className="space-y-3">
                        <div>
                          <label className="mb-1 block text-sm font-medium text-foreground">
                            截图间隔（秒）
                          </label>
                          <Input
                            type="number"
                            className="px-3 py-2 h-9"
                            value={settings.recordInterval}
                            onChange={(e) => handleChange('recordInterval', parseInt(e.target.value))}
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-foreground">
                              启用黑名单
                            </p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              开启后可以设置不需要截图的应用
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={settings.blacklistEnabled}
                              onChange={(e) => handleChange('blacklistEnabled', e.target.checked)}
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                          </label>
                        </div>
                        {settings.blacklistEnabled && (
                          <div>
                            <label className="mb-1 block text-sm font-medium text-foreground">
                              应用黑名单
                            </label>
                            <div className="border border-input rounded-md px-2 py-1.5 min-h-[38px] flex flex-wrap gap-1.5 items-center bg-background focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all">
                              {settings.blacklistApps.map((app) => (
                                <span
                                  key={app}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 text-sm bg-primary/10 text-primary rounded-md border border-primary/20"
                                >
                                  {app}
                                  <button
                                    type="button"
                                    onClick={() => handleRemoveBlacklistApp(app)}
                                    className="hover:bg-primary/20 rounded-full p-0.5 transition-colors"
                                    aria-label={`删除 ${app}`}
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </span>
                              ))}
                              <input
                                type="text"
                                className="flex-1 min-w-[120px] outline-none bg-transparent text-sm placeholder:text-muted-foreground px-1"
                                placeholder={settings.blacklistApps.length === 0 ? "输入应用名称后按回车添加" : "继续添加..."}
                                value={blacklistInput}
                                onChange={(e) => setBlacklistInput(e.target.value)}
                                onKeyDown={handleBlacklistKeyDown}
                              />
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              这些应用的窗口将不会被截图记录，输入应用名称后按回车添加（例如：微信、QQ、钉钉）
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* 对话设置 */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">对话设置</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          启用上下文
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          开启后发送消息时附带历史上下文
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={settings.chatContextEnabled}
                          onChange={(e) => handleChange('chatContextEnabled', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                    </div>

                    {settings.chatContextEnabled && (
                      <div>
                        <label className="mb-1 block text-sm font-medium text-foreground">
                          上下文轮次
                        </label>
                        <Input
                          type="number"
                          min="1"
                          max="20"
                          className="px-3 py-2 h-9"
                          value={settings.chatContextRounds}
                          onChange={(e) => {
                            const value = parseInt(e.target.value);
                            if (value >= 1 && value <= 20) {
                              handleChange('chatContextRounds', value);
                            }
                          }}
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                          附带最近 {settings.chatContextRounds} 轮历史对话作为上下文（最多 20 轮）
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* 开发者选项 */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">开发者选项</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        显示定时任务
                      </label>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        开启后在侧边栏显示定时任务菜单
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={showScheduler}
                        onChange={(e) => handleSchedulerToggle(e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        显示费用统计
                      </label>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        开启后在侧边栏显示 LLM 费用统计菜单
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={showCostTracking}
                        onChange={(e) => handleCostTrackingToggle(e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        显示项目管理
                      </label>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        开启后在侧边栏显示项目管理菜单
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={showProjectManagement}
                        onChange={(e) => handleProjectManagementToggle(e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                </CardContent>
              </Card>

              {/* 操作按钮 */}
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={handleCancel} disabled={saving} className="h-9">
                  取消
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="h-9"
                >
                  {saving ? '保存中...' : '保存'}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
