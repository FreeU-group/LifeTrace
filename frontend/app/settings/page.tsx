'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';
import Input from '@/components/common/Input';

export default function SettingsPage() {
  const [showScheduler, setShowScheduler] = useState(false);

  // 从 localStorage 读取设置
  useEffect(() => {
    const saved = localStorage.getItem('showScheduler');
    if (saved !== null) {
      setShowScheduler(saved === 'true');
    }
  }, []);

  // 保存设置到 localStorage 并触发自定义事件
  const handleSchedulerToggle = (checked: boolean) => {
    setShowScheduler(checked);
    localStorage.setItem('showScheduler', String(checked));
    // 触发自定义事件通知其他组件
    window.dispatchEvent(new CustomEvent('schedulerVisibilityChange', { detail: { visible: checked } }));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold text-foreground">设置</h1>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>基本设置</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-semibold text-foreground">
                  截图间隔（秒）
                </label>
                <Input
                  type="number"
                  className="px-4 py-2"
                  defaultValue={5}
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-foreground">
                  OCR 语言
                </label>
                <select className="w-full rounded-lg border border-input bg-background px-4 py-2 text-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20">
                  <option value="zh-cn">中文</option>
                  <option value="en">英文</option>
                  <option value="mixed">中英混合</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI 设置</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-semibold text-foreground">
                  API Key
                </label>
                <Input
                  type="password"
                  className="px-4 py-2"
                  placeholder="输入您的 API Key"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-foreground">
                  模型选择
                </label>
                <select className="w-full rounded-lg border border-input bg-background px-4 py-2 text-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20">
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5">GPT-3.5</option>
                  <option value="claude">Claude</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>存储设置</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-semibold text-foreground">
                  自动清理天数
                </label>
                <Input
                  type="number"
                  className="px-4 py-2"
                  defaultValue={30}
                />
                <p className="mt-1 text-sm font-medium text-muted-foreground">
                  超过指定天数的截图将被自动删除
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>开发者选项</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-semibold text-foreground">
                    显示定时任务
                  </label>
                  <p className="mt-1 text-sm font-medium text-muted-foreground">
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
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
