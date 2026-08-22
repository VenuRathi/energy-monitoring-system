import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo, useState } from "react";
import type { HourlyEnergyPoint } from "../../types/energy";
import { formatChartTime, formatNumber, formatTimestamp } from "../../lib/formatters";

type EnergyHistoryPanelProps = {
  data: HourlyEnergyPoint[];
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  onRetry: () => void;
};

const SERIES = [
  { key: "activeEnergy", label: "kWh", color: "#4f7fdc" },
  { key: "reactiveEnergy", label: "kVARh", color: "#8a7bd8" },
  { key: "apparentEnergy", label: "kVAh", color: "#31a98f" },
] as const;

function valueText(value: number | null) {
  return value === null ? "n/a" : formatNumber(value, 3);
}

export function EnergyHistoryPanel({ data, isLoading, isError, errorMessage, onRetry }: EnergyHistoryPanelProps) {
  const [mode, setMode] = useState<"cumulative" | "increment">("cumulative");

  const displayData = useMemo(() => {
    if (mode === "cumulative") return data;

    return data.map((point, index) => {
      const previous = data[index - 1];
      const delta = (current: number | null, prior: number | null | undefined) => {
        if (current === null || prior == null) return null;
        return current >= prior ? current - prior : current;
      };
      return {
        ...point,
        activeEnergy: delta(point.activeEnergy, previous?.activeEnergy),
        reactiveEnergy: delta(point.reactiveEnergy, previous?.reactiveEnergy),
        apparentEnergy: delta(point.apparentEnergy, previous?.apparentEnergy),
      };
    });
  }, [data, mode]);

  if (isLoading) {
    return <div className="page-state page-state--padded">Loading 72-hour energy history...</div>;
  }

  if (isError) {
    return (
      <div className="page-state page-state--error page-state--padded">
        <p>{errorMessage || "Unable to load hourly energy history."}</p>
        <button type="button" className="ghost-button" onClick={onRetry}>Retry history</button>
      </div>
    );
  }

  if (data.length === 0) {
    return <div className="page-state page-state--padded">No hourly energy history is available for this meter yet.</div>;
  }

  return (
    <div className="energy-history">
      <div className="energy-history__toolbar">
        <div>
          <span className="section-label">Energy interpretation</span>
          <p className="table-subtle">{mode === "cumulative" ? "Cumulative meter totals" : "Estimated change between hourly readings"}</p>
        </div>
        <div className="segmented-control" role="tablist" aria-label="Energy history mode">
          <button type="button" className={mode === "cumulative" ? "segmented-control__button segmented-control__button--active" : "segmented-control__button"} onClick={() => setMode("cumulative")}>Cumulative</button>
          <button type="button" className={mode === "increment" ? "segmented-control__button segmented-control__button--active" : "segmented-control__button"} onClick={() => setMode("increment")}>Hourly change</button>
        </div>
      </div>
      <div className="energy-history__chart">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={displayData} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="rgba(148, 163, 184, 0.18)" />
            <XAxis dataKey="hour" tickFormatter={formatChartTime} stroke="rgba(100, 116, 139, 0.8)" tickLine={false} axisLine={false} />
            <YAxis stroke="rgba(100, 116, 139, 0.8)" tickLine={false} axisLine={false} />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                const row = payload[0]?.payload as HourlyEnergyPoint;
                return (
                  <div className="chart-tooltip">
                    <div className="chart-tooltip__label">{formatTimestamp(String(label ?? ""))}</div>
                    {SERIES.map((series) => (
                      <div key={series.key} className="energy-history__tooltip-row">
                        <span style={{ color: series.color }}>{series.label}</span>
                        <strong>{valueText(row[series.key])}</strong>
                      </div>
                    ))}
                  </div>
                );
              }}
            />
            <Legend />
            {SERIES.map((series) => (
              <Line key={series.key} type="monotone" dataKey={series.key} name={series.label} stroke={series.color} strokeWidth={2} dot={false} connectNulls={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="table-shell energy-history__table-shell">
        <table className="latest-table latest-table--compact energy-history__table">
          <thead>
            <tr><th>Hour</th><th>kWh</th><th>kVARh</th><th>kVAh</th></tr>
          </thead>
          <tbody>
            {displayData.map((point) => (
              <tr key={point.hour}>
                <td>{formatTimestamp(point.hour)}</td>
                <td>{valueText(point.activeEnergy)}</td>
                <td>{valueText(point.reactiveEnergy)}</td>
                <td>{valueText(point.apparentEnergy)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
