import React, { useRef, useEffect, useState, useCallback } from 'react';

interface ScrollableTableProps {
  /** Minimum width the table content needs before scrolling kicks in */
  minWidth?: number;
  children: React.ReactNode;
}

/**
 * Wraps a Semi Design Table (or any content) in a horizontally scrollable
 * container with a custom scrollbar track below it.
 *
 * - On wide screens the table fits and no scrollbar appears.
 * - On narrow screens the table scrolls horizontally with a draggable
 *   thumb that mirrors / controls the scroll position.
 * - Tapping anywhere on the track jumps to that position.
 */
export function ScrollableTable({ minWidth = 460, children }: ScrollableTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [thumbStyle, setThumbStyle] = useState<React.CSSProperties>({
    position: 'absolute',
    top: 4,
    height: 20,
    width: '100%',
    left: 0,
    background: 'var(--semi-color-fill-2)',
    borderRadius: 6,
    userSelect: 'none',
    touchAction: 'none',
  });
  const [showBar, setShowBar] = useState(false);
  const isDragging = useRef(false);

  const updateThumb = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const maxScroll = el.scrollWidth - el.clientWidth;
    const overflow = maxScroll > 2;
    setShowBar(overflow);
    if (!overflow) return;
    const ratio = el.clientWidth / el.scrollWidth;
    const thumbW = Math.max(25, ratio * 100);
    const scrollRatio = el.scrollLeft / maxScroll;
    const left = scrollRatio * (100 - thumbW);
    setThumbStyle({
      position: 'absolute',
      top: 4,
      height: 20,
      width: `${thumbW}%`,
      left: `${left}%`,
      background: 'var(--semi-color-fill-2)',
      borderRadius: 6,
      userSelect: 'none',
      touchAction: 'none',
    });
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener('scroll', updateThumb, { passive: true });
    const observer = new ResizeObserver(updateThumb);
    observer.observe(el);
    updateThumb();
    return () => {
      el.removeEventListener('scroll', updateThumb);
      observer.disconnect();
    };
  }, [updateThumb]);

  const scrollToPosition = (clientX: number) => {
    const el = scrollRef.current;
    const track = trackRef.current;
    if (!el || !track) return;
    const rect = track.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    el.scrollLeft = ratio * (el.scrollWidth - el.clientWidth);
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    isDragging.current = true;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    scrollToPosition(e.clientX);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current) return;
    e.preventDefault();
    scrollToPosition(e.clientX);
  };

  const handlePointerUp = () => {
    isDragging.current = false;
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Scrollable content area — this is the width constraint */}
      <div
        ref={scrollRef}
        style={{
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
          width: '100%',
        }}
      >
        <div style={{ minWidth }}>{children}</div>
      </div>

      {/* Custom scrollbar track — only visible when content overflows */}
      {showBar && (
        <div
          ref={trackRef}
          style={{
            position: 'relative',
            height: 28,
            margin: '2px 8px 6px',
            background: 'var(--semi-color-fill-0)',
            borderRadius: 8,
            touchAction: 'none',
            userSelect: 'none',
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          <div style={thumbStyle} />
        </div>
      )}
    </div>
  );
}
