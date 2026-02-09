"use client";

import { useState, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Dashboard } from "@/components/Dashboard";
import { GetAdviceButton } from "@/components/GetAdviceButton";
import { AdviceView } from "@/components/AdviceView";
import { Chat } from "@/components/Chat";
import { ResizableDivider } from "@/components/ResizableDivider";

const DEFAULT_SIDEBAR_WIDTH = 288;
const DEFAULT_CHAT_WIDTH = 420;
const MIN_PANEL_WIDTH = 180;
const MAX_SIDEBAR_WIDTH = 500;
const MAX_CHAT_WIDTH = 600;

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export default function Home() {
  const [selectedIsin, setSelectedIsin] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [adviceText, setAdviceText] = useState("");
  const [sessionMessages, setSessionMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [refreshSessions, setRefreshSessions] = useState(0);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);
  const [chatWidth, setChatWidth] = useState(DEFAULT_CHAT_WIDTH);

  const sidebarCollapsed = sidebarWidth <= 0;
  const chatCollapsed = chatWidth <= 0;

  const handleNewChat = useCallback(() => {
    setSessionId(null);
    setAdviceText("");
    setSessionMessages([]);
  }, []);

  const handleSelectSession = useCallback((id: number, isin: string) => {
    setSessionId(id);
    setSelectedIsin(isin);
    setAdviceText("");
    setSessionMessages([]);
  }, []);

  const handleAdviceStart = useCallback(() => {
    setAdviceText("");
  }, []);

  const handleAdviceChunk = useCallback((text: string) => {
    setAdviceText(text);
  }, []);

  const handleAdviceComplete = useCallback((newSessionId: number, text: string) => {
    setSessionId(newSessionId);
    setAdviceText(text);
    setSessionMessages([]);
    setRefreshSessions((n) => n + 1);
  }, []);

  const resizeSidebar = useCallback((deltaX: number) => {
    setSidebarWidth((w) => clamp(w + deltaX, 0, MAX_SIDEBAR_WIDTH));
  }, []);

  const resizeChat = useCallback((deltaX: number) => {
    setChatWidth((w) => clamp(w - deltaX, 0, MAX_CHAT_WIDTH));
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarWidth((w) => (w <= 0 ? DEFAULT_SIDEBAR_WIDTH : 0));
  }, []);

  const toggleChat = useCallback(() => {
    setChatWidth((w) => (w <= 0 ? DEFAULT_CHAT_WIDTH : 0));
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left: Sidebar (0 width when collapsed) */}
      <div
        className="flex shrink-0 flex-col h-screen bg-[var(--card)] border-r border-zinc-800 overflow-hidden"
        style={{
          width: sidebarCollapsed ? 0 : Math.max(MIN_PANEL_WIDTH, sidebarWidth),
          minWidth: sidebarCollapsed ? 0 : undefined,
        }}
      >
        {!sidebarCollapsed && (
          <Sidebar
            selectedIsin={selectedIsin}
            onSelectStock={setSelectedIsin}
            selectedSessionId={sessionId}
            onSelectSession={handleSelectSession}
            onNewChat={handleNewChat}
            refreshSessions={refreshSessions}
          />
        )}
      </div>

      <ResizableDivider
        onResize={resizeSidebar}
        toggleSide="left"
        collapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
        toggleLabel="Sidebar"
      />

      {/* Center: Main analytics */}
      <main className="flex-1 flex flex-col min-w-[200px] min-h-0">
        <header className="border-b border-zinc-800 px-4 py-2 flex items-center gap-4 shrink-0">
          {selectedIsin && (
            <>
              <span className="text-sm text-zinc-400">Stock: {selectedIsin}</span>
              <GetAdviceButton
                isin={selectedIsin}
                onAdviceStart={handleAdviceStart}
                onAdviceChunk={handleAdviceChunk}
                onAdviceComplete={handleAdviceComplete}
              />
            </>
          )}
        </header>
        <div className="flex-1 flex min-h-0 overflow-hidden">
          <div className="flex-1 overflow-auto flex flex-col min-w-0">
            <Dashboard isin={selectedIsin} />
            {adviceText && (
              <div className="px-6 pb-4">
                <AdviceView adviceText={adviceText} />
              </div>
            )}
          </div>

          <ResizableDivider
            onResize={resizeChat}
            toggleSide="right"
            collapsed={chatCollapsed}
            onToggle={toggleChat}
            toggleLabel="Chat"
          />
          <div
            className="flex shrink-0 flex-col min-h-0 bg-zinc-950 border-l border-zinc-800 overflow-hidden"
            style={{
              width: chatCollapsed ? 0 : Math.max(MIN_PANEL_WIDTH, chatWidth),
              minWidth: chatCollapsed ? 0 : undefined,
            }}
          >
            {!chatCollapsed && (
              <div className="flex flex-col h-full min-h-0">
                <Chat
                  sessionId={sessionId}
                  initialMessages={sessionMessages}
                  initialAdvice={adviceText}
                  onSessionLoaded={setSessionMessages}
                />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
