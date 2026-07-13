import {
  ApiError,
  type BacktestRunRequest,
  type BacktestRunResponse,
  type BacktestRunSummary,
  type StrategyInfo,
  type TickerInfo,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response wasn't JSON; keep the generic message
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export async function fetchTickers(): Promise<TickerInfo[]> {
  const res = await fetch(`${API_BASE}/tickers`);
  return handleResponse<TickerInfo[]>(res);
}

export async function fetchStrategies(): Promise<StrategyInfo[]> {
  const res = await fetch(`${API_BASE}/strategies`);
  return handleResponse<StrategyInfo[]>(res);
}

export async function runBacktest(req: BacktestRunRequest): Promise<BacktestRunResponse> {
  const res = await fetch(`${API_BASE}/backtest/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse<BacktestRunResponse>(res);
}

export async function fetchRunResult(id: number): Promise<BacktestRunResponse> {
  const res = await fetch(`${API_BASE}/backtest/results/${id}`);
  return handleResponse<BacktestRunResponse>(res);
}

export async function fetchRunHistory(): Promise<BacktestRunSummary[]> {
  const res = await fetch(`${API_BASE}/backtest/results`);
  return handleResponse<BacktestRunSummary[]>(res);
}
