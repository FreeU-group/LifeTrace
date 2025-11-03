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
  isLoading?: boolean;
  error?: string | null;
  hasSearched?: boolean;
  searchQuery?: string;
}

export function SearchResults({
  results,
  selectedId,
  selectedIndex,
  onSelectResult,
  focused,
  theme,
  isLoading = false,
  error = null,
  hasSearched = false,
  searchQuery = "",
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
      const selectedElement = selectedItemRef.current;
      const containerRect = container.getBoundingClientRect();
      const elementRect = selectedElement.getBoundingClientRect();

      const isVisible =
        elementRect.top >= containerRect.top &&
        elementRect.bottom <= containerRect.bottom;

      if (!isVisible) {
        const scrollTop =
          selectedElement.offsetTop -
          container.offsetTop -
          container.clientHeight / 2 +
          selectedElement.clientHeight / 2;

        container.scrollTo({
          top: Math.max(0, scrollTop),
          behavior: "smooth",
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
        background: "#1a1a1a",
        categoryText: "text-gray-400",
        itemText: "text-gray-300",
        selectedBorder: "border-blue-500",
        selectedText: "text-blue-400",
        hoveredBorder: "border-gray-600",
        hoveredText: "text-gray-200",
        iconBg: "bg-gray-700",
        chevronColor: "text-gray-500",
      };
    } else {
      return {
        background: "#ffffff",
        categoryText: "text-gray-600",
        itemText: "text-gray-800",
        selectedBorder: "border-blue-500",
        selectedText: "text-blue-600",
        hoveredBorder: "border-gray-300",
        hoveredText: "text-gray-900",
        iconBg: "bg-gray-100",
        chevronColor: "text-gray-400",
      };
    }
  };

  const colors = getColors();

  // 渲染加载状态
  const renderLoadingState = () => (
    <div className="flex flex-col items-center justify-center h-64 px-4">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-4"></div>
      <p className={`text-sm ${colors.itemText}`}>正在搜索...</p>
    </div>
  );

  // 渲染错误状态
  const renderErrorState = () => (
    <div className="flex flex-col items-center justify-center h-64 px-4">
      <div className="text-4xl mb-4">⚠️</div>
      <p className={`text-sm ${colors.itemText} text-center`}>
        搜索出错：{error}
      </p>
    </div>
  );

  // 渲染空搜索结果状态
  const renderEmptyState = () => (
    <div className="flex flex-col items-center justify-center h-64 px-4">
      <div className="text-4xl mb-4">🔍</div>
      <p className={`text-sm ${colors.itemText} text-center`}>
        没有找到与 "{searchQuery}" 相关的结果
      </p>
      <p className={`text-xs ${colors.categoryText} text-center mt-2`}>
        尝试使用不同的关键词搜索
      </p>
    </div>
  );

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
        {isLoading ? (
          renderLoadingState()
        ) : error ? (
          renderErrorState()
        ) : hasSearched && results.length === 0 ? (
          renderEmptyState()
        ) : (
          Object.entries(groupedResults).map(
            ([category, categoryResults]) => (
              <div key={category} className="py-2">
                <div className="px-4 py-3">
                  <h3
                    className={`text-base font-bold uppercase tracking-wide ${colors.categoryText}`}
                  >
                    {category}
                  </h3>
                </div>
                <div>
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
                              <div className="text-base font-semibold truncate max-w-[200px]" title={result.title}>
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
              </div>
            )
          )
        )}

        {!hasSearched && !isLoading && (
          <div className="px-4 py-3">
            <h3 className={`text-base font-bold uppercase tracking-wide ${colors.categoryText}`}>
              商店
            </h3>
          </div>
        )}
      </div>
    </div>
  );
}
