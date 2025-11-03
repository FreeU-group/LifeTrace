import { useEffect, useState } from "react";
import { apiClient } from '../services/api';
import { ImageWithFallback } from './figma/ImageWithFallback';

// 时光机图片轮播 - 贾维斯AI助手风格
const timeMachineImages = [
  "https://images.unsplash.com/photo-1593377202145-c5e97fd065f4?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxBSSUyMGFzc2lzdGFudCUyMHJvYm90JTIwZGlnaXRhbCUyMHRlY2hub2xvZ3l8ZW58MXx8fHwxNzU1NDM3ODIwfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
  "https://images.unsplash.com/photo-1671417722838-3fbaa7f66203?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmdXR1cmlzdGljJTIwQUklMjBpbnRlcmZhY2UlMjBob2xvZ3JhbSUyMHRlY2hub2xvZ3l8ZW58MXx8fHwxNzU1NDM3ODIzfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
  "https://images.unsplash.com/photo-1677442136019-21780ecad995?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhcnRpZmljaWFsJTIwaW50ZWxsaWdlbmNlJTIwdmlydHVhbCUyMGFzc2lzdGFudCUyMGRpZ2l0YWx8ZW58MXx8fHwxNzU1NDM3ODI2fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
];

interface SearchResult {
  id: string;
  title: string;
  subtitle?: string;
  category: string;
  icon?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  description?: string;
}

interface DetailPanelProps {
  selectedResult: string | null;
  selectedResultData: SearchResult | null;
  focused: boolean;
  detailFocusArea: 'content' | 'actions';
  selectedActionIndex: number;
  theme: 'light' | 'dark';
}

