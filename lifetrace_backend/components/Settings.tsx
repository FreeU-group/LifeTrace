import { useState, useEffect } from "react";
import { X, ChevronRight, User, Eye, Search, Grid, Shield, Sun, Moon } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Select } from "./ui/select";
import { Separator } from "./ui/separator";

interface SettingsProps {
  theme: 'light' | 'dark';
  onThemeToggle: () => void;
  onClose: () => void;
}

type SettingCategory =
  | 'account'
  | 'interface'
  | 'search'
  | 'modules'
  | 'privacy';

type FocusArea = 'sidebar' | 'content';

const settingsCategories = [
  { id: 'account' as SettingCategory, label: '账户与个人信息', icon: User },
  { id: 'interface' as SettingCategory, label: '界面与显示', icon: Eye },
  { id: 'search' as SettingCategory, label: '搜索与内容偏好', icon: Search },
  { id: 'modules' as SettingCategory, label: '功能模块管理', icon: Grid },
  { id: 'privacy' as SettingCategory, label: '隐私与安全', icon: Shield },
];

export function Settings({ theme, onThemeToggle, onClose }: SettingsProps) {
  const [activeCategory, setActiveCategory] = useState<SettingCategory>('account');
  const [focusArea, setFocusArea] = useState<FocusArea>('sidebar');
  const [selectedSidebarIndex, setSelectedSidebarIndex] = useState(0);
  const [searchHistoryEnabled, setSearchHistoryEnabled] = useState(true);
  const [contentFilterEnabled, setContentFilterEnabled] = useState(false);
  const [dataCollectionEnabled, setDataCollectionEnabled] = useState(false);
  const [defaultSearchEngine, setDefaultSearchEngine] = useState('apps');

  const isDark = theme === 'dark';

  const getThemeColors = () => {
    if (isDark) {
      return {
        background: 'rgb(47, 48, 49)',
        panel: 'rgb(60, 60, 60)',
        sidebar: 'rgb(55, 56, 57)',
        text: 'text-white',
        textSecondary: 'text-gray-300',
        textMuted: 'text-gray-400',
        border: 'border-slate-600',
        hover: 'hover:bg-slate-700',
        selected: 'bg-slate-700',
        ring: 'ring-slate-400'
      };
    } else {
      return {
        background: 'rgb(248, 249, 250)',
        panel: 'white',
        sidebar: 'rgb(245, 246, 247)',
        text: 'text-gray-900',
        textSecondary: 'text-gray-700',
        textMuted: 'text-gray-500',
        border: 'border-gray-300',
        hover: 'hover:bg-gray-100',
        selected: 'bg-gray-200',
        ring: 'ring-gray-400'
      };
    }
  };

  const colors = getThemeColors();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          e.preventDefault();
          onClose();
          break;

        case 'ArrowUp':
          e.preventDefault();
          if (focusArea === 'sidebar' && selectedSidebarIndex > 0) {
            setSelectedSidebarIndex(selectedSidebarIndex - 1);
            setActiveCategory(settingsCategories[selectedSidebarIndex - 1].id);
          }
          break;

        case 'ArrowDown':
          e.preventDefault();
          if (focusArea === 'sidebar' && selectedSidebarIndex < settingsCategories.length - 1) {
            setSelectedSidebarIndex(selectedSidebarIndex + 1);
            setActiveCategory(settingsCategories[selectedSidebarIndex + 1].id);
          }
          break;

        case 'ArrowRight':
          e.preventDefault();
          if (focusArea === 'sidebar') {
            setFocusArea('content');
          }
          break;

        case 'ArrowLeft':
          e.preventDefault();
          if (focusArea === 'content') {
            setFocusArea('sidebar');
          }
          break;

        case 'Enter':
          e.preventDefault();
          if (focusArea === 'sidebar') {
            setActiveCategory(settingsCategories[selectedSidebarIndex].id);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusArea, selectedSidebarIndex, onClose]);

  const renderAccountSettings = () => (
    <div className="space-y-8">
      <div>
        <h2 className={`text-2xl mb-6 ${colors.text}`}>账户与个人信息</h2>

        <div className="space-y-6">
          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>个人资料编辑</h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="username" className={colors.textSecondary}>用户名</Label>
                <Input
                  id="username"
                  placeholder="输入用户名"
                  className="mt-2"
                  style={{ backgroundColor: colors.panel }}
                />
              </div>
              <div>
                <Label htmlFor="email" className={colors.textSecondary}>邮箱地址</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="输入邮箱地址"
                  className="mt-2"
                  style={{ backgroundColor: colors.panel }}
                />
              </div>
            </div>
          </div>

          <Separator className={colors.border} />

          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>账户安全设置</h3>
            <div className="space-y-4">
              <Button variant="outline" className="w-full justify-start">
                更改密码
              </Button>
              <Button variant="outline" className="w-full justify-start">
                启用两步验证
              </Button>
              <Button variant="outline" className="w-full justify-start text-red-600 border-red-600 hover:bg-red-50">
                删除账户
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderInterfaceSettings = () => (
    <div className="space-y-8">
      <div>
        <h2 className={`text-2xl mb-6 ${colors.text}`}>界面与显示</h2>

        <div className="space-y-6">
          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>主题设置</h3>
            <div className="flex items-center justify-between">
              <div>
                <Label className={colors.textSecondary}>深色模式</Label>
                <p className={`text-sm ${colors.textMuted} mt-1`}>切换深色或浅色主题</p>
              </div>
              <div className="flex items-center gap-2">
                <Sun className={`w-4 h-4 ${colors.textMuted}`} />
                <Switch checked={isDark} onCheckedChange={onThemeToggle} />
                <Moon className={`w-4 h-4 ${colors.textMuted}`} />
              </div>
            </div>
          </div>

          <Separator className={colors.border} />

          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>界面语言选择</h3>
            <div className="space-y-4">
              <div>
                <Label className={colors.textSecondary}>语言</Label>
                <div className="mt-2 grid grid-cols-2 gap-3">
                  <Button variant="outline" className="justify-start">
                    🇨🇳 中文 (简体)
                  </Button>
                  <Button variant="ghost" className="justify-start">
                    🇺🇸 English
                  </Button>
                  <Button variant="ghost" className="justify-start">
                    🇯🇵 日本語
                  </Button>
                  <Button variant="ghost" className="justify-start">
                    🇰🇷 한국어
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSearchSettings = () => (
    <div className="space-y-8">
      <div>
        <h2 className={`text-2xl mb-6 ${colors.text}`}>搜索与内容偏好</h2>

        <div className="space-y-6">
          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>默认搜索引擎选择</h3>
            <div className="space-y-3">
              {[
                { id: 'apps', label: '应用', icon: '💻' },
                { id: 'docs', label: '文档', icon: '📄' },
                { id: 'timemachine', label: '时光机', icon: '⏰' }
              ].map((engine) => (
                <Button
                  key={engine.id}
                  variant={defaultSearchEngine === engine.id ? "default" : "ghost"}
                  className="w-full justify-start"
                  onClick={() => setDefaultSearchEngine(engine.id)}
                >
                  <span className="mr-3">{engine.icon}</span>
                  {engine.label}
                  {defaultSearchEngine === engine.id && (
                    <span className="ml-auto text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      默认
                    </span>
                  )}
                </Button>
              ))}
            </div>
          </div>

          <Separator className={colors.border} />

          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>搜索历史管理</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className={colors.textSecondary}>保存搜索历史</Label>
                  <p className={`text-sm ${colors.textMuted} mt-1`}>记住您的搜索查询以便快速访问</p>
                </div>
                <Switch
                  checked={searchHistoryEnabled}
                  onCheckedChange={setSearchHistoryEnabled}
                />
              </div>
              <Button variant="outline" className="w-full justify-start">
                清除所有搜索历史
              </Button>
            </div>
          </div>

          <Separator className={colors.border} />

          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>内容过滤设置</h3>
            <div className="flex items-center justify-between">
              <div>
                <Label className={colors.textSecondary}>启用安全搜索</Label>
                <p className={`text-sm ${colors.textMuted} mt-1`}>过滤不适宜内容</p>
              </div>
              <Switch
                checked={contentFilterEnabled}
                onCheckedChange={setContentFilterEnabled}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderModulesSettings = () => (
    <div className="space-y-8">
      <div>
        <h2 className={`text-2xl mb-6 ${colors.text}`}>功能模块管理</h2>

        <div className="space-y-6">
          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>快捷功能按键</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg border" style={{ backgroundColor: colors.panel }}>
                  <div>
                    <p className={colors.textSecondary}>打开搜索</p>
                    <p className={`text-sm ${colors.textMuted}`}>Ctrl + Space</p>
                  </div>
                  <Button variant="ghost" size="sm">编辑</Button>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border" style={{ backgroundColor: colors.panel }}>
                  <div>
                    <p className={colors.textSecondary}>快速启动</p>
                    <p className={`text-sm ${colors.textMuted}`}>Alt + Space</p>
                  </div>
                  <Button variant="ghost" size="sm">编辑</Button>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border" style={{ backgroundColor: colors.panel }}>
                  <div>
                    <p className={colors.textSecondary}>设置面板</p>
                    <p className={`text-sm ${colors.textMuted}`}>Ctrl + ,</p>
                  </div>
                  <Button variant="ghost" size="sm">编辑</Button>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border" style={{ backgroundColor: colors.panel }}>
                  <div>
                    <p className={colors.textSecondary}>退出应用</p>
                    <p className={`text-sm ${colors.textMuted}`}>Ctrl + Q</p>
                  </div>
                  <Button variant="ghost" size="sm">编辑</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPrivacySettings = () => (
    <div className="space-y-8">
      <div>
        <h2 className={`text-2xl mb-6 ${colors.text}`}>隐私与安全</h2>

        <div className="space-y-6">
          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>数据收集偏好</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className={colors.textSecondary}>使用数据分析</Label>
                  <p className={`text-sm ${colors.textMuted} mt-1`}>帮助改善软件体验</p>
                </div>
                <Switch
                  checked={dataCollectionEnabled}
                  onCheckedChange={setDataCollectionEnabled}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className={colors.textSecondary}>崩溃报告</Label>
                  <p className={`text-sm ${colors.textMuted} mt-1`}>自动发送错误报告以帮助修复问题</p>
                </div>
                <Switch checked={true} />
              </div>
            </div>
          </div>

          <Separator className={colors.border} />

          <div>
            <h3 className={`text-lg mb-4 ${colors.text}`}>数据管理</h3>
            <div className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                导出用户数据
              </Button>
              <Button variant="outline" className="w-full justify-start">
                清除应用缓存
              </Button>
              <Button variant="outline" className="w-full justify-start text-red-600 border-red-600 hover:bg-red-50">
                重置所有设置
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeCategory) {
      case 'account':
        return renderAccountSettings();
      case 'interface':
        return renderInterfaceSettings();
      case 'search':
        return renderSearchSettings();
      case 'modules':
        return renderModulesSettings();
      case 'privacy':
        return renderPrivacySettings();
      default:
        return renderAccountSettings();
    }
  };

  return (
    <div
      className={`h-screen flex flex-col transition-colors duration-300 ${colors.text}`}
      style={{ backgroundColor: colors.background }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: colors.border }}>
        <div className="flex items-center gap-4">
          <h1 className={`text-2xl ${colors.text}`}>设置</h1>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className={`w-10 h-10 rounded-full p-0 transition-colors ${
            isDark
              ? 'text-gray-300 hover:text-white hover:bg-slate-700'
              : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <X className="w-5 h-5" />
        </Button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div
          className={`w-80 border-r ${colors.border}`}
          style={{ backgroundColor: colors.sidebar }}
        >
          <nav className="p-4">
            {settingsCategories.map((category, index) => {
              const Icon = category.icon;
              const isActive = activeCategory === category.id;
              const isKeyboardSelected = focusArea === 'sidebar' && selectedSidebarIndex === index;

              return (
                <Button
                  key={category.id}
                  variant="ghost"
                  className={`w-full justify-start p-4 h-auto mb-2 transition-all ${
                    isActive ? colors.selected : colors.hover
                  } ${isKeyboardSelected ? `ring-2 ${colors.ring}` : ''}`}
                  onClick={() => {
                    setActiveCategory(category.id);
                    setSelectedSidebarIndex(index);
                  }}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  <span className="flex-1 text-left">{category.label}</span>
                  <ChevronRight className="w-4 h-4 ml-auto" />
                </Button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div
          className={`flex-1 overflow-y-auto custom-scrollbar transition-all ${
            focusArea === 'content' ? `ring-2 ${colors.ring}` : ''
          }`}
          style={{ backgroundColor: colors.panel }}
        >
          <div className="max-w-4xl mx-auto p-8">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="px-6 py-3 border-t" style={{ borderColor: colors.border }}>
        <div
          className="rounded-xl px-4 py-3 backdrop-blur-sm border"
          style={{
            backgroundColor: isDark ? 'rgba(60, 60, 60, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            borderColor: isDark ? 'rgba(100, 100, 100, 0.2)' : 'rgba(200, 200, 200, 0.3)'
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <kbd className={`inline-flex items-center justify-center h-5 px-2 text-xs font-medium rounded border ${
                  isDark
                    ? 'bg-slate-700 text-gray-300 border-slate-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}>↑↓</kbd>
                <span className={`text-sm ${colors.textSecondary}`}>导航</span>
              </div>

              <div className="flex items-center gap-2">
                <kbd className={`inline-flex items-center justify-center h-5 px-2 text-xs font-medium rounded border ${
                  isDark
                    ? 'bg-slate-700 text-gray-300 border-slate-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}>←→</kbd>
                <span className={`text-sm ${colors.textSecondary}`}>切换区域</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <kbd className={`inline-flex items-center justify-center h-5 px-2 text-xs font-medium rounded border ${
                  isDark
                    ? 'bg-slate-700 text-gray-300 border-slate-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}>Enter</kbd>
                <span className={`text-sm ${colors.textSecondary}`}>选择</span>
              </div>

              <div className="flex items-center gap-2">
                <kbd className={`inline-flex items-center justify-center h-5 px-2 text-xs font-medium rounded border ${
                  isDark
                    ? 'bg-slate-700 text-gray-300 border-slate-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}>Esc</kbd>
                <span className={`text-sm ${colors.textSecondary}`}>关闭设置</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
