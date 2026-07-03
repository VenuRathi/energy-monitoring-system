import { useEffect, useMemo, useState } from "react";
import { AlertRulesPanel } from "../components/meters/AlertRulesPanel";
import { MeterEditorForm } from "../components/meters/MeterEditorForm";
import { MeterTable } from "../components/meters/MeterTable";
import { useMeterMutations, useReportMutations } from "../hooks/useEnergyMutations";
import { useAlertRulesData, useMetersData, useParameterCatalog } from "../hooks/useMetersData";
import type { MeterInput, MeterRecord } from "../types/energy";
import { formatNumber } from "../lib/formatters";

type MetersPageProps = {
  selectedMeterId: string;
  onSelectMeter: (meterId: string) => void;
};

const emptyMeter = (meterId?: string): MeterInput => ({
  meter_id: meterId,
  meter_name: "",
  location: "",
  manufacturer: "Schneider",
  model: "PM5000-EM6400",
  protocol: "modbus_rtu",
  enabled: true,
  seu: false,
  driver: "schneider.pm5000",
  com_port: "",
  slave_id: 1,
  baud_rate: 9600,
  parity: "N",
  stop_bits: 1,
  byte_size: 8,
  timeout: 2.0,
  one_based_map: true,
});

function validateMeterInput(input: MeterInput): string | null {
  const meterId = (input.meter_id ?? "").trim();
  if (!meterId) {
    return "Meter ID is required.";
  }
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(meterId)) {
    return "Meter ID may contain only letters, numbers, hyphens, and underscores.";
  }
  if (!input.meter_name.trim()) {
    return "Meter name is required.";
  }
  if (!input.location.trim()) {
    return "Location is required.";
  }
  if (!input.com_port.trim() && input.enabled) {
    return "COM port is required for an enabled meter.";
  }
  if (input.slave_id < 1 || input.slave_id > 247) {
    return "Slave ID must be between 1 and 247.";
  }
  if (input.timeout <= 0) {
    return "Timeout must be greater than zero.";
  }
  return null;
}

