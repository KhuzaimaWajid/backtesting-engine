import type { Trade } from "../types";

export function TradesTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <div className="empty-state" style={{ padding: "40px 24px" }}>
        <p>No trades were executed in this window.</p>
      </div>
    );
  }

  return (
    <div className="trades-table-scroll">
      <table className="trades-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Side</th>
            <th>Shares</th>
            <th>Price</th>
            <th>Commission</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={`${t.date}-${i}`}>
              <td>{t.date}</td>
              <td style={{ textAlign: "left" }}>
                <span className={`side-badge ${t.side === "BUY" ? "buy" : "sell"}`}>{t.side}</span>
              </td>
              <td>{t.shares.toLocaleString()}</td>
              <td>${t.price.toFixed(2)}</td>
              <td>${t.commission.toFixed(2)}</td>
              <td>${t.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
