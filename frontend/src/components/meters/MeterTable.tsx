import { Edit3, PauseCircle, PlayCircle } from "lucide-react";
import type { MeterRecord } from "../../types/energy";
import { formatTimestamp } from "../../lib/formatters";

type MeterTableProps = {
  meters: MeterRecord[];
  selectedMeterId: string;
  emptyMessage?: string;
  onSelect: (meterId: string) => void;
  onEdit: (meter: MeterRecord) => void;
  onEnable: (meter: MeterRecord) => void;
  onDisable: (meterId: string) => void;
};

export function MeterTable({ meters, selectedMeterId, emptyMessage, onSelect, onEdit, onEnable, onDisable }: MeterTableProps) {
  if (meters.length === 0) {
    return (
      <div className="page-state">
        <h3>No meters configured yet</h3>
        <p>{emptyMessage ?? "Add the first meter or run a scan on the active COM line to populate the meter list."}</p>
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
            <th>COM / Slave</th>
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
                {!meter.enabled ? <div className="table-subtle table-subtle--danger">Disabled</div> : null}
              </td>
              <td>
                <strong>{meter.com_port || "COM n/a"}</strong>
                <div className="table-subtle">Slave {meter.slave_id}</div>
              </td>
              <td>
                <strong>{meter.enabled ? "Active" : "Disabled"}</strong>
              </td>
              <td>{formatTimestamp(meter.last_update)}</td>
              <td>
                <div className="row-actions" onClick={(event) => event.stopPropagation()}>
                  <button type="button" className="icon-button" onClick={() => onEdit(meter)} aria-label={`Edit ${meter.meter_name}`}>
                    <Edit3 size={16} aria-hidden="true" />
                  </button>
                  {meter.enabled ? (
                    <button
                      type="button"
                      className="icon-button icon-button--danger"
                      onClick={() => onDisable(meter.meter_id)}
                      aria-label={`Disable ${meter.meter_name}`}
                    >
                      <PauseCircle size={16} aria-hidden="true" />
                    </button>
                  ) : (
                    <button type="button" className="icon-button" onClick={() => onEnable(meter)} aria-label={`Enable ${meter.meter_name}`}>
                      <PlayCircle size={16} aria-hidden="true" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
