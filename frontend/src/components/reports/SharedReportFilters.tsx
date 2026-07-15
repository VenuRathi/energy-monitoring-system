import { useMemo, useState } from "react";
import type { MeterRecord, ParameterCategory, ParameterMeta, ReportFilters } from "../../types/energy";

type SharedReportFiltersProps = {
  meters: MeterRecord[];
  parameters: ParameterMeta[];
  filters: ReportFilters;
  onChange: (next: ReportFilters) => void;
  onSelectMeter: (meterId: string) => void;
};

const categories: Array<ParameterCategory | "All"> = ["All", "Voltage", "Current", "Power", "Energy", "Quality", "Demand", "System"];
const prioritizedKeys = [
  "active_energy_received_out_of_load",
  "reactive_energy_received",
  "apparent_energy_received",
  "power_factor_total",
];
const rangePresets = [
  { label: "1 hour", hours: 1 },
  { label: "8 hours", hours: 8 },
  { label: "24 hours", hours: 24 },
  { label: "7 days", hours: 168 },
];

export function SharedReportFilters({ meters, parameters, filters, onChange, onSelectMeter }: SharedReportFiltersProps) {
  const [category, setCategory] = useState<(typeof categories)[number]>("All");
  const [search, setSearch] = useState("");
  const enabledMeters = useMemo(() => meters.filter((meter) => meter.enabled), [meters]);
  const selectedMeters = useMemo(
    () => meters.filter((meter) => filters.meterIds.includes(meter.meter_id)),
    [filters.meterIds, meters],
  );

  const filteredParameters = useMemo(() => {
    const query = search.trim().toLowerCase();
    const priority = new Map(prioritizedKeys.map((key, index) => [key, index]));
    return parameters
      .filter((parameter) => {
        const matchesCategory = category === "All" || parameter.category === category;
        const matchesQuery =
          !query ||
          parameter.label.toLowerCase().includes(query) ||
          parameter.key.toLowerCase().includes(query) ||
          parameter.unit.toLowerCase().includes(query);
        return matchesCategory && matchesQuery;
      })
      .sort((left, right) => {
        const leftPriority = priority.get(left.key);
        const rightPriority = priority.get(right.key);
        if (leftPriority !== undefined && rightPriority !== undefined) {
          return leftPriority - rightPriority;
        }
        if (leftPriority !== undefined) {
          return -1;
        }
        if (rightPriority !== undefined) {
          return 1;
        }
        return left.order - right.order;
      });
  }, [category, parameters, search]);

  const selectedParameters = useMemo(() => {
    const parameterMap = new Map(parameters.map((parameter) => [parameter.key, parameter]));
    return filters.parameterKeys
      .map((key, index) => {
        const parameter = parameterMap.get(key);
        if (!parameter) {
          return null;
        }
        return {
          index,
          parameter,
        };
      })
      .filter((item): item is { index: number; parameter: ParameterMeta } => item !== null);
  }, [filters.parameterKeys, parameters]);

  const toggleParameter = (parameterKey: string) => {
    onChange({
      ...filters,
      parameterKeys: filters.parameterKeys.includes(parameterKey)
        ? filters.parameterKeys.filter((key) => key !== parameterKey)
        : [...filters.parameterKeys, parameterKey],
    });
  };

  const applyRangePreset = (hours: number) => {
    onChange({
      ...filters,
      intervalHours: hours,
    });
  };

  const updateMeterSelection = (meterIds: string[]) => {
    const uniqueMeterIds = meterIds.filter((meterId, index) => meterIds.indexOf(meterId) === index);
    const primaryMeterId = uniqueMeterIds[0] ?? "";
    onChange({
      ...filters,
      meterId: primaryMeterId,
      meterIds: uniqueMeterIds,
    });
    onSelectMeter(primaryMeterId || "ALL");
  };

  return (
    <section className="report-filters">
      <div className="report-grid">
        <label className="editor__field">
          <span>Meters</span>
          <select
            multiple
            size={Math.min(5, Math.max(3, meters.length))}
            value={filters.meterIds}
            onChange={(event) => updateMeterSelection(Array.from(event.target.selectedOptions, (option) => option.value))}
          >
            {meters.map((meter) => (
              <option key={meter.meter_id} value={meter.meter_id}>
                {meter.meter_name} {meter.enabled ? "" : "(disabled)"}
              </option>
            ))}
          </select>
          <div className="report-meter-actions">
            <button
              type="button"
              className="ghost-button ghost-button--compact"
              onClick={() => updateMeterSelection(enabledMeters.map((meter) => meter.meter_id))}
            >
              Select enabled
            </button>
            <button type="button" className="ghost-button ghost-button--compact" onClick={() => updateMeterSelection(meters.map((meter) => meter.meter_id))}>
              Select all
            </button>
            <button type="button" className="ghost-button ghost-button--compact" onClick={() => updateMeterSelection([])}>
              Clear
            </button>
          </div>
        </label>

        <label className="editor__field">
          <span>Start date/time</span>
          <input
            type="datetime-local"
            value={filters.startDateTime}
            onChange={(event) => onChange({ ...filters, startDateTime: event.target.value })}
          />
        </label>

        <label className="editor__field">
          <span>End date/time</span>
          <input
            type="datetime-local"
            value={filters.endDateTime}
            onChange={(event) => onChange({ ...filters, endDateTime: event.target.value })}
          />
        </label>
      </div>

      <div className="report-selected report-selected--compact">
        <span className="report-selected__label">Selected meters</span>
        <div className="report-selected__chips">
          {selectedMeters.length > 0 ? (
            selectedMeters.map((meter) => (
              <button
                key={meter.meter_id}
                type="button"
                className="report-selected__chip"
                onClick={() => updateMeterSelection(filters.meterIds.filter((meterId) => meterId !== meter.meter_id))}
              >
                <span>{meter.meter_name}</span>
                <span className="report-selected__remove">Remove</span>
              </button>
            ))
          ) : (
            <span className="report-selected__empty">No meters selected yet.</span>
          )}
        </div>
      </div>

      <div className="report-range-bar">
        <span className="report-range-bar__label">Reading interval</span>
        <div className="report-range-bar__actions">
          <button
            type="button"
            className={`ghost-button ghost-button--compact ${filters.intervalHours === null ? "ghost-button--active" : ""}`}
            onClick={() => onChange({ ...filters, intervalHours: null })}
          >
            All readings
          </button>
          {rangePresets.map((preset) => (
            <button
              key={preset.hours}
              type="button"
              className={`ghost-button ghost-button--compact ${filters.intervalHours === preset.hours ? "ghost-button--active" : ""}`}
              onClick={() => applyRangePreset(preset.hours)}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="explorer__toolbar">
        <label className="explorer__field">
          <span className="explorer__label">Search</span>
          <input
            className="explorer__input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search parameter"
          />
        </label>

        <label className="explorer__field">
          <span className="explorer__label">Category</span>
          <select className="explorer__input" value={category} onChange={(event) => setCategory(event.target.value as typeof category)}>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="explorer__meta explorer__meta--compact">
        <span>{filteredParameters.length} parameters</span>
        <span>{filters.parameterKeys.length} selected</span>
      </div>

      <div className="report-selected report-selected--compact">
        <span className="report-selected__label">Selected parameters</span>
        <div className="report-selected__chips">
          {selectedParameters.length > 0 ? (
            selectedParameters.map(({ index, parameter }) => (
              <button
                key={parameter.key}
                type="button"
                className="report-selected__chip"
                onClick={() => toggleParameter(parameter.key)}
              >
                <span className="report-selected__index">{index + 1}</span>
                <span>{parameter.label}</span>
                <span className="report-selected__remove">Remove</span>
              </button>
            ))
          ) : (
            <span className="report-selected__empty">No parameters selected yet.</span>
          )}
        </div>
      </div>

      <div className="explorer__list explorer__list--compact">
        {filteredParameters.map((parameter) => {
          const selectedIndex = filters.parameterKeys.indexOf(parameter.key);
          return (
          <button
            key={parameter.key}
            type="button"
            className={`parameter-row ${filters.parameterKeys.includes(parameter.key) ? "parameter-row--selected" : ""}`}
            onClick={() => toggleParameter(parameter.key)}
          >
            <span className="parameter-row__main">
              <strong>{parameter.label}</strong>
              <span>{parameter.key}</span>
            </span>
            <span className="parameter-row__side">
              {selectedIndex >= 0 ? <span className="parameter-row__index">#{selectedIndex + 1}</span> : null}
              <span className="parameter-row__category">{parameter.category}</span>
              <span className="parameter-row__unit">{parameter.unit || "n/a"}</span>
            </span>
          </button>
          );
        })}
      </div>
    </section>
  );
}
