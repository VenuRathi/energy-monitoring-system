import type { MeterDiscoveryResult, MeterDiscoverySyncResult, MeterInput } from "../../types/energy";

type MeterEditorFormProps = {
  mode: "add" | "edit";
  value: MeterInput;
  scanStart: number;
  scanEnd: number;
  onChange: (next: MeterInput) => void;
  onScanRangeChange: (next: { scanStart: number; scanEnd: number }) => void;
  onSubmit: () => void;
  onCancel: () => void;
  onDiscover: () => void;
  onSyncDetected: () => void;
  saving: boolean;
  discovering: boolean;
  syncingDetected: boolean;
  errorMessage: string | null;
  discoveryErrorMessage?: string | null;
  discoveryResult?: MeterDiscoveryResult | null;
  syncResult?: MeterDiscoverySyncResult | null;
};

export function MeterEditorForm({
  mode,
  value,
  scanStart,
  scanEnd,
  onChange,
  onScanRangeChange,
  onSubmit,
  onCancel,
  onDiscover,
  onSyncDetected,
  saving,
  discovering,
  syncingDetected,
  errorMessage,
  discoveryErrorMessage,
  discoveryResult,
  syncResult,
}: MeterEditorFormProps) {
  const update = <K extends keyof MeterInput>(field: K, nextValue: MeterInput[K]) => {
    onChange({ ...value, [field]: nextValue });
  };

  const meterLabel = value.meter_name.trim() || value.meter_id || "New meter";
  const lineSummary = `${value.com_port || "COM n/a"} - Slave ${value.slave_id}`;
  const serialSummary = `${value.baud_rate} baud - ${value.parity}-${value.byte_size}-${value.stop_bits} - ${value.timeout}s timeout`;

  return (
    <section className="editor">
      <div className="editor__header">
        <div className="section-heading">
          <div>
            <p className="section-label">{mode === "edit" ? "Edit meter" : "Meter details"}</p>
            <h4>{meterLabel}</h4>
            <p className="page-copy">
              {mode === "edit"
                ? "Review the live meter setup, then change only what is needed."
                : "Create a clean meter record before enabling it for polling."}
            </p>
          </div>
        </div>

        <div className="editor__summary">
          <div className="editor__summary-row">
            <span className={`status-pill status-pill--${value.enabled ? "online" : "offline"}`}>
              {value.enabled ? "polling enabled" : "disabled"}
            </span>
            <span className="editor__meta-chip">{mode === "edit" ? "existing meter" : "new meter"}</span>
          </div>
          <div className="editor__meta-list">
            <span>{lineSummary}</span>
            <span>{serialSummary}</span>
            <span>{value.driver}</span>
          </div>
        </div>
      </div>

      <section className="editor__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Identity</p>
            <h4>Meter record</h4>
          </div>
        </div>

        <div className="editor__grid">
          <label className="editor__field">
            <span>Meter ID</span>
            <input
              value={value.meter_id ?? ""}
              onChange={(event) => update("meter_id", event.target.value.toUpperCase())}
              disabled={mode === "edit"}
              placeholder="MTR-001"
            />
            <small className="editor__hint">Internal ID for this app. Example: `MTR-003`.</small>
          </label>
          <label className="editor__field">
            <span>Meter name</span>
            <input value={value.meter_name} onChange={(event) => update("meter_name", event.target.value)} />
          </label>
          <label className="editor__field">
            <span>Location</span>
            <input value={value.location} onChange={(event) => update("location", event.target.value)} />
          </label>
          <label className="editor__field">
            <span>Manufacturer</span>
            <input value={value.manufacturer} onChange={(event) => update("manufacturer", event.target.value)} />
          </label>
          <label className="editor__field">
            <span>Model</span>
            <input value={value.model} onChange={(event) => update("model", event.target.value)} />
          </label>
          <label className="editor__field">
            <span>Protocol</span>
            <select value={value.protocol} onChange={(event) => update("protocol", event.target.value)}>
              <option value="modbus_rtu">modbus_rtu</option>
            </select>
          </label>
          <label className="editor__field">
            <span>Driver</span>
            <select value={value.driver} onChange={(event) => update("driver", event.target.value)}>
              <option value="schneider.pm5000">schneider.pm5000</option>
            </select>
          </label>
          <label className="editor__field editor__field--inline">
            <span>SEU</span>
            <input
              type="checkbox"
              checked={value.seu}
              onChange={(event) => update("seu", event.target.checked)}
            />
          </label>
        </div>
      </section>

      <section className="editor__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Line settings</p>
            <h4>Polling and serial configuration</h4>
          </div>
        </div>

        <div className="editor__grid">
          <label className="editor__field">
            <span>COM port</span>
            <input
              value={value.com_port}
              onChange={(event) => update("com_port", event.target.value.toUpperCase())}
              placeholder="COM6"
            />
            <small className="editor__hint">Example: `COM6`. Use scan to find the connected meters on this line.</small>
          </label>
          <label className="editor__field">
            <span>Slave ID</span>
            <input
              type="number"
              value={value.slave_id}
              onChange={(event) => update("slave_id", Number(event.target.value))}
            />
            <small className="editor__hint">Real meter address on the daisy chain. Example: `3`.</small>
          </label>
          <label className="editor__field">
            <span>Baud rate</span>
            <input
              type="number"
              value={value.baud_rate}
              onChange={(event) => update("baud_rate", Number(event.target.value))}
            />
          </label>
          <label className="editor__field">
            <span>Parity</span>
            <select value={value.parity} onChange={(event) => update("parity", event.target.value)}>
              <option value="N">N</option>
              <option value="E">E</option>
              <option value="O">O</option>
            </select>
          </label>
          <label className="editor__field">
            <span>Stop bits</span>
            <input
              type="number"
              value={value.stop_bits}
              onChange={(event) => update("stop_bits", Number(event.target.value))}
            />
          </label>
          <label className="editor__field">
            <span>Byte size</span>
            <input
              type="number"
              value={value.byte_size}
              onChange={(event) => update("byte_size", Number(event.target.value))}
            />
          </label>
          <label className="editor__field">
            <span>Timeout</span>
            <input
              type="number"
              step="0.1"
              value={value.timeout}
              onChange={(event) => update("timeout", Number(event.target.value))}
            />
          </label>
          <label className="editor__field editor__field--inline">
            <span>One based map</span>
            <input
              type="checkbox"
              checked={value.one_based_map}
              onChange={(event) => update("one_based_map", event.target.checked)}
            />
          </label>
          <label className="editor__field editor__field--inline">
            <span>Active for polling</span>
            <input
              type="checkbox"
              checked={value.enabled}
              onChange={(event) => update("enabled", event.target.checked)}
            />
          </label>
        </div>
      </section>

      <section className="editor__section">
        <div className="section-heading">
          <div>
            <p className="section-label">Discovery</p>
            <h4>Scan the line safely</h4>
            <p className="page-copy">
              Scan first, then let the system update which meters should stay active for polling.
            </p>
          </div>
        </div>

        <div className="editor__grid">
          <label className="editor__field">
            <span>Scan start</span>
            <input
              type="number"
              min={1}
              max={247}
              value={scanStart}
              onChange={(event) => onScanRangeChange({ scanStart: Number(event.target.value), scanEnd })}
            />
          </label>
          <label className="editor__field">
            <span>Scan end</span>
            <input
              type="number"
              min={1}
              max={247}
              value={scanEnd}
              onChange={(event) => onScanRangeChange({ scanStart, scanEnd: Number(event.target.value) })}
            />
          </label>
        </div>

        <div className="editor__notice">
          Recommended order: enter the COM settings, click the main scan button, let the system update the active meters,
          then only rename or adjust meters if needed.
        </div>

        <div className="editor__actions">
          <button
            type="button"
            className="primary-button"
            onClick={onSyncDetected}
            disabled={syncingDetected || discovering || !value.com_port.trim()}
          >
            {syncingDetected ? "Scanning line..." : "Scan line and update active meters"}
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={onDiscover}
            disabled={discovering || syncingDetected || !value.com_port.trim()}
          >
            {discovering ? "Checking..." : "Preview detected meters"}
          </button>
        </div>
      </section>

      {discoveryErrorMessage ? <div className="page-state page-state--padded">{discoveryErrorMessage}</div> : null}

      {discoveryResult ? (
        <div className="editor__result">
          <strong>{discoveryResult.message}</strong>
          {discoveryResult.recommendedSlaveId ? ` Recommended slave: ${discoveryResult.recommendedSlaveId}.` : ""}
          {discoveryResult.matches.length > 0 ? (
            <div className="page-copy">
              {discoveryResult.matches
                .map((match) =>
                  match.assignedMeterId
                    ? `Slave ${match.slaveId} (${match.probeLabel}) already assigned to ${match.assignedMeterName || match.assignedMeterId}`
                    : `Slave ${match.slaveId} responded via ${match.probeLabel}`,
                )
                .join(" | ")}
            </div>
          ) : null}
        </div>
      ) : null}

      {syncResult ? (
        <div className="editor__result">
          <strong>{syncResult.message}</strong>
          <div className="page-copy">
            Connected slave IDs: {syncResult.respondingSlaveIds.length > 0 ? syncResult.respondingSlaveIds.join(", ") : "none"}.
            Added: {syncResult.createdMeterIds.length > 0 ? syncResult.createdMeterIds.join(", ") : "none"}.
            Updated: {syncResult.updatedMeterIds.length > 0 ? syncResult.updatedMeterIds.join(", ") : "none"}.
            Left offline: {syncResult.offlineMeterIds.length > 0 ? syncResult.offlineMeterIds.join(", ") : "none"}.
          </div>
        </div>
      ) : null}

      {errorMessage ? <div className="page-state page-state--padded">{errorMessage}</div> : null}

      <div className="editor__actions">
        <button type="button" className="ghost-button" onClick={onCancel}>
          Cancel
        </button>
        <button type="button" className="primary-button" onClick={onSubmit} disabled={saving}>
          {saving ? "Saving..." : "Save changes"}
        </button>
      </div>
    </section>
  );
}
