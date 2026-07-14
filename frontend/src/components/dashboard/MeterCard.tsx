import type { MeterRecord } from "../../types/energy";
import { formatNumber, formatTimestamp } from "../../lib/formatters";

type MeterCardProps = {
  meter: MeterRecord;
  active?: boolean;
  onClick?: (meterId: string) => void;
};

export function MeterCard({ meter, active = false, onClick }: MeterCardProps) {
  return (
    <button
      type="button"
      className={`meter-card ${active ? "meter-card--active" : ""}`}
      onClick={() => onClick?.(meter.meter_id)}
    >
      <div className="meter-card__top">
        <div>
          <p className="meter-card__plant">{meter.meter_id}</p>
          <h5 className="meter-card__name">{meter.meter_name}</h5>
          {meter.status_detail ? <p className="meter-card__detail">{meter.status_detail}</p> : null}
        </div>
        <span className={`status-pill status-pill--${meter.status}`}>{meter.status}</span>
      </div>

      <dl className="meter-card__metrics">
        <div>
          <dt>Active Power</dt>
          <dd>{formatNumber(meter.base_power, 2)} kW</dd>
        </div>
        <div>
          <dt>Voltage L-N</dt>
          <dd>{formatNumber(meter.base_voltage, 1)} V</dd>
        </div>
        <div>
          <dt>Current</dt>
          <dd>{formatNumber(meter.base_current, 2)} A</dd>
        </div>
        <div>
          <dt>Energy</dt>
          <dd>{formatNumber(meter.base_energy, 2)} kWh</dd>
        </div>
      </dl>

      <div className="meter-card__footer">
        <span>{meter.location}</span>
        <span>{meter.seu ? "SEU" : "Non-SEU"}</span>
        <span>Updated {formatTimestamp(meter.last_update)}</span>
      </div>
    </button>
  );
}
