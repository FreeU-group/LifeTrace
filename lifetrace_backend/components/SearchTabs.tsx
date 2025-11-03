import { Button } from "./ui/button";

interface SearchTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  focused: boolean;
  selectedIndex: number;
  theme: 'light' | 'dark';
}

const tabs = [
  { id: "all", label: "全部" },
  { id: "apps", label: "应用" },
  { id: "docs", label: "文档" },
  { id: "timemachine", label: "时光机" },
];

export function SearchTabs({ activeTab, onTabChange, focused, selectedIndex, theme }: SearchTabsProps) {
  const isDark = theme === 'dark';

  return (
    <div className="flex items-center gap-3 px-6 py-4">
      {tabs.map((tab, index) => (
        <Button
          key={tab.id}
          variant="ghost"
          size="sm"
          onClick={() => onTabChange(tab.id)}
          className={`rounded-full px-5 py-2.5 transition-all duration-200 border text-base font-bold uppercase tracking-wide ${
            activeTab === tab.id
              ? isDark
                ? "bg-slate-600 text-white border-slate-500 shadow-sm"
                : "bg-gray-200 text-gray-900 border-gray-300 shadow-sm"
              : isDark
                ? "text-gray-300 border-transparent"
                : "text-gray-700 border-transparent"
          } ${
            focused && selectedIndex === index
              ? "ring-2 ring-slate-400"
              : ""
          }`}
        >
          {tab.label}
        </Button>
      ))}

      <div className="flex-1" />
    </div>
  );
}
