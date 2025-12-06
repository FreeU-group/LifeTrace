'use client';

import { useState, useEffect, useRef } from 'react';
import { Loader2, CheckCircle2, XCircle, ChevronDown, ChevronRight, Sparkles, Image as ImageIcon } from 'lucide-react';

interface Slide {
  title: string;
  index: number;
  prompt: string;
  status: 'pending' | 'generating' | 'done' | 'error';
  error?: string;
  filename?: string;
  url?: string;
  isExpanded: boolean;
}

interface SlidesGenerationModalProps {
  isOpen: boolean;
  slides: Slide[];
  currentSlideIndex: number | null;
  isGenerating: boolean;
  isComplete: boolean;
  hasError: boolean;
  onClose: () => void;
  onToggleSlide: (index: number) => void;
  // i18n labels
  labels: {
    title: string;
    generating: string;
    complete: string;
    failed: string;
    close: string;
    pending: string;
    generatingStatus: string;
    doneStatus: string;
    errorStatus: string;
    progress: string;
  };
}

export default function SlidesGenerationModal({
  isOpen,
  slides,
  currentSlideIndex,
  isGenerating,
  isComplete,
  hasError,
  onClose,
  onToggleSlide,
  labels,
}: SlidesGenerationModalProps) {
  const contentRefs = useRef<(HTMLDivElement | null)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到当前生成的幻灯片
  useEffect(() => {
    if (currentSlideIndex !== null && contentRefs.current[currentSlideIndex]) {
      contentRefs.current[currentSlideIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [currentSlideIndex]);

  // 自动滚动到最新内容
  useEffect(() => {
    if (containerRef.current && isGenerating) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [slides, isGenerating]);

  if (!isOpen) return null;

  const completedCount = slides.filter((s) => s.status === 'done').length;
  const errorCount = slides.filter((s) => s.status === 'error').length;
  const totalCount = slides.length;

  const getStatusIcon = (status: Slide['status']) => {
    switch (status) {
      case 'pending':
        return <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30" />;
      case 'generating':
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case 'done':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusText = (status: Slide['status']) => {
    switch (status) {
      case 'pending':
        return labels.pending;
      case 'generating':
        return labels.generatingStatus;
      case 'done':
        return labels.doneStatus;
      case 'error':
        return labels.errorStatus;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 背景遮罩 */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* 模态框 */}
      <div className="relative w-full max-w-3xl max-h-[85vh] mx-4 bg-background rounded-xl shadow-2xl border border-border flex flex-col overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
              <ImageIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">{labels.title}</h2>
              <p className="text-sm text-muted-foreground">
                {isGenerating
                  ? labels.generating
                  : isComplete
                    ? hasError
                      ? labels.failed
                      : labels.complete
                    : labels.pending}
              </p>
            </div>
          </div>

          {/* 进度指示 */}
          <div className="flex items-center gap-3">
            {totalCount > 0 && (
              <div className="text-sm text-muted-foreground">
                {labels.progress.replace('{completed}', String(completedCount)).replace('{total}', String(totalCount))}
              </div>
            )}
            {isGenerating && <Loader2 className="h-5 w-5 animate-spin text-primary" />}
            {isComplete && !hasError && <CheckCircle2 className="h-5 w-5 text-green-500" />}
            {isComplete && hasError && <XCircle className="h-5 w-5 text-red-500" />}
          </div>
        </div>

        {/* 进度条 */}
        {totalCount > 0 && (
          <div className="h-1 bg-muted">
            <div
              className={`h-full transition-all duration-300 ${
                hasError ? 'bg-red-500' : 'bg-gradient-to-r from-purple-500 to-pink-500'
              }`}
              style={{ width: `${(completedCount / totalCount) * 100}%` }}
            />
          </div>
        )}

        {/* 幻灯片列表 */}
        <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-3">
          {slides.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>正在解析大纲...</span>
            </div>
          ) : (
            slides.map((slide, index) => (
              <div
                key={index}
                ref={(el) => { contentRefs.current[index] = el; }}
                className={`rounded-lg border transition-all ${
                  slide.status === 'generating'
                    ? 'border-primary bg-primary/5'
                    : slide.status === 'done'
                      ? 'border-green-500/30 bg-green-500/5'
                      : slide.status === 'error'
                        ? 'border-red-500/30 bg-red-500/5'
                        : 'border-border bg-card'
                }`}
              >
                {/* 幻灯片标题栏 */}
                <button
                  onClick={() => onToggleSlide(index)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-muted/50 transition-colors rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {slide.isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    )}
                    {getStatusIcon(slide.status)}
                    <span className="font-medium text-foreground">{slide.title}</span>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    slide.status === 'generating'
                      ? 'bg-primary/10 text-primary'
                      : slide.status === 'done'
                        ? 'bg-green-500/10 text-green-600 dark:text-green-400'
                        : slide.status === 'error'
                          ? 'bg-red-500/10 text-red-600 dark:text-red-400'
                          : 'bg-muted text-muted-foreground'
                  }`}>
                    {getStatusText(slide.status)}
                  </span>
                </button>

                {/* 幻灯片内容 */}
                {slide.isExpanded && (
                  <div className="px-4 pb-4">
                    {slide.status === 'pending' ? (
                      <div className="text-sm text-muted-foreground italic">
                        等待生成...
                      </div>
                    ) : slide.status === 'error' ? (
                      <div className="text-sm text-red-500">
                        {slide.error || '生成失败'}
                      </div>
                    ) : slide.status === 'done' && slide.url ? (
                      <div className="space-y-2">
                        <div className="text-sm text-muted-foreground">
                          Prompt: {slide.prompt}
                        </div>
                        <div className="rounded-lg overflow-hidden border border-border">
                          <img
                            src={slide.url.startsWith('http') ? slide.url : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${slide.url}`}
                            alt={slide.title}
                            className="w-full h-auto"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          文件名: {slide.filename}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">
                        {slide.status === 'generating' ? '正在生成...' : ''}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* 底部操作栏 */}
        <div className="flex items-center justify-end px-6 py-4 border-t border-border bg-muted/30">
          <button
            onClick={onClose}
            disabled={isGenerating}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              isGenerating
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            }`}
          >
            {labels.close}
          </button>
        </div>
      </div>
    </div>
  );
}
