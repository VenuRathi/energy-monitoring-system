import { CheckCircle2, Filter, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { MeterRecord, ReportFilters } from "../../types/energy";

type SharedReportFiltersProps = {
  meters: MeterRecord[];
  filters: ReportFilters;
  onChange: (next: ReportFilters) => void;
  onSelectMeter: (meterId: string) => void;
};

export function SharedReportFilters({ meters, filters, onChange, onSelectMeter }: SharedReportFiltersProps) {
  const [search, setSearch] = useState("");
  const enabledMeters = useMemo(() => meters.filter((meter) => meter.enabled), [meters]);
  const visibleMeters = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return meters;
    }
    return meters.filter((meter) =>
      [meter.meter_name, meter.meter_id, meter.location].some((value) => value.toLowerCase().includes(query)),
    );
  }, [meters, search]);
  const selectedMeters = useMemo(
    () => meters.filter((meter) => filters.meterIds.includes(meter.meter_id)),
    [filters.meterIds, meters],
  );

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
    <section className="report-filters report-scope">
      <div className="report-grid report-grid--scope">
        <div className="editor__field">
          <span>Meters</span>
          <label className="report-meter-search">
            <span className="sr-only">Search meters</span>
            <Search size={15} aria-hidden="true" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by meter name, ID, or location"
            />
          </label>
          <div className="report-meter-list" role="group" aria-label="Meters">
            {visibleMeters.map((meter) => {
              const selected = filters.meterIds.includes(meter.meter_id);
              return (
                <label key={meter.meter_id} className={`report-meter-option ${selected ? "report-meter-option--selected" : ""}`}>
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() =>
                      updateMeterSelection(
                        selected
                          ? filters.meterIds.filter((meterId) => meterId !== meter.meter_id)
                          : [...filters.meterIds, meter.meter_id],
                      )
                    }
                  />
                  <span className="report-meter-option__copy">
                    <strong>{meter.meter_name}</strong>
                    <small>{meter.location || meter.meter_id}</small>
                  </span>
                  <span className={`status-pill status-pill--${meter.enabled ? meter.status : "offline"}`}>
                    {meter.enabled ? meter.status : "Disabled"}
                  </span>
                </label>
              );
            })}
            {visibleMeters.length === 0 ? <span className="report-meter-list__empty">No meters match this search.</span> : null}
          </div>
          <div className="report-meter-actions">
            <button
              type="button"
              className="ghost-button ghost-button--compact"
              onClick={() => updateMeterSelection(enabledMeters.map((meter) => meter.meter_id))}
            >
              <CheckCircle2 size={15} aria-hidden="true" />
              Select enabled
            </button>
            <button type="button" className="ghost-button ghost-button--compact" onClick={() => updateMeterSelection(meters.map((meter) => meter.meter_id))}>
              <Filter size={15} aria-hidden="true" />
              Select all
            </button>
            <button type="button" className="ghost-button ghost-button--compact" onClick={() => updateMeterSelection([])}>
              <X size={15} aria-hidden="true" />
              Clear
            </button>
          </div>
        </div>
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
                <span className="report-selected__remove"><X size={13} aria-hidden="true" /></span>
              </button>
            ))
          ) : (
            <span className="report-selected__empty">No meters selected yet.</span>
          )}
        </div>
      </div>
    </section>
  );
}
