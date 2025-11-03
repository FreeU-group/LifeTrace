import { ChevronRight } from "lucide-react";
import { Button } from "./ui/button";
import { useEffect, useRef, useState } from "react";

interface SearchResult {
  id: string;
  title: string;
  subtitle?: string;
  icon?: string;
  category: string;
}

interface SearchResultsProps {
  results: SearchResult[];
  selectedId: string | null;
  selectedIndex: number;
  onSelectResult: (id: string) => void;
  focused: boolean;
  theme: "light" | "dark";
}

export function SearchResults({
  results,
  selectedId,
  selectedIndex,
  onSelectResult,
  focused,
  theme,
}: SearchResultsProps) {
  const selectedItemRef = useRef<HTMLButtonElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const isDark = theme === "dark";

  // 当选中项改变时，滚动到可见区域
  useEffect(() => {
    if (
      focused &&
      selectedItemRef.current &&
      scrollContainerRef.current
    ) {
      const container = scrollContainerRef.current;
      const item = selectedItemRef.current;

      const containerRect = container.getBoundingClientRect();
      const itemRect = item.getBoundingClientRect();

      if (itemRect.bottom > containerRect.bottom) {
        // 项目在容器底部以下，向下滚动
        item.scrollIntoView({
          behavior: "smooth",
          block: "end",
        });
      } else if (itemRect.top < containerRect.top) {
        // 项目在容器顶部以上，向上滚动
        item.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }
  }, [selectedIndex, focused]);

  const groupedResults = results.reduce(
    (acc, result) => {
      if (!acc[result.category]) {
        acc[result.category] = [];
      }
      acc[result.category].push(result);
      return acc;
    },
    {} as Record<string, SearchResult[]>,
  );

  let globalIndex = 0;

  const getColors = () => {
    if (isDark) {
      return {
        background: "rgb(47, 48, 49)",
        categoryText: "text-gray-400",
        itemText: "text-gray-300",
        selectedText: "text-white",
        hoveredText: "text-gray-200",
        iconBg: "bg-slate-600",
        chevronColor: "text-gray-500",
        selectedBorder: "border-slate-400",
        hoveredBorder: "border-slate-500",
      };
    } else {
      return {
        background: "rgb(248, 249, 250)",
        categoryText: "text-gray-600",
        itemText: "text-gray-700",
        selectedText: "text-gray-900",
        hoveredText: "text-gray-800",
        iconBg: "bg-gray-200",
        chevronColor: "text-gray-400",
        selectedBorder: "border-gray-400",
        hoveredBorder: "border-gray-300",
      };
    }
  };

  const colors = getColors();

  return (
    <div
      className="w-96 flex flex-col"
      style={{
        backgroundColor: colors.background,
        height: "calc(100vh - 160px)",
      }}
    >
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto custom-scrollbar"
      >
        {Object.entries(groupedResults).map(
          ([category, categoryResults]) => (
            <div key={category} className="py-2">
              <div className="px-4 py-3">
                <h3
                  className={`text-base font-bold uppercase tracking-wide ${colors.categoryText}`}
                >
                  {category}
                </h3>
              </div>

              {categoryResults.map((result) => {
                const currentIndex = globalIndex++;
                const isKeyboardSelected =
                  focused && selectedIndex === currentIndex;
                const isSelected = isKeyboardSelected || selectedId === result.id;

                return (
                  <div key={result.id} className="px-2">
                    <Button
                      ref={
                        isKeyboardSelected
                          ? selectedItemRef
                          : undefined
                      }
                      variant="ghost"
                      className={`w-full justify-start px-4 py-4 h-auto rounded-lg transition-all border-2 ${
                        isSelected
                          ? `${colors.selectedBorder} ${colors.selectedText}`
                          : hoveredId === result.id
                          ? `${colors.hoveredBorder} ${colors.hoveredText}`
                          : `border-transparent ${colors.itemText}`
                      }`}
                      onMouseEnter={() => {
                        setHoveredId(result.id);
                      }}
                      onMouseLeave={() => {
                        setHoveredId(null);
                      }}
                      onClick={() => {
                        onSelectResult(result.id);
                      }}
                    >
                      <div className="flex items-center gap-4 w-full">
                        <div
                          className={`w-9 h-9 ${colors.iconBg} rounded flex items-center justify-center text-lg ${
                            isDark
                              ? "text-white"
                              : "text-gray-700"
                          }`}
                        >
                          {result.icon || "📁"}
                        </div>
                        <div className="flex-1 text-left">
                          <div className="text-base font-semibold">
                            {result.title}
                          </div>
                          {result.subtitle && (
                            <div
                              className={`text-sm font-medium ${isDark ? "text-gray-500" : "text-gray-500"}`}
                            >
                              {result.subtitle}
                            </div>
                          )}
                        </div>
                        <ChevronRight
                          className={`w-4 h-4 ${colors.chevronColor}`}
                        />
                      </div>
                    </Button>
                  </div>
                );
              })}
            </div>
          ),
        )}

        <div className="px-4 py-3">
          <h3 className={`text-base font-bold uppercase tracking-wide ${colors.categoryText}`}>
            商店
          </h3>
        </div>
      </div>
    </div>
  );
}