export function DetailPanel({ selectedResult, selectedResultData, focused, detailFocusArea, selectedActionIndex, theme }: DetailPanelProps) {
  const isDark = theme === 'dark';

  // 时光机图片轮播状态（事件截图）
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [eventScreenshotIds, setEventScreenshotIds] = useState<number[]>([]);
  const [totalScreenshots, setTotalScreenshots] = useState(0); // 总截图数
  const [isLoadingMore, setIsLoadingMore] = useState(false); // 是否正在加载更多
  const [currentShotDesc, setCurrentShotDesc] = useState("");

  // 图片轮播控制函数
  const nextImage = () => {
    const nextIndex = (currentImageIndex + 1) % totalScreenshots;
    setCurrentImageIndex(nextIndex);

    // 如果下一张图片还没加载，则加载它
    if (nextIndex >= eventScreenshotIds.length && !isLoadingMore) {
      loadMoreScreenshots();
    }
  };

  const prevImage = () => {
    const prevIndex = (currentImageIndex - 1 + totalScreenshots) % totalScreenshots;
    setCurrentImageIndex(prevIndex);

    // 如果上一张图片还没加载，则加载它
    if (prevIndex >= eventScreenshotIds.length && !isLoadingMore) {
      loadMoreScreenshots();
    }
  };

  // 加载更多截图（懒加载）
  const loadMoreScreenshots = async () => {
    if (!selectedResultData || !selectedResultData.id.startsWith('event-') || isLoadingMore) {
      return;
    }

    setIsLoadingMore(true);
    const eventId = parseInt(selectedResultData.id.replace('event-', ''));

    try {
      const detail = await apiClient.getEventDetail(eventId);
      const ids = (detail.screenshots || []).map(s => s.id);
      setEventScreenshotIds(ids);
      setTotalScreenshots(ids.length);
    } catch (e) {
      console.error('加载更多截图失败:', e);
    } finally {
      setIsLoadingMore(false);
    }
  };

  // 当选择了事件项（id 形如 event-123）时，只加载第一张截图
  useEffect(() => {
    const loadFirstScreenshot = async () => {
      if (!selectedResultData || !selectedResultData.id.startsWith('event-')) {
        setEventScreenshotIds([]);
        setTotalScreenshots(0);
        setCurrentImageIndex(0);
        setCurrentShotDesc(selectedResultData?.description || "");
        return;
      }

      const eventId = parseInt(selectedResultData.id.replace('event-', ''));
      try {
        const detail = await apiClient.getEventDetail(eventId);
        const allIds = (detail.screenshots || []).map(s => s.id);

        // 只保存第一张截图ID，节省内存
        setEventScreenshotIds(allIds.length > 0 ? [allIds[0]] : []);
        setTotalScreenshots(allIds.length);
        setCurrentImageIndex(0);
      } catch (e) {
        setEventScreenshotIds([]);
        setTotalScreenshots(0);
      }
    };

    loadFirstScreenshot();

    // 清理函数：组件卸载或选择项变化时释放内存
    return () => {
      setEventScreenshotIds([]);
      setTotalScreenshots(0);
      setCurrentImageIndex(0);
      setCurrentShotDesc("");
    };
  }, [selectedResultData?.id]);

  // 当前图片变化时，加载对应截图的OCR文本作为描述
  useEffect(() => {
    const loadCurrentShotDesc = async () => {
      if (!eventScreenshotIds.length || currentImageIndex >= totalScreenshots) {
        setCurrentShotDesc("");
        return;
      }

      // 如果当前索引的截图ID还没加载，先触发加载
      if (currentImageIndex >= eventScreenshotIds.length) {
        setCurrentShotDesc("加载中...");
        return;
      }

      const sid = eventScreenshotIds[currentImageIndex];
      try {
        const detail = await apiClient.getScreenshotDetail(sid);
        const text = (detail.ocr_result?.text_content || "").trim();
        setCurrentShotDesc(text || detail.window_title || detail.app_name || "无文本内容");
      } catch (err) {
        setCurrentShotDesc("无文本内容");
      }
    };
    loadCurrentShotDesc();
  }, [currentImageIndex, eventScreenshotIds, totalScreenshots]);

  const getColors = () => {
    if (isDark) {
      return {
        background: 'rgb(47, 48, 49)',
        panel: 'rgb(60, 60, 60)',
        text: 'text-white',
        textSecondary: 'text-gray-300',
        textTertiary: 'text-gray-500',
        textMuted: 'text-gray-400',
        actionHover: 'hover:text-white',
        actionText: 'text-gray-300',
        bullet: 'bg-slate-500'
      };
    } else {
      return {
        background: 'rgb(248, 249, 250)',
        panel: 'white',
        text: 'text-gray-900',
        textSecondary: 'text-gray-700',
        textTertiary: 'text-gray-600',
        textMuted: 'text-gray-500',
        actionHover: 'hover:text-gray-900',
        actionText: 'text-gray-700',
        bullet: 'bg-gray-400'
      };
    }
  };

  const colors = getColors();

  if (!selectedResult) {
    return (
      <div className="flex-1 p-4 flex flex-col" style={{ backgroundColor: colors.background }}>
        <div
          className="flex-1 rounded-xl flex items-center justify-center mb-4"
          style={{ backgroundColor: colors.panel }}
        >
          <div className={colors.textMuted}>请选择一个搜索结果查看详情</div>
        </div>

        {/* Empty Action Panel */}
        <div
          className="h-32 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: colors.panel }}
        >
          <div className={colors.textMuted}>选择应用以查看快速操作</div>
        </div>
      </div>
    );
  }

  // Mock detail content based on selected result
  const getDetailContent = () => {
    if (!selectedResultData) {
      return {
        title: "应用详情",
        description: "这里显示所选应用程序的详细信息。",
        features: ["功能特性将在这里显示"]
      };
    }

    // 时光机项目的特殊处理
    if (selectedResultData.category === '时光机') {
      return {
        title: selectedResultData.title,
        description: "时光机记录了您的数字活动轨迹，帮助您回顾和追踪重要的操作历史。",
        features: [
          "自动记录活动时间",
          "详细描述活动内容",
          "智能分类管理",
          "快速搜索历史记录"
        ]
      };
    }

    switch (selectedResult) {
      case "onenote-win10":
        return {
          title: "OneNote for Windows 10",
          description: "Microsoft OneNote 是一个数字笔记本应用程序，可帮助您整理笔记、创意、会议记录等。",
          features: [
            "创建和整理笔记",
            "跨设备同步",
            "手写和绘图支持",
            "与Office集成"
          ]
        };
      case "nvidia-control":
        return {
          title: "NVIDIA Control Panel",
          description: "NVIDIA 控制面板是管理 NVIDIA 显卡设置的应用程序。",
          features: [
            "显示设置调整",
            "3D性能优化",
            "多显示器配置",
            "驱动程序更新"
          ]
        };
      default:
        return {
          title: selectedResultData.title,
          description: selectedResultData.category === '文档'
            ? "这是您的文档文件，包含重要的项目信息和数据。"
            : "这里显示所选应用程序的详细信息。",
          features: selectedResultData.category === '文档'
            ? ["文档编辑", "版本控制", "共享协作", "格式转换"]
            : ["功能特性将在这里显示"]
        };
    }
  };

  const content = getDetailContent();

  const actions = [
    {
      icon: (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V10zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
        </svg>
      ),
      label: "打开"
    },
    {
      icon: (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd"/>
          <path fillRule="evenodd" d="M4 5a2 2 0 012-2h8a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 3a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h.01a1 1 0 100-2H10zm3 0a1 1 0 000 2h.01a1 1 0 100-2H13z" clipRule="evenodd"/>
          <path d="M4 14a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1z"/>
        </svg>
      ),
      label: "以管理员身份运行"
    },
    {
      icon: (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/>
        </svg>
      ),
      label: "打开文件位置"
    }
  ];

  return (
    <div className="flex-1 p-4 flex flex-col" style={{ backgroundColor: colors.background }}>
      {/* Content Area */}
      <div
        className={`flex-1 rounded-xl p-8 mb-4 transition-all ${
          focused && detailFocusArea === 'content' ? 'ring-2 ring-slate-400' : ''
        }`}
        style={{ backgroundColor: colors.panel }}
      >
        {selectedResultData?.apiData?.id ? (
          /* 显示搜索结果对应的截图 */
          <div className="flex items-center justify-center relative px-6 h-80">
            <div className="w-full max-w-4xl h-72 relative flex items-center justify-center">
              <div className="flex-1 h-64 rounded-xl overflow-hidden shadow-2xl relative group ring-1 ring-white/20">
                <ImageWithFallback
                  src={`http://localhost:8840/api/screenshots/${selectedResultData.apiData.id}/image`}
                  alt={`截图 - ${selectedResultData.title}`}
                  className="w-full h-full object-cover transition-all duration-500"
                />
              </div>
            </div>
          </div>
        ) : selectedResultData?.category === '时光机' ? (
          /* Time Machine Image Carousel - Enhanced with side thumbnails */
          <div className="flex items-center justify-center relative px-6 h-64">
            {/* Full carousel container */}
            <div className="w-full max-w-5xl h-56 relative flex items-center gap-6">

              {/* Left thumbnail - 不预加载，避免内存占用 */}
              <div className="w-28 h-20 md:w-32 md:h-24 rounded-lg overflow-hidden opacity-50 hover:opacity-70 transition-all duration-300 cursor-pointer flex-shrink-0 shadow-lg ring-1 ring-white/10"
                   onClick={prevImage}>
                {eventScreenshotIds.length > 0 && currentImageIndex < eventScreenshotIds.length ? (
                  <div className={`w-full h-full flex items-center justify-center ${isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-500'}`}>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </div>
                ) : (
                  <ImageWithFallback
                    src={timeMachineImages[(currentImageIndex - 1 + timeMachineImages.length) % timeMachineImages.length]}
                    alt="上一张图片"
                    className="w-full h-full object-cover"
                  />
                )}
              </div>

              {/* Main Image Display */}
              <div className="flex-1 h-52 rounded-xl overflow-hidden shadow-2xl relative group ring-1 ring-white/20">
                {eventScreenshotIds.length > 0 && currentImageIndex < eventScreenshotIds.length ? (
                  <ImageWithFallback
                    src={`http://localhost:8840/api/screenshots/${eventScreenshotIds[currentImageIndex]}/image`}
                    alt={`截图 ${currentImageIndex + 1} / ${totalScreenshots}`}
                    className="w-full h-full object-cover transition-all duration-500"
                  />
                ) : (
                  <ImageWithFallback
                    src={timeMachineImages[currentImageIndex % timeMachineImages.length]}
                    alt={`贾维斯AI助手图片 ${currentImageIndex + 1}`}
                    className="w-full h-full object-cover transition-all duration-500"
                  />
                )}

                {/* Navigation Buttons */}
                <button
                  onClick={prevImage}
                  className={`absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full backdrop-blur-sm border transition-all duration-200 opacity-0 group-hover:opacity-100 hover:scale-110 z-10 ${
                    isDark
                      ? 'bg-black/20 border-white/20 text-white hover:bg-black/40'
                      : 'bg-white/20 border-black/20 text-black hover:bg-white/40'
                  }`}
                  style={{ backdropFilter: 'blur(8px)' }}
                >
                  <svg className="w-5 h-5 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </button>

                <button
                  onClick={nextImage}
                  className={`absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full backdrop-blur-sm border transition-all duration-200 opacity-0 group-hover:opacity-100 hover:scale-110 z-10 ${
                    isDark
                      ? 'bg-black/20 border-white/20 text-white hover:bg-black/40'
                      : 'bg-white/20 border-black/20 text-black hover:bg-white/40'
                  }`}
                  style={{ backdropFilter: 'blur(8px)' }}
                >
                  <svg className="w-5 h-5 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              {/* Right thumbnail - 不预加载，避免内存占用 */}
              <div className="w-28 h-20 md:w-32 md:h-24 rounded-lg overflow-hidden opacity-50 hover:opacity-70 transition-all duration-300 cursor-pointer flex-shrink-0 shadow-lg ring-1 ring-white/10"
                   onClick={nextImage}>
                {eventScreenshotIds.length > 0 && currentImageIndex < eventScreenshotIds.length ? (
                  <div className={`w-full h-full flex items-center justify-center ${isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-500'}`}>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                ) : (
                  <ImageWithFallback
                    src={timeMachineImages[(currentImageIndex + 1) % timeMachineImages.length]}
                    alt="下一张图片"
                    className="w-full h-full object-cover"
                  />
                )}
              </div>
            </div>

            {/* Image Indicators - 显示总数而不是已加载的ID数 */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-3 items-center">
              {totalScreenshots > 0 ? (
                // 事件截图：使用总截图数
                Array.from({ length: Math.min(totalScreenshots, 10) }, (_, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setCurrentImageIndex(index);
                      // 如果点击的截图还没加载，触发加载
                      if (index >= eventScreenshotIds.length && !isLoadingMore) {
                        loadMoreScreenshots();
                      }
                    }}
                    className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                      currentImageIndex === index
                        ? 'bg-white scale-125 shadow-lg'
                        : isDark
                          ? 'bg-white/40 hover:bg-white/60 hover:scale-110'
                          : 'bg-black/40 hover:bg-black/60 hover:scale-110'
                    }`}
                  />
                ))
              ) : (
                // 默认图片轮播
                timeMachineImages.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                      currentImageIndex === index
                        ? 'bg-white scale-125 shadow-lg'
                        : isDark
                          ? 'bg-white/40 hover:bg-white/60 hover:scale-110'
                          : 'bg-black/40 hover:bg-black/60 hover:scale-110'
                    }`}
                  />
                ))
              )}
              {totalScreenshots > 10 && (
                <div className={`text-xs ${isDark ? 'text-white/60' : 'text-black/60'} ml-1`}>
                  +{totalScreenshots - 10}
                </div>
              )}
              {isLoadingMore && (
                <div className={`text-xs ${isDark ? 'text-white/60' : 'text-black/60'} ml-2 flex items-center gap-1`}>
                  <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>加载中...</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Default Content for Apps and Documents */
          <div className="max-w-2xl">
            <h1 className={`text-2xl mb-4 ${colors.text}`}>{content.title}</h1>

            <div className="mb-6">
              <p className={`${colors.textSecondary} leading-relaxed`}>{content.description}</p>
            </div>

            <div className="mb-6">
              <h2 className={`text-lg mb-3 ${colors.text}`}>主要功能</h2>
              <ul className="space-y-2">
                {content.features.map((feature, index) => (
                  <li key={index} className={`${colors.textSecondary} flex items-center gap-2`}>
                    <div className={`w-1.5 h-1.5 ${colors.bullet} rounded-full`}></div>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Panel - Different for Time Machine */}
      {selectedResultData?.category === '时光机' ? (
        <div className="rounded-xl p-6" style={{ backgroundColor: colors.panel }}>
          <div className="space-y-4">
            {/* Time Range - Direct display */}
            <div className={`${colors.text} text-sm flex items-center gap-2`}>
              <span>{selectedResultData.timeRange?.start}</span>
              <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              <span>{selectedResultData.timeRange?.end}</span>
            </div>

            {/* Description - show current screenshot OCR if是事件 */}
            <div
              className={`${colors.textSecondary} text-sm leading-relaxed max-h-20 overflow-y-auto custom-scrollbar p-3 rounded-lg`}
              style={{ backgroundColor: isDark ? 'rgba(0, 0, 0, 0.2)' : 'rgba(0, 0, 0, 0.05)' }}
            >
              {eventScreenshotIds.length ? currentShotDesc : selectedResultData.description}
            </div>
          </div>
        </div>
      ) : (
        // Original Action Panel for Apps and Documents
        <div className="h-32 rounded-xl flex overflow-hidden" style={{ backgroundColor: colors.panel }}>
          {/* Left side - Actions */}
          <div className="w-64 p-4 flex flex-col justify-center">
            <div className="space-y-1">
              {actions.map((action, index) => (
                <div
                  key={index}
                  className={`flex items-center gap-3 ${colors.actionText} ${colors.actionHover} cursor-pointer group transition-all rounded px-2 py-1.5 ${
                    focused && detailFocusArea === 'actions' && selectedActionIndex === index
                      ? `ring-2 ring-slate-400 ${colors.text.replace('text-', '')}`
                      : ''
                  }`}
                >
                  <div className="w-5 h-5 flex items-center justify-center">
                    {action.icon}
                  </div>
                  <span className="text-sm">{action.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Elegant separator */}
          <div className="flex items-center px-2">
            <div className={`w-px bg-gradient-to-b from-transparent ${
              isDark ? 'via-gray-500' : 'via-gray-300'
            } to-transparent h-16 opacity-60`}></div>
          </div>

          {/* Right side - File Info */}
          <div className="flex-1 p-4 pr-6 min-w-0 flex flex-col justify-center">
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className={`text-sm ${colors.textMuted}`}>最后修改时间</span>
                <span className={`text-sm ${colors.text}`}>2024年12月15日 14:32</span>
              </div>

              <div className="flex items-center justify-between">
                <span className={`text-sm ${colors.textMuted}`}>所在路径</span>
                <span className={`text-sm ${colors.text} truncate ml-3`} title="C:\Program Files\WindowsApps\Microsoft.Office.OneNote_16001.14326.21200.0_x64__8wekyb3d8bbwe">
                  C:\Program Files\...\OneNote
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className={`text-sm ${colors.textMuted}`}>文件大小</span>
                <span className={`text-sm ${colors.text}`}>156 MB</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
