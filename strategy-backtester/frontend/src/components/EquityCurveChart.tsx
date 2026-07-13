import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipContentProps } from "recharts";
import type { EquityPoint } from "../types";

interface Props {
  equityCurve: EquityPoint[];
  initialCapital: number;
}

interface ChartRow extends EquityPoint {
  drawdownPct: number;
}

function withDrawdown(points: EquityPoint[]): ChartRow[] {
  let peak = -Infinity;
  return points.map((p) => {
    peak = Math.max(peak, p.equity);
    const drawdownPct = peak > 0 ? (p.equity / peak - 1) * 100 : 0;
    return { ...p, drawdownPct };
  });
}

function formatTick(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function formatCurrency(v: number): string {
  if (Math.abs(v) >= 1000) return `$${(v / 1000).toFixed(0)}k`;
  return `$${v.toFixed(0)}`;
}

function ChartTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0].payload as ChartRow;
  return (
    <div
      style={{
        background: "var(--surface-raised)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        padding: "10px 12px",
        fontSize: 12,
        fontFamily: "var(--font-mono)",
        boxShadow: "var(--shadow-panel)",
      }}
    >
      <div style={{ color: "var(--text-tertiary)", marginBottom: 4 }}>{row.date}</div>
      <div style={{ color: "var(--text-primary)" }}>
        Equity: ${row.equity.toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </div>
      <div style={{ color: row.drawdownPct < -0.01 ? "var(--loss)" : "var(--text-secondary)" }}>
        Drawdown: {row.drawdownPct.toFixed(2)}%
      </div>
      <div style={{ color: "var(--text-tertiary)" }}>Shares held: {row.shares}</div>
    </div>
  );
}

export function EquityCurveChart({ equityCurve, initialCapital }: Props) {
  const data = useMemo(() => withDrawdown(equityCurve), [equityCurve]);
  const minDrawdown = useMemo(
    () => Math.min(0, ...data.map((d) => d.drawdownPct)),
    [data]
  );

  // Sample tick indices so the X axis doesn't try to render one label per day.
  const tickIndices = useMemo(() => {
    const target = 7;
    const step = Math.max(1, Math.floor(data.length / target));
    const idx: string[] = [];
    for (let i = 0; i < data.length; i += step) idx.push(data[i].date);
    return idx;
  }, [data]);

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border-subtle)" vertical={false} />
          <XAxis
            dataKey="date"
            ticks={tickIndices}
            tickFormatter={formatTick}
            tick={{ fill: "var(--text-tertiary)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: "var(--text-tertiary)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={false}
            tickLine={false}
            width={52}
            domain={["auto", "auto"]}
          />
          <Tooltip content={ChartTooltip} />
          <Area
            type="monotone"
            dataKey="equity"
            stroke="var(--accent)"
            strokeWidth={1.75}
            fill="url(#equityGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div style={{ marginTop: 2 }}>
        <ResponsiveContainer width="100%" height={72}>
          <AreaChart data={data} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="date" hide />
            <YAxis hide domain={[minDrawdown, 0]} />
            <Area
              type="monotone"
              dataKey="drawdownPct"
              stroke="var(--loss)"
              strokeWidth={1}
              fill="var(--loss)"
              fillOpacity={0.22}
            />
          </AreaChart>
        </ResponsiveContainer>
        <div
          className="mono text-tertiary"
          style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", marginTop: 2 }}
        >
          Drawdown
        </div>
      </div>

      <p className="text-tertiary" style={{ fontSize: 11.5, marginTop: 14 }}>
        Started at ${initialCapital.toLocaleString()}. Marked to market at each day's close.
      </p>
    </div>
  );
}
