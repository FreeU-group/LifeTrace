import { forwardRef } from "react";
import { Search, Settings, Sun, Moon, X } from "lucide-react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

interface SearchHeaderProps {
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
  focused: boolean;
  theme: 'light' | 'dark';
  onThemeToggle: () => void;
  onSettingsClick: () => void;
  onCloseClick: () => void;
}

export const SearchHeader = forwardRef<HTMLInputElement, SearchHeaderProps>(
  ({ searchQuery, onSearchQueryChange, focused, theme, onThemeToggle, onSettingsClick, onCloseClick }, ref) => {
    const isDark = theme === 'dark';

    return (
      <div className="w-full px-6 pt-5 pb-3">
        <div className="relative flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 stroke-2 ${
              isDark ? 'text-slate-300' : 'text-gray-600'
            }`} />
            <Input
              ref={ref}
              type="text"
              placeholder="搜索"
              value={searchQuery}
              onChange={(e) => onSearchQueryChange(e.target.value)}
              className={`pl-12 pr-4 rounded-full h-12 transition-all text-base font-bold uppercase tracking-wide border-2 ${
                focused ? 'ring-2 ring-slate-400' : ''
              } ${
                isDark
                  ? 'border-gray-600 text-white placeholder-gray-400 hover:border-gray-500'
                  : 'border-gray-300 text-gray-900 placeholder-gray-500 bg-gray-50 hover:border-gray-400'
              }`}
              style={{
                backgroundColor: isDark ? 'rgb(60, 60, 60)' : undefined
              }}
            />
          </div>

          {/* 右上角按钮组 */}
          <div className="flex items-center gap-2">
            {/* 主题切换按钮 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onThemeToggle}
              className={`w-12 h-12 rounded-full p-0 transition-colors ${
                isDark
                  ? 'text-gray-300 hover:text-white hover:bg-slate-700'
                  : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {isDark ? <Sun className="w-6 h-6 stroke-2" /> : <Moon className="w-6 h-6 stroke-2" />}
            </Button>

            {/* 设置按钮 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onSettingsClick}
              className={`w-12 h-12 rounded-full p-0 transition-colors ${
                isDark
                  ? 'text-gray-300 hover:text-white hover:bg-slate-700'
                  : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Settings className="w-6 h-6 stroke-2" />
            </Button>

            {/* 关闭按钮 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onCloseClick}
              className={`w-12 h-12 rounded-full p-0 transition-colors ${
                isDark
                  ? 'text-gray-300 hover:text-white hover:bg-slate-700'
                  : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <X className="w-6 h-6 stroke-2" />
            </Button>
          </div>
        </div>
      </div>
    );
  }
);

SearchHeader.displayName = 'SearchHeader';
