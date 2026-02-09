"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type ContentSegment =
  | { type: "visible"; content: string }
  | { type: "think"; content: string; open?: boolean };

const THINK_OPEN = "<think>";
const THINK_CLOSE = "</think>";

/**
 * Splits model content into visible and think segments.
 * Handles unclosed <think> (treats remainder as think in progress).
 */
export function parseThinkBlocks(content: string): ContentSegment[] {
  if (!content.trim()) return [];
  const segments: ContentSegment[] = [];
  let rest = content;
  while (rest.length > 0) {
    const openIdx = rest.indexOf(THINK_OPEN);
    if (openIdx === -1) {
      segments.push({ type: "visible", content: rest });
      break;
    }
    if (openIdx > 0) {
      segments.push({ type: "visible", content: rest.slice(0, openIdx) });
    }
    rest = rest.slice(openIdx + THINK_OPEN.length);
    const closeIdx = rest.indexOf(THINK_CLOSE);
    if (closeIdx === -1) {
      segments.push({ type: "think", content: rest });
      break;
    }
    segments.push({ type: "think", content: rest.slice(0, closeIdx) });
    rest = rest.slice(closeIdx + THINK_CLOSE.length);
  }
  return segments;
}

const COLLAPSIBLE_LABEL = "Model reasoning";

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 12 12" fill="currentColor" aria-hidden>
      <path d="M5 3v6l4-3-4-3z" />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 12 12" fill="currentColor" aria-hidden>
      <path d="M3 5l3 4 3-4H3z" />
    </svg>
  );
}

type Props = {
  content: string;
  className?: string;
};

export function MessageContent({ content, className = "" }: Props) {
  const [thinkOpen, setThinkOpen] = useState<Record<number, boolean>>({});
  const segments = parseThinkBlocks(content);

  const toggleThink = (index: number) => {
    setThinkOpen((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  if (segments.length === 0 && !content) return null;

  return (
    <div className={className}>
      {segments.map((seg, i) => {
        if (seg.type === "visible") {
          return (
            <div
              key={i}
              className="prose prose-invert prose-sm max-w-none prose-p:my-1.5 prose-headings:my-2 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-strong:text-zinc-200 prose-p:text-zinc-300 prose-headings:text-zinc-100"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{seg.content}</ReactMarkdown>
            </div>
          );
        }
        const isOpen = thinkOpen[i] ?? false;
        const id = `think-${i}`;
        return (
          <details
            key={i}
            className="my-2 rounded-lg border border-zinc-700 bg-zinc-800/80 overflow-hidden"
            open={isOpen}
            onToggle={(e) => {
              const target = e.target as HTMLDetailsElement;
              setThinkOpen((prev) => ({ ...prev, [i]: target.open }));
            }}
          >
            <summary
              className="list-none cursor-pointer select-none px-3 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-300 hover:bg-zinc-800 flex items-center gap-2"
              onClick={(e) => {
                e.preventDefault();
                toggleThink(i);
              }}
            >
              <span
                className="inline-flex items-center justify-center w-4 h-4 shrink-0"
                style={{ color: "#71717a" }}
                data-model-reasoning-chevron
                aria-hidden
              >
                {isOpen ? <ChevronDownIcon className="w-3 h-3" /> : <ChevronRightIcon className="w-3 h-3" />}
              </span>
              <span>{COLLAPSIBLE_LABEL}</span>
              {!isOpen && seg.content.trim().length > 0 && (
                <span className="text-zinc-600 truncate flex-1">
                  — {seg.content.trim().slice(0, 40)}
                  {seg.content.trim().length > 40 ? "…" : ""}
                </span>
              )}
            </summary>
            <div
              id={id}
              className="px-3 py-2 text-sm text-zinc-400 whitespace-pre-wrap border-t border-zinc-700 max-h-48 overflow-y-auto"
            >
              {seg.content.trim() || "—"}
            </div>
          </details>
        );
      })}
    </div>
  );
}
