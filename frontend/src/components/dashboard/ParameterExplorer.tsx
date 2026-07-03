import { useMemo, useState } from "react";
import type { LatestReadingRow, ParameterCategory, ParameterMeta } from "../../types/energy";

type ParameterExplorerProps = {
  parameters: ParameterMeta[];
  latestReadings: LatestReadingRow[];
  selectedKey: string;
  onSelect: (parameterKey: string) => void;
};

const categoryOptions: Array<ParameterCategory | "All"> = [
  "All",
  "Voltage",
  "Current",
  "Power",
  "Energy",
  "Quality",
  "Demand",
  "System",
];

export function ParameterExplorer({ parameters, latestReadings, selectedKey, onSelect }: ParameterExplorerProps) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<(typeof categoryOptions)[number]>("All");

  const readingMap = useMemo(() => {
    return new Map(latestReadings.map((reading) => [reading.parameterKey, reading]));
  }, [latestReadings]);

  const filteredParameters = useMemo(() => {
    const searchText = query.trim().toLowerCase();

    return parameters
      .filter((parameter) => category === "All" || parameter.category === category)
      .filter((parameter) => {
        if (!searchText) return true;
        return (
          parameter.label.toLowerCase().includes(searchText) ||
          parameter.key.toLowerCase().includes(searchText) ||
          parameter.unit.toLowerCase().includes(searchText)
        );
      })
      .sort((left, right) => {
        if (left.key === selectedKey) return -1;
        if (right.key === selectedKey) return 1;
        return left.order - right.order;
      });
  }, [category, parameters, query]);

  return (
    <section className="explorer">
      <div className="explorer__toolbar">
        <label className="explorer__field">
          <span className="explorer__label">Search</span>
          <input
            className="explorer__input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search parameter or unit"
          />
        </label>

        <label className="explorer__field">
          <span className="explorer__label">Category</span>
          <select
            className="explorer__input"
            value={category}
            onChange={(event) => setCategory(event.target.value as (typeof categoryOptions)[number])}
          >
            {categoryOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="explorer__meta">
        <span>{filteredParameters.length} parameters</span>
        <span>Backend metadata</span>
      </div>

      <div className="explorer__list" role="list">
        {filteredParameters.length === 0 ? (
          <div className="page-state page-state--padded">No parameters match the current filters.</div>
        ) : (
          filteredParameters.slice(0, 18).map((parameter) => (
            <button
              key={parameter.key}
              type="button"
              className={`parameter-row ${selectedKey === parameter.key ? "parameter-row--selected" : ""}`}
              onClick={() => onSelect(parameter.key)}
            >
              <span className="parameter-row__main">
                <strong>{parameter.label}</strong>
                <span>{parameter.key}</span>
              </span>
              <span className="parameter-row__side">
                <span className="parameter-row__value">
                  {readingMap.get(parameter.key)?.value ?? "n/a"}
                </span>
                <span className="parameter-row__category">{parameter.category}</span>
                <span className="parameter-row__unit">{parameter.unit || "n/a"}</span>
              </span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
