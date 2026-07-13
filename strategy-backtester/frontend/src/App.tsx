import { useEffect, useState } from "react";
import { AlertTriangle, LineChart } from "lucide-react";
import { fetchRunHistory, fetchRunResult, fetchStrategies, fetchTickers, runBacktest } from "./api";
import { StrategyForm } from "./components/StrategyForm";
import { MetricsReadout } from "./components/MetricsReadout";
import { EquityCurveChart } from "./components/EquityCurveChart";
import { TradesTable } from "./components/TradesTable";
import { RunHistory } from "./components/RunHistory";
import type {
  BacktestRunRequest,
  BacktestRunResponse,
  BacktestRunSummary,
  StrategyInfo,
  TickerInfo,
} from "./types";
import { ApiError } from "./types";

type Tab = "results" | "history";

export default function App() {
  const [tickers, setTickers] = useState<TickerInfo[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [runHistory, setRunHistory] = useState<BacktestRunSummary[]>([]);
  const [currentRun, setCurrentRun] = useState<BacktestRunResponse | null>(null);

  const [tab, setTab] = useState<Tab>("results");
  const [loading, setLoading] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const [t, s, h] = await Promise.all([fetchTickers(), fetchStrategies(), fetchRunHistory()]);
        setTickers(t);
        setStrategies(s);
        setRunHistory(h);
      } catch (err) {
        setInitError(
          err instanceof ApiError
            ? `Could not reach the API (${err.message}). Is the backend running on the expected URL?`
            : "Could not reach the API. Is the backend running? See the README for setup."
        );
      }
    }
    init();
  }, []);

  async function handleSubmit(req: BacktestRunRequest) {
    setLoading(true);
    setRunError(null);
    try {
      const result = await runBacktest(req);
      setCurrentRun(result);
      setTab("results");
      fetchRunHistory().then(setRunHistory).catch(() => {});
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "The backtest failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectRun(id: number) {
    setRunError(null);
    try {
      const result = await fetchRunResult(id);
      setCurrentRun(result);
      setTab("results");
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "Could not load that run.");
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="wordmark">
          <span className="wordmark-mark">
            <LineChart size={18} strokeWidth={2.25} />
          </span>
          BACKTEST.ENGINE
          <span className="wordmark-tagline">rule-based strategy simulation, 30-stock US equity universe</span>
        </div>
      </header>

      <div className="app-body">
        <aside className="rail">
          {initError ? (
            <div className="error-banner">
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
              <span>{initError}</span>
            </div>
          ) : (
            <StrategyForm tickers={tickers} strategies={strategies} loading={loading} onSubmit={handleSubmit} />
          )}
        </aside>

        <main className="main">
          <div className="tabs" style={{ marginBottom: 20 }}>
            <button className={`tab ${tab === "results" ? "active" : ""}`} onClick={() => setTab("results")}>
              Results
            </button>
            <button className={`tab ${tab === "history" ? "active" : ""}`} onClick={() => setTab("history")}>
              History {runHistory.length > 0 ? `(${runHistory.length})` : ""}
            </button>
          </div>

          {tab === "results" && (
            <>
              {runError && (
                <div className="error-banner">
                  <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
                  <span>{runError}</span>
                </div>
              )}

              {currentRun ? (
                <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                  <MetricsReadout metrics={currentRun.metrics} />

                  <div className="panel">
                    <div className="panel-header">
                      <div className="panel-title">
                        {currentRun.ticker} · {currentRun.strategy_name}
                      </div>
                      <div className="text-tertiary mono" style={{ fontSize: 11 }}>
                        {currentRun.start_date} → {currentRun.end_date} · {currentRun.fill_timing}
                      </div>
                    </div>
                    <div className="panel-body">
                      <EquityCurveChart
                        equityCurve={currentRun.equity_curve}
                        initialCapital={currentRun.initial_capital}
                      />
                    </div>
                  </div>

                  <div className="panel">
                    <div className="panel-header">
                      <div className="panel-title">Trades</div>
                      <div className="text-tertiary mono" style={{ fontSize: 11 }}>
                        {currentRun.trades.length} fills
                      </div>
                    </div>
                    <TradesTable trades={currentRun.trades} />
                  </div>
                </div>
              ) : (
                !runError && (
                  <div className="empty-state">
                    <LineChart size={28} className="empty-state-icon" />
                    <p>Configure a strategy on the left and run a backtest to see results here.</p>
                  </div>
                )
              )}
            </>
          )}

          {tab === "history" && (
            <div className="panel fade-in">
              <RunHistory runs={runHistory} selectedId={currentRun?.id ?? null} onSelect={handleSelectRun} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
