"use client";

import { useState, useCallback } from "react";
import { adviceStreamUrl } from "@/lib/api";

type ProgressStep = {
  step: string;
  stepIndex: number;
  totalSteps: number;
  percent: number;
  status: string;
  message?: string;
};

type Props = {
  isin: string | null;
  onAdviceStart?: () => void;
  onAdviceChunk?: (accumulatedText: string) => void;
  onAdviceComplete: (sessionId: number, adviceText: string) => void;
};

export function GetAdviceButton({ isin, onAdviceStart, onAdviceChunk, onAdviceComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const [percent, setPercent] = useState(0);
  const [steps, setSteps] = useState<ProgressStep[]>([]);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runAdvice = useCallback(() => {
    if (!isin) return;
    setLoading(true);
    setPercent(0);
    setSteps([]);
    setCurrentStep(null);
    setError(null);
    onAdviceStart?.();
    const url = adviceStreamUrl(isin);
    let adviceText = "";

    fetch(url, { method: "POST" })
      .then((r) => {
        if (!r.ok || !r.body) throw new Error("Request failed");
        const reader = r.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let eventType = "";
        const read = () => {
          reader.read().then(({ done, value }) => {
            if (done) {
              setLoading(false);
              return;
            }
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split("\n\n");
            buffer = parts.pop() || "";
            for (const block of parts) {
              const lines = block.split("\n");
              for (const line of lines) {
                if (line.startsWith("event: ")) eventType = line.slice(7).trim();
                else if (line.startsWith("data: ") && eventType) {
                  try {
                    const d = JSON.parse(line.slice(6));
                    if (eventType === "progress") {
                      setPercent(d.percent ?? 0);
                      setCurrentStep(d.step ?? null);
                      setSteps((prev) => {
                        const next = [...prev];
                        const idx = next.findIndex((s) => s.step === d.step && s.stepIndex === d.stepIndex);
                        if (idx >= 0) next[idx] = d;
                        else next.push(d);
                        return next;
                      });
                    } else if (eventType === "step_failed") {
                      setSteps((prev) => [...prev, { step: d.step, stepIndex: prev.length, totalSteps: 10, percent: 0, status: "failed", message: d.message }]);
                    } else if (eventType === "advice_chunk") {
                      const chunk = d.text ?? "";
                      adviceText += chunk;
                      onAdviceChunk?.(adviceText);
                    } else if (eventType === "done") {
                      setLoading(false);
                      setPercent(100);
                      if (d.success && d.sessionId != null) {
                        onAdviceComplete(d.sessionId, adviceText);
                      } else {
                        setError("Advice pipeline failed or did not return a session.");
                      }
                    }
                  } catch (_) {}
                }
              }
            }
            read();
          });
        };
        read();
      })
      .catch((e) => {
        setLoading(false);
        setError(e instanceof Error ? e.message : "Connection error");
      });
  }, [isin, onAdviceStart, onAdviceChunk, onAdviceComplete]);

  if (!isin) return null;

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={runAdvice}
        disabled={loading}
        className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        {loading ? "Running..." : "Get financial advice"}
      </button>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {loading && (
        <div className="space-y-2">
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-600 transition-all duration-300"
              style={{ width: `${percent}%` }}
            />
          </div>
          <p className="text-sm text-zinc-400">
            {currentStep || "Starting..."} — {percent}%
          </p>
          <ul className="text-xs space-y-1 max-h-32 overflow-y-auto">
            {steps.map((s, i) => (
              <li
                key={`${s.step}-${i}`}
                className={s.status === "failed" ? "text-red-400" : "text-zinc-500"}
              >
                {s.status === "failed" ? "✗ " : "✓ "}
                {s.step}
                {s.message && ` — ${s.message}`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