export function MetersPage({ selectedMeterId, onSelectMeter }: MetersPageProps) {
  const { data, isLoading } = useMetersData();
  const { data: parameters = [] } = useParameterCatalog();
  const { saveMeter, deleteMeter, discoverMeters, syncDiscoveredMeters } = useMeterMutations();
  const reportMutations = useReportMutations();
  const [editing, setEditing] = useState<MeterInput>(emptyMeter());
  const [mode, setMode] = useState<"add" | "edit">("add");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [scanRange, setScanRange] = useState({ scanStart: 1, scanEnd: 16 });

  const meters = data ?? [];

  const selectedMeter = useMemo(
    () => meters.find((meter) => meter.meter_id === selectedMeterId) ?? meters[0],
    [meters, selectedMeterId],
  );
  const { data: alertRules = [] } = useAlertRulesData(selectedMeter?.meter_id ?? "");

  useEffect(() => {
    if (mode === "add") {
      setEditing(emptyMeter());
      setValidationMessage(null);
    }
  }, [mode]);

  useEffect(() => {
    if (selectedMeter && mode === "edit" && editing.meter_id !== selectedMeter.meter_id) {
      setEditing({
        meter_id: selectedMeter.meter_id,
        meter_name: selectedMeter.meter_name,
        location: selectedMeter.location,
        manufacturer: selectedMeter.manufacturer,
        model: selectedMeter.model,
        protocol: selectedMeter.protocol,
        enabled: selectedMeter.enabled,
        seu: selectedMeter.seu,
        driver: selectedMeter.driver,
        com_port: selectedMeter.com_port,
        slave_id: selectedMeter.slave_id,
        baud_rate: selectedMeter.baud_rate,
        parity: selectedMeter.parity,
        stop_bits: selectedMeter.stop_bits,
        byte_size: selectedMeter.byte_size,
        timeout: selectedMeter.timeout,
        one_based_map: selectedMeter.one_based_map,
      });
      setValidationMessage(null);
    }
  }, [editing.meter_id, mode, selectedMeter]);

  const startAdd = () => {
    setMode("add");
    setEditing(emptyMeter());
    setValidationMessage(null);
  };

  const startEdit = (meter: MeterRecord) => {
    setMode("edit");
    setEditing({
      meter_id: meter.meter_id,
      meter_name: meter.meter_name,
      location: meter.location,
      manufacturer: meter.manufacturer,
      model: meter.model,
      protocol: meter.protocol,
      enabled: meter.enabled,
      seu: meter.seu,
      driver: meter.driver,
      com_port: meter.com_port,
      slave_id: meter.slave_id,
      baud_rate: meter.baud_rate,
      parity: meter.parity,
      stop_bits: meter.stop_bits,
      byte_size: meter.byte_size,
      timeout: meter.timeout,
      one_based_map: meter.one_based_map,
    });
    setValidationMessage(null);
    onSelectMeter(meter.meter_id);
  };

  const submit = () => {
    const message = validateMeterInput(editing);
    if (message) {
      setValidationMessage(message);
      return;
    }

    setValidationMessage(null);
    saveMeter.mutate(editing, {
      onSuccess: (savedMeter) => {
        setMode("add");
        setEditing(emptyMeter());
        onSelectMeter(savedMeter.meter_id);
      },
    });
  };

  const remove = (meterId: string) => {
    deleteMeter.mutate(meterId);
    if (selectedMeterId === meterId && meters.length > 1) {
      onSelectMeter(meters.find((meter) => meter.meter_id !== meterId)?.meter_id ?? meters[0].meter_id);
    }
  };

  const runDiscovery = () => {
    if (!editing.com_port.trim()) {
      setValidationMessage("COM port is required before discovery.");
      return;
    }
    if (scanRange.scanStart < 1 || scanRange.scanEnd > 247 || scanRange.scanEnd < scanRange.scanStart) {
      setValidationMessage("Discovery scan range must stay between 1 and 247, and end must be >= start.");
      return;
    }
    setValidationMessage(null);
    discoverMeters.mutate({
      com_port: editing.com_port,
      baud_rate: editing.baud_rate,
      parity: editing.parity,
      stop_bits: editing.stop_bits,
      byte_size: editing.byte_size,
      timeout: editing.timeout,
      one_based_map: editing.one_based_map,
      scanStart: scanRange.scanStart,
      scanEnd: scanRange.scanEnd,
    }, {
      onSuccess: (result) => {
        if (result.recommendedSlaveId) {
          setEditing((current) => ({ ...current, slave_id: result.recommendedSlaveId ?? current.slave_id }));
        }
      },
    });
  };

  const runSyncDetected = () => {
    if (!editing.com_port.trim()) {
      setValidationMessage("COM port is required before syncing detected meters.");
      return;
    }
    if (scanRange.scanStart < 1 || scanRange.scanEnd > 247 || scanRange.scanEnd < scanRange.scanStart) {
      setValidationMessage("Discovery scan range must stay between 1 and 247, and end must be >= start.");
      return;
    }
    setValidationMessage(null);
    syncDiscoveredMeters.mutate({
      com_port: editing.com_port,
      baud_rate: editing.baud_rate,
      parity: editing.parity,
      stop_bits: editing.stop_bits,
      byte_size: editing.byte_size,
      timeout: editing.timeout,
      one_based_map: editing.one_based_map,
      scanStart: scanRange.scanStart,
      scanEnd: scanRange.scanEnd,
    });
  };

  if (isLoading) {
    return <div className="page-state">Loading meters...</div>;
  }

  const onlineCount = meters.filter((meter) => meter.status === "online").length;
  const needsSetup = meters.length === 0 || onlineCount === 0;

  return (
    <section className="page-stack">
      <section className="page-state page-state--padded">
        <div className="section-heading">
          <div>
            <p className="section-label">Meter setup</p>
            <h3 className="page-title">Set up the line in a few simple steps</h3>
            <p className="page-copy">
              This page is designed for operators: enter line settings, scan the connected meters, then save names and locations.
            </p>
          </div>
          <button type="button" className="primary-button" onClick={startAdd}>
            Add or edit meter
          </button>
        </div>

        <div className="meters-summary">
          <div className="summary-card">
            <span className="summary-card__label">Total meters</span>
            <strong>{meters.length}</strong>
          </div>
          <div className="summary-card">
            <span className="summary-card__label">Talking now</span>
            <strong>{meters.filter((meter) => meter.status === "online").length}</strong>
          </div>
          <div className="summary-card">
            <span className="summary-card__label">Need attention</span>
            <strong>{meters.filter((meter) => meter.status === "warning").length}</strong>
          </div>
        </div>
      </section>

      <section className={`setup-guide ${needsSetup ? "setup-guide--highlight" : ""}`}>
        <div className="setup-guide__card">
          <span className="setup-guide__step">Step 1</span>
          <h4>Enter line settings</h4>
          <p>Fill in COM port, baud rate, parity, stop bits, byte size, and timeout.</p>
        </div>
        <div className="setup-guide__card">
          <span className="setup-guide__step">Step 2</span>
          <h4>Scan the daisy chain</h4>
          <p>Use the scan button to find which slave IDs are actually connected right now.</p>
        </div>
        <div className="setup-guide__card">
          <span className="setup-guide__step">Step 3</span>
          <h4>Sync active meters</h4>
          <p>The system will keep detected meters active for polling and turn off missing ones from that scan range.</p>
        </div>
        <div className="setup-guide__card">
          <span className="setup-guide__step">Step 4</span>
          <h4>Name the meters</h4>
          <p>Update the meter name, location, and SEU flag so reports and dashboard labels are easy to understand.</p>
        </div>
      </section>

      <section className="dashboard__split">
        <div className="panel">
          <div className="section-heading">
            <div>
              <p className="section-label">Detected and saved meters</p>
              <h4>Current meter list</h4>
            </div>
          </div>
          <MeterTable
            meters={meters}
            selectedMeterId={selectedMeterId}
            onSelect={onSelectMeter}
            onEdit={startEdit}
            onDelete={remove}
          />
        </div>

        <MeterEditorForm
          mode={mode}
          value={editing}
          scanStart={scanRange.scanStart}
          scanEnd={scanRange.scanEnd}
          onChange={setEditing}
          onScanRangeChange={setScanRange}
          onSubmit={submit}
          onCancel={() => {
            setMode("add");
            setEditing(emptyMeter());
            setValidationMessage(null);
          }}
          onDiscover={runDiscovery}
          onSyncDetected={runSyncDetected}
          saving={saveMeter.isPending}
          discovering={discoverMeters.isPending}
          syncingDetected={syncDiscoveredMeters.isPending}
          errorMessage={validationMessage ?? (saveMeter.error instanceof Error ? saveMeter.error.message : null)}
          discoveryErrorMessage={
            validationMessage ??
            (discoverMeters.error instanceof Error
              ? discoverMeters.error.message
              : syncDiscoveredMeters.error instanceof Error
                ? syncDiscoveredMeters.error.message
                : null)
          }
          discoveryResult={discoverMeters.data ?? null}
          syncResult={syncDiscoveredMeters.data ?? null}
        />
      </section>

      <section className="page-state page-state--padded">
        <p className="section-label">Selected meter</p>
        <h4 className="page-title">{selectedMeter?.meter_name ?? "No meter selected"}</h4>
        <p className="page-copy">
          {selectedMeter
            ? `${selectedMeter.location} - ${selectedMeter.manufacturer} ${selectedMeter.model} - ${formatNumber(selectedMeter.base_power, 2)} kW base load`
            : "Choose a meter from the table to review or edit it."}
        </p>
      </section>

      {selectedMeter ? (
        <AlertRulesPanel
          meterId={selectedMeter.meter_id}
          meterName={selectedMeter.meter_name}
          parameters={parameters}
          rules={alertRules}
          onSave={(input) => reportMutations.saveAlertRule.mutate(input)}
          onDelete={(ruleId) => reportMutations.deleteAlertRule.mutate(ruleId)}
          saving={reportMutations.saveAlertRule.isPending}
          errorMessage={reportMutations.saveAlertRule.error instanceof Error ? reportMutations.saveAlertRule.error.message : null}
        />
      ) : null}
    </section>
  );
}
