export interface TickerInfo {
  symbol: string;
  name: string;
  sector: string;
}

export interface StrategyParamSchema {
  name: string;
  label: string;
  type: "int" | "float";
  default: number;
  min: number;
  max: number;
  step: number;
}

export interface StrategyInfo {
  id: string;
  name: string;
  description: string;
  params: StrategyParamSchema[];
}

export type FillTiming = "next_open" | "same_close";

export interface BacktestRunRequest {
  ticker: string;
  strategy_id: string;
  params: Record<string, number>;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_bps: number;
  slippage_bps: number;
  fill_timing: FillTiming;
}

export interface Metrics {
  total_return_pct: number;
  cagr_pct: number;
  volatility_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  num_trades: number;
}

export interface EquityPoint {
  date: string;
  equity: number;
  cash: number;
  position_value: number;
  shares: number;
}

export interface Trade {
  date: string;
  side: "BUY" | "SELL";
  shares: number;
  price: number;
  commission: number;
  value: number;
}

export interface BacktestRunResponse {
  id: number;
  ticker: string;
  strategy_id: string;
  strategy_name: string;
  params: Record<string, number>;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_bps: number;
  slippage_bps: number;
  fill_timing: FillTiming;
  created_at: string;
  status: string;
  error_message?: string | null;
  metrics: Metrics;
  equity_curve: EquityPoint[];
  trades: Trade[];
}

export interface BacktestRunSummary {
  id: number;
  ticker: string;
  strategy_id: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  created_at: string;
  status: string;
  total_return_pct?: number | null;
  cagr_pct?: number | null;
  sharpe_ratio?: number | null;
  max_drawdown_pct?: number | null;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
