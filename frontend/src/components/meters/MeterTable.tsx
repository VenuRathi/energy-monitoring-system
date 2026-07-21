import type { MeterRecord } from "../../types/energy";
import { formatTimestamp } from "../../lib/formatters";

type MeterTableProps = {
  meters: MeterRecord[];
  selectedMeterId: string;
  onSelect: (meterId: string) => void;
  onEdit: (meter: MeterRecord) => void;
  onDisable: (meterId: string) => void;
};

export function MeterTable({ meters, selectedMeterId, onSelect, onEdit, onDisable }: MeterTableProps) {
  if (meters.length === 0) {
    return (
      <div className="page-state">
        <h3>No meters configured yet</h3>
        <p>Add the first meter or run a scan on the active COM line to populate the meter list.</p>
      </div>
    );
  }

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
                <div className="table-subtle">
                  {meter.com_port || "COM n/a"} - Slave {meter.slave_id}
                </div>
                {!meter.enabled ? <div className="table-subtle table-subtle--danger">Disabled meter</div> : null}
              </td>
              <td>{meter.manufacturer} {meter.model}</td>
              <td>{meter.location}</td>
              <td>
                <span className={`status-pill status-pill--${meter.status}`}>{meter.status}</span>
                {meter.status_detail ? <div className="table-subtle">{meter.status_detail}</div> : null}
              </td>
              <td>{meter.seu ? "Yes" : "No"}</td>
              <td>
                <strong>{meter.enabled ? "Active" : "Disabled"}</strong>
                <div className="table-subtle">{meter.enabled ? "Included in polling" : "History preserved only"}</div>
              </td>
              <td>{formatTimestamp(meter.last_update)}</td>
              <td>
                <div className="row-actions" onClick={(event) => event.stopPropagation()}>
                  <button type="button" className="ghost-button" onClick={() => onEdit(meter)}>
                    Edit
                  </button>
                  <button
                    type="button"
                    className="ghost-button ghost-button--danger"
                    onClick={() => onDisable(meter.meter_id)}
                    disabled={!meter.enabled}
                  >
                    Disable Meter
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
