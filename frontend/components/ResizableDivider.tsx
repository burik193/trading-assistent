"use client";

import { useRef, useCallback, useEffect, useState } from "react";

/** Right-pointing chevron (▶). fill=currentColor so it matches button color. */
function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 12 12" fill="currentColor" aria-hidden>
      <path d="M5 3v6l4-3-4-3z" />
    </svg>
  );
}

/** Left-pointing chevron (◀). fill=currentColor so it matches button color. */
function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 12 12" fill="currentColor" aria-hidden>
      <path d="M7 3v6l-4-3 4-3z" />
    </svg>
  );
}

type Props = {
  /** Called during drag with horizontal delta in pixels */
  onResize: (deltaX: number) => void;
  /** Which side has the collapse/expand button */
  toggleSide?: "left" | "right";
  /** Is that side currently collapsed (width 0) */
  collapsed?: boolean;
  /** Toggle collapse/expand */
  onToggle?: () => void;
  /** Label for the toggle button (e.g. "Sidebar", "Chat") */
  toggleLabel?: string;
};

export function ResizableDivider({
  onResize,
  toggleSide,
  collapsed = false,
  onToggle,
  toggleLabel = "Panel",
}: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const startX = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if ((e.target as HTMLElement).closest("button")) return;
      e.preventDefault();
      startX.current = e.clientX;
      setIsDragging(true);
    },
    []
  );

  useEffect(() => {
    if (!isDragging) return;
    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startX.current;
      startX.current = e.clientX;
      onResize(deltaX);
    };
    const handleMouseUp = () => {
      setIsDragging(false);
    };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging, onResize]);

  const showToggle = toggleSide != null && onToggle != null;
  const expand = collapsed;

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      className={`group flex flex-col items-stretch w-2 shrink-0 border-zinc-800 border-l border-r transition-colors ${
        isDragging ? "bg-zinc-600" : "bg-zinc-900 hover:bg-zinc-800"
      }`}
      onMouseDown={handleMouseDown}
      style={{ cursor: "col-resize" }}
    >
      {/* Draggable hit area */}
      <div className="flex-1 min-h-[2rem] w-full" title="Drag to resize" />
      {showToggle && (
        <div className="flex items-center justify-center py-1">
          <button
            type="button"
            data-divider-toggle
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
            className="flex items-center justify-center w-6 h-6 rounded bg-zinc-800 border border-zinc-700 focus:outline-none focus:ring-1 focus:ring-[#71717a] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#71717a]"
            style={{ color: "#a1a1aa" }}
            title={expand ? `Show ${toggleLabel}` : `Hide ${toggleLabel}`}
            aria-label={expand ? `Show ${toggleLabel}` : `Hide ${toggleLabel}`}
          >
            {toggleSide === "left" ? (
              expand ? (
                <ChevronLeftIcon className="w-3.5 h-3.5" />
              ) : (
                <ChevronRightIcon className="w-3.5 h-3.5" />
              )
            ) : (
              expand ? (
                <ChevronRightIcon className="w-3.5 h-3.5" />
              ) : (
                <ChevronLeftIcon className="w-3.5 h-3.5" />
              )
            )}
          </button>
        </div>
      )}
      <div className="flex-1 min-h-[2rem] w-full" />
    </div>
  );
}
