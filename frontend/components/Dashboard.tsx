"use client";

import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { fetchSeries, fetchMetrics } from "@/lib/api";
import type { SeriesResponse, TrendPoint } from "@/lib/api";

type Props = {
  isin: string | null;
};

type RangeKey = "1D" | "5D" | "1M" | "3M" | "1Y";

const RANGES: { label: string; value: RangeKey }[] = [
  { label: "1D", value: "1D" },
  { label: "5D", value: "5D" },
  { label: "1M", value: "1M" },
  { label: "3M", value: "3M" },
  { label: "1Y", value: "1Y" },
];

function rangeToApiInterval(_range: RangeKey): string {
  return "1d";
}

function sliceSeriesByRange<T extends { time: string }>(series: T[], range: RangeKey): T[] {
  if (series.length === 0) return series;
  const n = range === "1D" ? 1 : range === "5D" ? 5 : range === "1M" ? 21 : range === "3M" ? 63 : 252;
  return series.slice(-n);
}

export function Dashboard({ isin }: Props) {
  const [series, setSeries] = useState<Array<{ time: string; close?: number; volume?: number }>>([]);
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);
  const [range, setRange] = useState<RangeKey>("1M");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forecastData, setForecastData] = useState<SeriesResponse | null>(null);

  useEffect(() => {
    if (!isin) {
      setSeries([]);
      setMetrics(null);
      setForecastData(null);
      return;
    }
    setLoading(true);
    setError(null);
    const intervalKey = rangeToApiInterval(range);
    const includeForecast = range === "1Y" || range === "3M" || range === "1M";
    Promise.all([fetchSeries(isin, intervalKey, includeForecast), fetchMetrics(isin)])
      .then(([s, m]) => {
        const raw = (s.series || []).map((d) => ({ ...d, time: d.time?.slice(0, 10) || "" }));
        const sliced = sliceSeriesByRange(raw, range);
        setSeries(sliced);
        setMetrics(m);
        setForecastData(s);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [isin, range]);

  // All hooks must run before any early return (React rules of hooks)
  const chartData = useMemo(() => {
    if (!series.length) return [];
    const hasForecast = forecastData?.forecast?.length && forecastData?.trend_line?.length;
    const base = series.map((d) => ({
      time: d.time,
      close: d.close ?? null,
      trend: null as number | null,
      upper: null as number | null,
      lower: null as number | null,
      isForecast: false,
    }));
    if (hasForecast && forecastData) {
      const trendByTime = new Map<string, number>();
      (forecastData.trend_line as TrendPoint[]).forEach((p) => trendByTime.set(p.time, p.value));
      (forecastData.upper_band as TrendPoint[] || []).forEach((p) => {
        const b = base.find((d) => d.time === p.time);
        if (b) b.upper = p.value;
      });
      (forecastData.lower_band as TrendPoint[] || []).forEach((p) => {
        const b = base.find((d) => d.time === p.time);
        if (b) b.lower = p.value;
      });
      base.forEach((d) => { d.trend = trendByTime.get(d.time) ?? null; });
      const forecastPoints = (forecastData.forecast || []).map((p) => ({
        time: p.time,
        close: p.close,
        trend: null,
        upper: null,
        lower: null,
        isForecast: true,
      }));
      return [...base, ...forecastPoints];
    }
    return base.map((d) => ({ ...d, trend: null, upper: null, lower: null, isForecast: false }));
  }, [series, forecastData]);

  const hasPrognosis = chartData.some((d) => d.isForecast) && forecastData?.forecast_stats;

  if (!isin) {
    return (
      <div className="p-6 text-zinc-500 text-center">
        Select a stock from the sidebar to see the dashboard.
      </div>
    );
  }

  const metricEntries = metrics
    ? Object.entries(metrics).filter(
        ([k, v]) =>
          v != null &&
          v !== "" &&
          !["Symbol", "Name", "Description", "AssetType", "Exchange", "AssetClass"].includes(k)
      )
    : [];

  const noKpis = !loading && series.length === 0 && (!metrics || metricEntries.length === 0);
  const showWarningBox = error || noKpis;
  const defaultWarningMessage =
    "Data temporarily unavailable. Some metrics or series could not be loaded. Please try again later.";

  return (
    <div className="p-6 space-y-6">
      <div className="flex gap-2 flex-wrap">
        {RANGES.map((r) => (
          <button
            key={r.label}
            type="button"
            onClick={() => setRange(r.value)}
            className={`px-3 py-1.5 rounded text-sm ${
              range === r.value ? "bg-zinc-600 text-white" : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>
      {showWarningBox && (
        <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4 text-amber-200 text-sm">
          {defaultWarningMessage}
        </div>
      )}
      {error && !showWarningBox && <p className="text-red-400 text-sm">{error}</p>}
      {error && showWarningBox && error.toLowerCase().includes("network") && (
        <p className="text-red-400 text-sm">{error}</p>
      )}
      {loading && <p className="text-zinc-500">Loading...</p>}
      {!loading && series.length > 0 && (
        <div className="space-y-4">
          <div className="h-80 bg-[var(--card)] rounded-lg p-4 border border-zinc-800">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                <XAxis dataKey="time" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} domain={["auto", "auto"]} />
                <Tooltip
                  contentStyle={{ background: "#27272a", border: "1px solid #3f3f46" }}
                  labelStyle={{ color: "#a1a1aa" }}
                />
                <Line type="monotone" dataKey="close" stroke="#22c55e" strokeWidth={2} dot={false} name="Close" />
                <Line type="monotone" dataKey="trend" stroke="#a78bfa" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Trend" />
                <Line type="monotone" dataKey="upper" stroke="#3b82f6" strokeWidth={1} strokeOpacity={0.6} dot={false} name="+2σ" />
                <Line type="monotone" dataKey="lower" stroke="#3b82f6" strokeWidth={1} strokeOpacity={0.6} dot={false} name="-2σ" />
                <Legend />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {hasPrognosis && forecastData?.forecast_stats && (
            <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
              <h3 className="text-sm font-medium text-zinc-300 mb-2">Near-term prognosis (next 3 trading days)</h3>
              <p className="text-zinc-400 text-sm mb-2">
                Linear trend and ±2σ band from last {series.length} days. Forecast: extrapolated trend.
              </p>
              <ul className="text-sm text-zinc-400 space-y-1">
                {(forecastData.forecast || []).map((p, i) => (
                  <li key={p.time}>
                    <span className="text-amber-400">{p.time}</span>: {typeof p.close === "number" ? p.close.toFixed(2) : p.close}
                  </li>
                ))}
              </ul>
              {forecastData.forecast_stats.std != null && (
                <p className="text-xs text-zinc-500 mt-2">
                  Std dev: {Number(forecastData.forecast_stats.std).toFixed(2)} · Slope: {Number(forecastData.forecast_stats.slope ?? 0).toFixed(4)}
                </p>
              )}
            </div>
          )}
        </div>
      )}
      {metrics && metricEntries.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {metricEntries.map(([key, value]) => {
            const { label, formatted } = formatMetric(key, value);
            const num = typeof value === "number";
            const isPositive = num && value > 0;
            const isNegative = num && value < 0;
            return (
              <div
                key={key}
                className="bg-[var(--card)] rounded-lg p-3 border border-zinc-800"
              >
                <p className="text-xs text-zinc-500 truncate" title={key}>
                  {label}
                </p>
                <p
                  className={`text-sm font-medium mt-0.5 break-all ${
                    isPositive ? "text-green-400" : isNegative ? "text-red-400" : "text-zinc-300"
                  }`}
                >
                  {formatted}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const KPI_LABELS: Record<string, string> = {
  MarketCapitalization: "Market Cap",
  PERatio: "P/E Ratio",
  EPS: "EPS",
  "52WeekHigh": "52W High",
  "52WeekLow": "52W Low",
  Beta: "Beta",
  DividendYield: "Div Yield",
  DividendPerShare: "Div/Share",
  RevenuePerShareTTM: "Revenue/Share (TTM)",
  ProfitMargin: "Profit Margin",
  OperatingMarginTTM: "Operating Margin",
  ReturnOnAssetsTTM: "ROA",
  ReturnOnEquityTTM: "ROE",
  RevenueTTM: "Revenue (TTM)",
  GrossProfitTTM: "Gross Profit (TTM)",
  DilutedEPSTTM: "Diluted EPS (TTM)",
  QuarterlyEarningsGrowthYOY: "Earnings Growth (YOY)",
  QuarterlyRevenueGrowthYOY: "Revenue Growth (YOY)",
  TrailingPE: "Trailing P/E",
  ForwardPE: "Forward P/E",
  PEGRatio: "PEG Ratio",
  PriceToSalesRatioTTM: "Price/Sales",
  PriceToBookRatio: "P/B",
  RevenueGrowthYOY: "Revenue Growth (YOY)",
  EVToRevenue: "EV/Revenue",
  EVToEBITDA: "EV/EBITDA",
  SharesOutstanding: "Shares Out",
  BookValue: "Book Value",
  Sector: "Sector",
  Industry: "Industry",
  Country: "Country",
  FiscalYearEnd: "Fiscal Year End",
  LatestQuarter: "Latest Quarter",
  EBITDA: "EBITDA",
  AnalystTargetPrice: "Target Price",
  ShortRatio: "Short Ratio",
  ShortPercentOutstanding: "Short %",
  LongBusinessSummary: "Summary",
  NetAssets: "Net Assets",
  ExpenseRatio: "Expense Ratio",
  Yield: "Yield",
  TotalAssets: "Total Assets",
};

function formatMetric(key: string, value: unknown): { label: string; formatted: string } {
  const label = KPI_LABELS[key] || key.replace(/([A-Z])/g, " $1").replace(/^./, (s) => s.toUpperCase()).trim();
  if (value == null || value === "") return { label, formatted: "—" };
  if (typeof value === "boolean") return { label, formatted: value ? "Yes" : "No" };
  if (typeof value !== "number" && typeof value !== "string") return { label, formatted: String(value) };
  const num = typeof value === "number" ? value : parseFloat(String(value));
  if (!Number.isFinite(num)) return { label, formatted: String(value) };
  if (key === "MarketCapitalization" || key === "SharesOutstanding" || key === "RevenueTTM" || key === "GrossProfitTTM" || key === "EBITDA" || key === "BookValue" || key === "NetAssets" || key === "TotalAssets") {
    return { label, formatted: formatCompactNumber(num) };
  }
  const pctKeys = ["DividendYield", "ProfitMargin", "OperatingMarginTTM", "ReturnOnAssetsTTM", "ReturnOnEquityTTM", "ShortPercentOutstanding", "ExpenseRatio", "Yield", "QuarterlyEarningsGrowthYOY", "QuarterlyRevenueGrowthYOY"];
  if (pctKeys.includes(key)) {
    const pct = num <= 1 && num >= -1 ? num * 100 : num;
    return { label, formatted: `${pct.toFixed(2)}%` };
  }
  if (key === "LatestQuarter" || key === "FiscalYearEnd" || (typeof value === "string" && value.length <= 20)) {
    return { label, formatted: String(value) };
  }
  if (Number.isInteger(num) && Math.abs(num) >= 1000) {
    return { label, formatted: formatCompactNumber(num) };
  }
  if (num !== 0 && Math.abs(num) < 0.01) return { label, formatted: num.toExponential(2) };
  if (Number.isInteger(num)) return { label, formatted: String(num) };
  return { label, formatted: num.toFixed(2) };
}

function formatCompactNumber(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1e12) return (n / 1e12).toFixed(2) + " T";
  if (abs >= 1e9) return (n / 1e9).toFixed(2) + " B";
  if (abs >= 1e6) return (n / 1e6).toFixed(2) + " M";
  if (abs >= 1e3) return (n / 1e3).toFixed(2) + " K";
  return n.toFixed(2);
}
