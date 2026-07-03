import { useMemo, useState } from "react";
import { formatNumber } from "../../lib/formatters";
import type { AlertRule, AlertRuleInput, ParameterMeta } from "../../types/energy";

type AlertRulesPanelProps = {
  meterId: string;
  meterName: string;
  parameters: ParameterMeta[];
  rules: AlertRule[];
  onSave: (input: AlertRuleInput) => void;
  onDelete: (ruleId: number) => void;
  saving: boolean;
  errorMessage?: string | null;
};

const emptyForm = {
  parameterKey: "",
  minValue: "",
  maxValue: "",
  enabled: true,
};

export function AlertRulesPanel({ meterId, meterName, parameters, rules, onSave, onDelete, saving, errorMessage }: AlertRulesPanelProps) {
  const [form, setForm] = useState(emptyForm);

  const numericParameters = useMemo(
    () => parameters.filter((parameter) => parameter.dataType === "number").sort((left, right) => left.order - right.order),
    [parameters],
  );

  const submit = () => {
    onSave({
      meterId,
      parameterKey: form.parameterKey,
      minValue: form.minValue === "" ? null : Number(form.minValue),
      maxValue: form.maxValue === "" ? null : Number(form.maxValue),
      enabled: form.enabled,
    });
  };

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="section-label">Alerts</p>
          <h4>{meterName ? `${meterName} threshold rules` : "Threshold rules"}</h4>
        </div>
      </div>

      {errorMessage ? <div className="page-state page-state--error page-state--padded">{errorMessage}</div> : null}

      <div className="dashboard__split">
        <div className="panel">
          <div className="table-shell">
            <table className="latest-table latest-table--compact">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>Status</th>
                  <th>Last value</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.length === 0 ? (
                  <tr>
                    <td colSpan={6}>No alert rules configured for this meter.</td>
                  </tr>
                ) : (
                  rules.map((rule) => (
                    <tr key={rule.id}>
                      <td className="latest-table__parameter">
                        <strong>{rule.parameterLabel}</strong>
                        <div className="table-subtle">{rule.parameterKey}</div>
                      </td>
                      <td>{rule.minValue !== null ? formatNumber(rule.minValue, 2) : "n/a"}</td>
                      <td>{rule.maxValue !== null ? formatNumber(rule.maxValue, 2) : "n/a"}</td>
                      <td>
                        <span className={`status-pill status-pill--${rule.isActive ? "warning" : "online"}`}>
                          {rule.isActive ? "Active" : "Normal"}
                        </span>
                      </td>
                      <td>{rule.lastValue !== null ? `${formatNumber(rule.lastValue, 2)} ${rule.unit}`.trim() : "n/a"}</td>
                      <td>
                        <div className="row-actions">
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={() =>
                              setForm({
                                parameterKey: rule.parameterKey,
                                minValue: rule.minValue === null ? "" : String(rule.minValue),
                                maxValue: rule.maxValue === null ? "" : String(rule.maxValue),
                                enabled: rule.enabled,
                              })
                            }
                          >
                            Load
                          </button>
                          <button type="button" className="ghost-button ghost-button--danger" onClick={() => onDelete(rule.id)}>
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <p className="page-copy">
            Set parameter-specific min/max ranges. Alerts trigger only when a value crosses the configured range and clear when
            it comes back within limits.
          </p>

          <div className="editor__grid">
            <label className="editor__field">
              <span>Parameter</span>
              <select value={form.parameterKey} onChange={(event) => setForm((current) => ({ ...current, parameterKey: event.target.value }))}>
                <option value="">Select parameter</option>
                {numericParameters.map((parameter) => (
                  <option key={parameter.key} value={parameter.key}>
                    {parameter.label} {parameter.unit ? `(${parameter.unit})` : ""}
                  </option>
                ))}
              </select>
            </label>

            <label className="editor__field">
              <span>Minimum value</span>
              <input
                type="number"
                value={form.minValue}
                onChange={(event) => setForm((current) => ({ ...current, minValue: event.target.value }))}
                placeholder="Leave blank if unused"
              />
            </label>

            <label className="editor__field">
              <span>Maximum value</span>
              <input
                type="number"
                value={form.maxValue}
                onChange={(event) => setForm((current) => ({ ...current, maxValue: event.target.value }))}
                placeholder="Leave blank if unused"
              />
            </label>

            <label className="editor__field editor__field--inline">
              <span>Enabled</span>
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(event) => setForm((current) => ({ ...current, enabled: event.target.checked }))}
              />
            </label>
          </div>

          <div className="editor__actions">
            <button type="button" className="ghost-button" onClick={() => setForm(emptyForm)}>
              Reset
            </button>
            <button type="button" className="primary-button" onClick={submit} disabled={saving || !meterId || !form.parameterKey}>
              {saving ? "Saving..." : "Save alert rule"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
