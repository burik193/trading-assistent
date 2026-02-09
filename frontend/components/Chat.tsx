"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { sendChatMessage, fetchSession } from "@/lib/api";
import { MessageContent } from "@/components/MessageContent";

type Message = { role: string; content: string };

type Props = {
  sessionId: number | null;
  initialMessages?: Message[];
  initialAdvice?: string;
  onSessionLoaded?: (messages: Message[]) => void;
};

export function Chat({
  sessionId,
  initialMessages = [],
  initialAdvice = "",
  onSessionLoaded,
}: Props) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const loadSession = useCallback(() => {
    if (!sessionId) return;
    fetchSession(sessionId)
      .then((s) => {
        const msgs = (s.messages || []).map((m: { role: string; content: string }) => ({
          role: m.role,
          content: m.content,
        }));
        setMessages(msgs);
        onSessionLoaded?.(msgs);
      })
      .catch(console.error);
  }, [sessionId, onSessionLoaded]);

  useEffect(() => {
    if (sessionId && !initialAdvice) {
      loadSession();
    }
  }, [sessionId, initialAdvice]);

  const sendMessage = useCallback(() => {
    if (!sessionId || !input.trim()) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setStreaming(true);
    setStreamText("");
    sendChatMessage(sessionId, userMessage).then((r) => {
      if (!r.ok || !r.body) {
        setStreaming(false);
        return;
      }
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let rawBuffer = "";
      let replyContent = "";
      const read = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            setStreaming(false);
            setMessages((prev) => [...prev, { role: "assistant", content: replyContent }]);
            return;
          }
          rawBuffer += decoder.decode(value, { stream: true });
          const blocks = rawBuffer.split("\n\n");
          rawBuffer = blocks.pop() || "";
          for (const block of blocks) {
            const lines = block.split("\n");
            let dataLine = "";
            for (const line of lines) {
              if (line.startsWith("data: ")) dataLine = line.slice(6);
            }
            if (dataLine) {
              try {
                const d = JSON.parse(dataLine) as { text?: string };
                if (typeof d.text === "string") {
                  replyContent += d.text;
                  setStreamText(replyContent);
                }
              } catch (_) {}
            }
          }
          read();
        });
      };
      read();
    });
  }, [sessionId, input]);

  if (!sessionId) {
    return (
      <div className="p-4 text-zinc-500 text-sm">
        Run &quot;Get financial advice&quot; to open chat for this stock.
      </div>
    );
  }

  const displayMessages = [...messages];
  if (streaming && streamText) {
    displayMessages.push({ role: "assistant", content: streamText });
  }

  return (
    <div className="flex flex-col h-full border-t border-zinc-800">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {initialAdvice && messages.length === 0 && !streamText && (
          <div className="rounded-lg bg-[var(--card)] p-3 border border-zinc-800">
            <p className="text-xs text-zinc-500 mb-1">Advice</p>
            <div className="text-sm text-zinc-300">
              <MessageContent content={initialAdvice} />
            </div>
          </div>
        )}
        {displayMessages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-zinc-700 text-zinc-100"
                  : "bg-[var(--card)] border border-zinc-800 text-zinc-300"
              }`}
            >
              {m.role === "assistant" ? (
                <MessageContent content={m.content} />
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="p-3 border-t border-zinc-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a follow-up..."
            className="flex-1 py-2 px-3 rounded-lg bg-zinc-800 border border-zinc-700 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            disabled={streaming}
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="py-2 px-4 rounded-lg bg-zinc-600 hover:bg-zinc-500 disabled:opacity-50 text-sm font-medium"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
