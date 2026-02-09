"use client";

import { MessageContent } from "@/components/MessageContent";

type Props = {
  adviceText: string;
};

export function AdviceView({ adviceText }: Props) {
  if (!adviceText) return null;
  return (
    <div className="p-4 rounded-lg bg-[var(--card)] border border-zinc-800 prose prose-invert prose-sm max-w-none">
      <h3 className="text-lg font-semibold text-zinc-200 mb-2">Financial advice</h3>
      <div className="text-zinc-300 text-sm leading-relaxed">
        <MessageContent content={adviceText} />
      </div>
    </div>
  );
}
