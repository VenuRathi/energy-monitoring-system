import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "../../types/energy";
import { formatChartTime, formatNumber } from "../../lib/formatters";

type EnergyChartProps = {
  data: TrendPoint[];
  label: string;
  unit: string;
};

export function EnergyChart({ data, label, unit }: EnergyChartProps) {
  if (data.length === 0) {
    return (
      <div className="chart chart--empty">
        <div className="chart__header">
          <div>
            <p className="section-label">Trend</p>
            <h4>{label}</h4>
          </div>
          <span className="chart__unit">{unit || "n/a"}</span>
        </div>
        <div className="page-state page-state--padded">No readings available yet for this meter.</div>
      </div>
    );
  }

  return (
    <div className="chart">
      <div className="chart__header">
        <div>
          <p className="section-label">Trend</p>
          <h4>{label}</h4>
        </div>
        <span className="chart__unit">{unit || "n/a"}</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#7dd3fc" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#7dd3fc" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(148, 163, 184, 0.2)" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatChartTime}
            stroke="rgba(100, 116, 139, 0.8)"
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="rgba(100, 116, 139, 0.8)"
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}`}
          />
          <Tooltip
            content={({ active, payload, label: tooltipLabel }) => {
              if (!active || !payload?.length) {
                return null;
              }

              const value = Number(payload[0]?.value ?? 0);

              return (
                <div className="chart-tooltip">
                  <div className="chart-tooltip__label">
                    {formatChartTime(String(tooltipLabel ?? ""))}
                  </div>
                  <div className="chart-tooltip__value">
                    {formatNumber(value, 2)} {unit}
                  </div>
                  <div className="chart-tooltip__series">{label}</div>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#7dd3fc"
            fill="url(#powerGradient)"
            strokeWidth={2}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
