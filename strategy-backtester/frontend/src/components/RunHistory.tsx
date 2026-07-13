import { History } from "lucide-react";
import type { BacktestRunSummary } from "../types";

interface Props {
  runs: BacktestRunSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function RunHistory({ runs, selectedId, onSelect }: Props) {
  if (runs.length === 0) {
    return (
      <div className="empty-state">
        <History size={28} className="empty-state-icon" />
        <p>No backtests run yet.</p>
        <p className="text-tertiary" style={{ fontSize: 12 }}>
          Configure a strategy on the left and run one to see it here.
        </p>
      </div>
    );
  }

  return (
    <div className="history-list">
      {runs.map((r) => {
        const ret = r.total_return_pct ?? 0;
        return (
          <button
            key={r.id}
            className={`history-row ${r.id === selectedId ? "selected" : ""}`}
            onClick={() => onSelect(r.id)}
            type="button"
          >
            <span className="history-ticker">{r.ticker}</span>
            <span className="history-meta">
              {r.strategy_name} · {r.start_date} → {r.end_date}
            </span>
            <span
              className="history-return mono"
              style={{ color: ret > 0 ? "var(--gain)" : ret < 0 ? "var(--loss)" : "var(--text-secondary)" }}
            >
              {ret > 0 ? "+" : ""}
              {ret.toFixed(1)}%
            </span>
            <span className="text-tertiary mono" style={{ fontSize: 11 }}>
              #{r.id}
            </span>
          </button>
        );
      })}
    </div>
  );
}
