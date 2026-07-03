import type { LatestReadingRow } from "../../types/energy";
import { formatNumber } from "../../lib/formatters";

type LatestReadingsTableProps = {
  rows: LatestReadingRow[];
};

export function LatestReadingsTable({ rows }: LatestReadingsTableProps) {
  if (rows.length === 0) {
    return <div className="page-state page-state--padded">No readings available yet for this meter.</div>;
  }

  return (
    <div className="table-shell">
      <table className="latest-table latest-table--compact">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Value</th>
            <th>Unit</th>
            <th>Date</th>
            <th>Time</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.parameterKey}>
              <td className="latest-table__parameter">
                <strong>{row.label}</strong>
                <div className="table-subtle">{row.parameterKey}</div>
              </td>
              <td className="latest-table__value">
                {typeof row.value === "number" ? formatNumber(row.value, 2) : row.value}
              </td>
              <td className="latest-table__unit">{row.unit || "n/a"}</td>
              <td className="latest-table__updated">{row.date || "n/a"}</td>
              <td className="latest-table__updated">{row.time || "n/a"}</td>
              <td className="latest-table__updated">{row.timestampSource === "meter" ? "Meter" : "Fallback"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
