import type { MeterRecord } from "../../types/energy";

type MeterSelectorProps = {
  meters: MeterRecord[];
  value: string;
  onChange: (meterId: string) => void;
};

export function MeterSelector({ meters, value, onChange }: MeterSelectorProps) {
  return (
    <label className="meter-selector">
      <span className="meter-selector__label">Selected meter</span>
      <select className="meter-selector__control" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="ALL">ALL - All configured meters</option>
        {meters.map((meter) => (
          <option key={meter.meter_id} value={meter.meter_id}>
            {meter.meter_id} - {meter.meter_name} - {meter.location}
          </option>
        ))}
      </select>
    </label>
  );
}
