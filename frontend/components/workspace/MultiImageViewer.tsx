'use client';

import { useState, useEffect } from 'react';
import { X, Download, Maximize2, Image as ImageIcon } from 'lucide-react';

interface ImageInfo {
  url: string;
  name: string;
}

interface MultiImageViewerProps {
  images: ImageInfo[];
  initialIndex?: number;
  onClose?: () => void;
}

export default function MultiImageViewer({ images, onClose }: MultiImageViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageLoadStates, setImageLoadStates] = useState<Record<number, boolean>>({});

  const handleDownload = (image: ImageInfo, e: React.MouseEvent) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = image.url;
    link.download = image.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleImageLoad = (index: number) => {
    setImageLoadStates((prev) => ({ ...prev, [index]: true }));
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (isFullscreen) {
          setIsFullscreen(false);
        } else {
          onClose?.();
        }
        return;
      }

      // Don't handle keyboard shortcuts if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen, onClose]);

  if (images.length === 0) {
    return (
      <div className="flex flex-col h-full bg-background items-center justify-center">
        <ImageIcon className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No images to display</p>
        {onClose && (
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 rounded hover:bg-accent"
          >
            Close
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-background ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30 flex-shrink-0">
        <div className="flex items-center gap-2">
          <ImageIcon className="h-4 w-4 text-muted-foreground" />
          <h3 className="font-medium text-sm">Slides</h3>
          <span className="text-xs text-muted-foreground">
            ({images.length} {images.length === 1 ? 'image' : 'images'})
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded hover:bg-accent"
            title={isFullscreen ? "Exit Fullscreen (F)" : "Fullscreen (F)"}
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          {!isFullscreen && onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded hover:bg-accent"
              title="Close (ESC)"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Images Grid - Vertical Scroll */}
      <div className="flex-1 overflow-y-auto bg-muted/20 p-4">
        <div className="max-w-5xl mx-auto space-y-4">
          {images.map((image, index) => (
            <div
              key={index}
              className="bg-background rounded-lg border border-border overflow-hidden shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Image Header */}
              <div className="px-4 py-2 border-b bg-muted/30 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-muted-foreground">
                    #{index + 1}
                  </span>
                  <span className="text-sm font-medium truncate max-w-md">
                    {image.name}
                  </span>
                </div>
                <button
                  onClick={(e) => handleDownload(image, e)}
                  className="p-1.5 rounded hover:bg-accent transition-colors"
                  title="Download"
                >
                  <Download className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>

              {/* Image Container */}
              <div className="relative bg-muted/20 flex items-center justify-center min-h-[200px]">
                {!imageLoadStates[index] && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-muted-foreground text-sm">Loading...</div>
                  </div>
                )}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={image.url}
                  alt={image.name}
                  className={`max-w-full h-auto object-contain ${
                    imageLoadStates[index] ? 'opacity-100' : 'opacity-0'
                  } transition-opacity duration-200`}
                  onLoad={() => handleImageLoad(index)}
                  onError={() => handleImageLoad(index)}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-4 py-2 border-t bg-muted/30 text-xs text-muted-foreground flex items-center justify-between flex-shrink-0">
        <div>
          {images.length} {images.length === 1 ? 'image' : 'images'} in slides folder
        </div>
        <div className="flex gap-4">
          <kbd className="px-2 py-1 bg-background rounded border text-xs">F</kbd>
          <span>fullscreen</span>
          <kbd className="px-2 py-1 bg-background rounded border text-xs">ESC</kbd>
          <span>to close</span>
        </div>
      </div>
    </div>
  );
}
