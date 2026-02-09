"use client";

import { useEffect, useState, useRef } from "react";
import type { Stock, Session } from "@/lib/api";
import { fetchStocks, fetchSessions } from "@/lib/api";

type Props = {
  selectedIsin: string | null;
  onSelectStock: (isin: string) => void;
  selectedSessionId: number | null;
  onSelectSession: (sessionId: number, isin: string) => void;
  onNewChat: () => void;
  refreshSessions?: boolean;
};

export function Sidebar({
  selectedIsin,
  onSelectStock,
  selectedSessionId,
  onSelectSession,
  onNewChat,
  refreshSessions,
}: Props) {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoadError(null);
    Promise.all([fetchStocks(), fetchSessions()])
      .then(([s, sess]) => {
        setStocks(Array.isArray(s) ? s : []);
        setSessions(Array.isArray(sess) ? sess : []);
      })
      .catch((err) => {
        setLoadError(err instanceof Error ? err.message : "Could not load stocks");
        setStocks([]);
        setSessions([]);
      })
      .finally(() => setLoading(false));
  }, [refreshSessions]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredStocks = search
    ? stocks.filter(
        (s) =>
          s.name.toLowerCase().includes(search.toLowerCase()) ||
          (s.symbol && s.symbol.toLowerCase().includes(search.toLowerCase())) ||
          s.isin.toLowerCase().includes(search.toLowerCase())
      )
    : stocks.slice(0, 300);

  const selectedStock = stocks.find((s) => s.isin === selectedIsin);
  const displayValue = selectedStock
    ? `${selectedStock.name}${selectedStock.symbol ? ` (${selectedStock.symbol})` : ""}`
    : "Select a stock...";

  return (
    <aside className="w-full min-w-0 border-r border-zinc-800 flex flex-col h-screen bg-[var(--card)]">
      <div className="p-3 border-b border-zinc-800">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full py-2 px-3 rounded-lg bg-zinc-700 hover:bg-zinc-600 text-sm font-medium"
        >
          New chat
        </button>
      </div>
      <div className="p-2 flex-1 overflow-hidden flex flex-col">
        <label className="text-xs text-zinc-500 mb-1 block">Stock</label>
        <div className="relative" ref={dropdownRef} data-testid="stock-dropdown">
          <button
            type="button"
            onClick={() => setDropdownOpen((o) => !o)}
            className="w-full py-2 px-3 rounded-lg bg-zinc-800 border border-zinc-700 text-left text-sm text-zinc-200 hover:bg-zinc-700 focus:outline-none focus:ring-1 focus:ring-zinc-500 flex items-center justify-between gap-2"
            data-testid="stock-dropdown-trigger"
            aria-expanded={dropdownOpen}
            aria-haspopup="listbox"
          >
            <span className="truncate">{displayValue}</span>
            <span className="text-zinc-500 shrink-0" aria-hidden>
              {dropdownOpen ? "▲" : "▼"}
            </span>
          </button>
          {dropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 rounded-lg border border-zinc-700 bg-zinc-900 shadow-lg z-50 max-h-80 flex flex-col">
              <div className="p-2 border-b border-zinc-700">
                <input
                  type="text"
                  placeholder="Search stocks..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full py-1.5 px-2 rounded bg-zinc-800 border border-zinc-700 text-sm placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                  autoFocus
                />
              </div>
              {loading ? (
                <p className="p-3 text-zinc-500 text-sm">Loading...</p>
              ) : loadError ? (
                <p className="p-3 text-amber-400 text-sm">{loadError}</p>
              ) : filteredStocks.length === 0 ? (
                <div className="p-3 text-zinc-500 text-sm space-y-1">
                  <p>{search ? "No stocks match your search." : "No stocks in database."}</p>
                  {!search && (
                    <p className="text-zinc-600 text-xs">
                      Run migrations from project root: <code className="bg-zinc-800 px-1 rounded">cd backend && alembic upgrade head</code>
                    </p>
                  )}
                </div>
              ) : (
                <ul className="overflow-y-auto flex-1 p-1 min-h-0" role="listbox" data-testid="stock-list">
                  {filteredStocks.map((s) => (
                    <li key={s.isin} role="option">
                      <button
                        type="button"
                        onClick={() => {
                          onSelectStock(s.isin);
                          setDropdownOpen(false);
                        }}
                        className={`w-full text-left py-2 px-2 rounded text-sm truncate block ${
                          selectedIsin === s.isin ? "bg-zinc-700 text-white" : "hover:bg-zinc-800 text-zinc-300"
                        }`}
                      >
                        {s.name} {s.symbol && <span className="text-zinc-500">({s.symbol})</span>}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
        <div className="mt-4 pt-2 border-t border-zinc-800">
          <label className="text-xs text-zinc-500 mb-1 block">Past chats</label>
          <ul className="space-y-0.5 max-h-40 overflow-y-auto">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => onSelectSession(s.id, s.isin)}
                  className={`w-full text-left py-1.5 px-2 rounded text-sm truncate ${
                    selectedSessionId === s.id ? "bg-zinc-700" : "hover:bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {s.title || `Session ${s.id}`}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </aside>
  );
}
