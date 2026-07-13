import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Play, Loader2 } from "lucide-react";
import type { BacktestRunRequest, FillTiming, StrategyInfo, TickerInfo } from "../types";

interface Props {
  tickers: TickerInfo[];
  strategies: StrategyInfo[];
  loading: boolean;
  onSubmit: (req: BacktestRunRequest) => void;
}

function defaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 5);
  const toISO = (d: Date) => d.toISOString().slice(0, 10);
  return { start: toISO(start), end: toISO(end) };
}

export function StrategyForm({ tickers, strategies, loading, onSubmit }: Props) {
  const { start: defaultStart, end: defaultEnd } = useMemo(defaultDateRange, []);

  const [ticker, setTicker] = useState("AAPL");
  const [strategyId, setStrategyId] = useState("");
  const [params, setParams] = useState<Record<string, number>>({});
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(defaultEnd);
  const [initialCapital, setInitialCapital] = useState(100_000);
  const [commissionBps, setCommissionBps] = useState(5);
  const [slippageBps, setSlippageBps] = useState(5);
  const [fillTiming, setFillTiming] = useState<FillTiming>("next_open");

  // Once strategies load, select the first one and seed its default params.
  useEffect(() => {
    if (strategies.length > 0 && !strategyId) {
      const first = strategies[0];
      setStrategyId(first.id);
      setParams(Object.fromEntries(first.params.map((p) => [p.name, p.default])));
    }
  }, [strategies, strategyId]);

  const activeStrategy = strategies.find((s) => s.id === strategyId);

  function handleStrategyChange(id: string) {
    setStrategyId(id);
    const strat = strategies.find((s) => s.id === id);
    if (strat) {
      setParams(Object.fromEntries(strat.params.map((p) => [p.name, p.default])));
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ticker,
      strategy_id: strategyId,
      params,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      commission_bps: commissionBps,
      slippage_bps: slippageBps,
      fill_timing: fillTiming,
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="section-label">Instrument</div>
      <div className="field">
        <label className="field-label" htmlFor="ticker-select">
          Ticker
        </label>
        <select
          id="ticker-select"
          className="control"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
        >
          {tickers.map((t) => (
            <option key={t.symbol} value={t.symbol}>
              {t.symbol} — {t.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label className="field-label" htmlFor="start-date">
          Date range
        </label>
        <div className="field-row">
          <input
            id="start-date"
            type="date"
            className="control"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <input
            type="date"
            className="control"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>

      <hr className="divider" />

      <div className="section-label">Strategy</div>
      <div className="field">
        <label className="field-label" htmlFor="strategy-select">
          Rule set
        </label>
        <select
          id="strategy-select"
          className="control"
          value={strategyId}
          onChange={(e) => handleStrategyChange(e.target.value)}
        >
          {strategies.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {activeStrategy && <div className="strategy-description">{activeStrategy.description}</div>}

      {activeStrategy?.params.map((p) => (
        <div className="field" key={p.name}>
          <label className="field-label" htmlFor={`param-${p.name}`}>
            {p.label}
          </label>
          <div className="slider-row">
            <input
              id={`param-${p.name}`}
              type="range"
              min={p.min}
              max={p.max}
              step={p.step}
              value={params[p.name] ?? p.default}
              onChange={(e) =>
                setParams((prev) => ({ ...prev, [p.name]: Number(e.target.value) }))
              }
            />
            <span className="slider-value">
              {(params[p.name] ?? p.default).toString()}
              {p.name === "threshold_pct" ? "%" : ""}
            </span>
          </div>
        </div>
      ))}

      <hr className="divider" />

      <div className="section-label">Execution</div>

      <div className="field">
        <label className="field-label" htmlFor="capital">
          Initial capital (USD)
        </label>
        <input
          id="capital"
          type="number"
          className="control"
          min={1000}
          step={1000}
          value={initialCapital}
          onChange={(e) => setInitialCapital(Number(e.target.value))}
        />
      </div>

      <div className="field">
        <label className="field-label">Costs (bps, flat per trade)</label>
        <div className="field-row">
          <div>
            <label className="field-label" htmlFor="commission" style={{ fontSize: 11 }}>
              Commission
            </label>
            <input
              id="commission"
              type="number"
              className="control"
              min={0}
              max={500}
              step={0.5}
              value={commissionBps}
              onChange={(e) => setCommissionBps(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="field-label" htmlFor="slippage" style={{ fontSize: 11 }}>
              Slippage
            </label>
            <input
              id="slippage"
              type="number"
              className="control"
              min={0}
              max={500}
              step={0.5}
              value={slippageBps}
              onChange={(e) => setSlippageBps(Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      <div className="field">
        <label className="field-label" htmlFor="fill-timing">
          Fill timing
        </label>
        <select
          id="fill-timing"
          className="control"
          value={fillTiming}
          onChange={(e) => setFillTiming(e.target.value as FillTiming)}
        >
          <option value="next_open">Next bar open (no look-ahead)</option>
          <option value="same_close">Same bar close (simplified)</option>
        </select>
      </div>

      <button type="submit" className="btn-run" disabled={loading || !strategyId}>
        {loading ? <Loader2 size={16} className="spin" /> : <Play size={15} />}
        {loading ? "Running…" : "Run backtest"}
      </button>

      <p className="assumption-note">
        Long/flat only, single position, whole shares. Orders fill on the next bar's open by
        default; costs and slippage are flat bps assumptions applied to trade notional. See the
        README for the full list of assumptions.
      </p>
    </form>
  );
}
