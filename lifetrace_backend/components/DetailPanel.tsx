import { useState } from "react";
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

  // 时光机图片轮播状态
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // 图片轮播控制函数
  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % timeMachineImages.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + timeMachineImages.length) % timeMachineImages.length);
  };

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
        {selectedResultData?.category === '时光机' ? (
          /* Time Machine Image Carousel - Enhanced with side thumbnails */
          <div className="flex items-center justify-center relative px-6 h-64">
            {/* Full carousel container */}
            <div className="w-full max-w-5xl h-56 relative flex items-center gap-6">

              {/* Left thumbnail */}
              <div className="w-28 h-20 md:w-32 md:h-24 rounded-lg overflow-hidden opacity-50 hover:opacity-70 transition-all duration-300 cursor-pointer flex-shrink-0 shadow-lg ring-1 ring-white/10"
                   onClick={prevImage}>
                <ImageWithFallback
                  src={timeMachineImages[(currentImageIndex - 1 + timeMachineImages.length) % timeMachineImages.length]}
                  alt="上一张图片"
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Main Image Display */}
              <div className="flex-1 h-52 rounded-xl overflow-hidden shadow-2xl relative group ring-1 ring-white/20">
                <ImageWithFallback
                  src={timeMachineImages[currentImageIndex]}
                  alt={`贾维斯AI助手图片 ${currentImageIndex + 1}`}
                  className="w-full h-full object-cover transition-all duration-500"
                />

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

              {/* Right thumbnail */}
              <div className="w-28 h-20 md:w-32 md:h-24 rounded-lg overflow-hidden opacity-50 hover:opacity-70 transition-all duration-300 cursor-pointer flex-shrink-0 shadow-lg ring-1 ring-white/10"
                   onClick={nextImage}>
                <ImageWithFallback
                  src={timeMachineImages[(currentImageIndex + 1) % timeMachineImages.length]}
                  alt="下一张图片"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>

            {/* Image Indicators - Positioned lower */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-3">
              {timeMachineImages.map((_, index) => (
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
              ))}
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

            {/* Description - Direct display */}
            <div
              className={`${colors.textSecondary} text-sm leading-relaxed max-h-20 overflow-y-auto custom-scrollbar p-3 rounded-lg`}
              style={{ backgroundColor: isDark ? 'rgba(0, 0, 0, 0.2)' : 'rgba(0, 0, 0, 0.05)' }}
            >
              {selectedResultData.description}
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
