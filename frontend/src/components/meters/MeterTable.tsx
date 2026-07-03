import type { MeterRecord } from "../../types/energy";
import { formatTimestamp } from "../../lib/formatters";

type MeterTableProps = {
  meters: MeterRecord[];
  selectedMeterId: string;
  onSelect: (meterId: string) => void;
  onEdit: (meter: MeterRecord) => void;
  onDelete: (meterId: string) => void;
};

export function MeterTable({ meters, selectedMeterId, onSelect, onEdit, onDelete }: MeterTableProps) {
  return (
    <div className="table-shell">
      <table className="latest-table latest-table--compact meters-table">
        <thead>
          <tr>
            <th>Meter</th>
            <th>Model</th>
            <th>Location</th>
            <th>Status</th>
            <th>SEU</th>
            <th>Polling</th>
            <th>Last update</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {meters.map((meter) => (
            <tr
              key={meter.meter_id}
              className={selectedMeterId === meter.meter_id ? "meters-table__row--selected" : ""}
              onClick={() => onSelect(meter.meter_id)}
            >
              <td className="latest-table__parameter">
                <strong>{meter.meter_name}</strong>
                <div className="table-subtle">{meter.meter_id}</div>
              </td>
              <td>{meter.manufacturer} {meter.model}</td>
              <td>{meter.location}</td>
              <td>
                <span className={`status-pill status-pill--${meter.status}`}>{meter.status}</span>
              </td>
              <td>{meter.seu ? "Yes" : "No"}</td>
              <td>{meter.enabled ? "Yes" : "No"}</td>
              <td>{formatTimestamp(meter.last_update)}</td>
              <td>
                <div className="row-actions" onClick={(event) => event.stopPropagation()}>
                  <button type="button" className="ghost-button" onClick={() => onEdit(meter)}>
                    Edit
                  </button>
                  <button type="button" className="ghost-button ghost-button--danger" onClick={() => onDelete(meter.meter_id)}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
