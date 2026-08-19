import { Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { ParameterCategory, ParameterMeta, ReportFilters } from "../../types/energy";
import { sortParametersByEnergyPriority } from "../../lib/energyParameters";

type ReportCriteriaProps = {
  parameters: ParameterMeta[];
  filters: ReportFilters;
  onChange: (next: ReportFilters) => void;
  includeDateRange?: boolean;
};

const categories: Array<ParameterCategory | "All"> = ["All", "Voltage", "Current", "Power", "Energy", "Quality", "Demand", "System"];
const rangePresets = [
  { label: "1 hour", hours: 1 },
  { label: "8 hours", hours: 8 },
  { label: "24 hours", hours: 24 },
  { label: "7 days", hours: 168 },
];

export function ReportCriteria({ parameters, filters, onChange, includeDateRange = true }: ReportCriteriaProps) {
  const [category, setCategory] = useState<(typeof categories)[number]>("All");
  const [search, setSearch] = useState("");

  const filteredParameters = useMemo(() => {
    const query = search.trim().toLowerCase();
    return sortParametersByEnergyPriority(
      parameters.filter((parameter) => {
        const matchesCategory = category === "All" || parameter.category === category;
        const matchesQuery =
          !query ||
          parameter.label.toLowerCase().includes(query) ||
          parameter.key.toLowerCase().includes(query) ||
          parameter.unit.toLowerCase().includes(query);
        return matchesCategory && matchesQuery;
      }),
    );
  }, [category, parameters, search]);

  const selectedParameters = useMemo(() => {
    const parameterMap = new Map(parameters.map((parameter) => [parameter.key, parameter]));
    return filters.parameterKeys
      .map((key, index) => {
        const parameter = parameterMap.get(key);
        return parameter ? { index, parameter } : null;
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

  return (
    <div className="report-criteria">
      {includeDateRange ? (
        <div className="report-grid report-grid--criteria">
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
      ) : null}

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
              onClick={() => onChange({ ...filters, intervalHours: preset.hours })}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="explorer__toolbar">
        <label className="explorer__field">
          <span className="explorer__label">Search parameters</span>
          <span className="explorer__input-icon" aria-hidden="true"><Search size={15} /></span>
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
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="explorer__meta explorer__meta--compact">
        <span>{filteredParameters.length} parameters available</span>
        <span>{filters.parameterKeys.length} selected</span>
      </div>

      <div className="report-selected report-selected--compact">
        <span className="report-selected__label">Selected parameters</span>
        <div className="report-selected__chips">
          {selectedParameters.length > 0 ? (
            selectedParameters.map(({ index, parameter }) => (
              <button key={parameter.key} type="button" className="report-selected__chip" onClick={() => toggleParameter(parameter.key)}>
                <span className="report-selected__index">{index + 1}</span>
                <span>{parameter.label}</span>
                <span className="report-selected__remove"><X size={13} aria-hidden="true" /></span>
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
    </div>
  );
}
