import type { Metrics } from "../types";

function fmtPct(v: number): string {
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

function signClass(v: number): string {
  if (v > 0) return "gain";
  if (v < 0) return "loss";
  return "";
}

export function MetricsReadout({ metrics }: { metrics: Metrics }) {
  const cells: { label: string; value: string; cls: string }[] = [
    { label: "Total Return", value: fmtPct(metrics.total_return_pct), cls: signClass(metrics.total_return_pct) },
    { label: "CAGR", value: fmtPct(metrics.cagr_pct), cls: signClass(metrics.cagr_pct) },
    { label: "Sharpe Ratio", value: metrics.sharpe_ratio.toFixed(2), cls: signClass(metrics.sharpe_ratio) },
    { label: "Max Drawdown", value: fmtPct(metrics.max_drawdown_pct), cls: "loss" },
    { label: "Volatility (ann.)", value: `${metrics.volatility_pct.toFixed(2)}%`, cls: "" },
    { label: "Win Rate", value: `${metrics.win_rate_pct.toFixed(1)}% (${metrics.num_trades})`, cls: "" },
  ];

  return (
    <div className="readout-strip fade-in">
      {cells.map((c) => (
        <div className="readout-cell" key={c.label}>
          <div className="readout-label">{c.label}</div>
          <div className={`readout-value ${c.cls}`}>{c.value}</div>
        </div>
      ))}
    </div>
  );
}
