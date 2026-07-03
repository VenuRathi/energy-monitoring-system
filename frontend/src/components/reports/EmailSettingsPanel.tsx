import { useEffect, useState } from "react";
import { formatTimestamp } from "../../lib/formatters";
import type { EmailHealth, EmailSettings, EmailSettingsInput } from "../../types/energy";

type EmailSettingsPanelProps = {
  settings?: EmailSettings | null;
  health?: EmailHealth | null;
  saving: boolean;
  testing: boolean;
  saveError?: string | null;
  testError?: string | null;
  testResultMessage?: string | null;
  onSave: (input: EmailSettingsInput) => void;
  onSendTest: (recipientEmails: string[]) => void;
};

export function EmailSettingsPanel({
  settings,
  health,
  saving,
  testing,
  saveError,
  testError,
  testResultMessage,
  onSave,
  onSendTest,
}: EmailSettingsPanelProps) {
  const [smtpHost, setSmtpHost] = useState("");
  const [smtpPort, setSmtpPort] = useState("587");
  const [smtpUsername, setSmtpUsername] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [smtpFromEmail, setSmtpFromEmail] = useState("");
  const [smtpUseTls, setSmtpUseTls] = useState(true);
  const [smtpUseSsl, setSmtpUseSsl] = useState(false);
  const [testRecipients, setTestRecipients] = useState("");

  useEffect(() => {
    if (!settings) {
      return;
    }

    setSmtpHost(settings.smtpHost ?? "");
    setSmtpPort(String(settings.smtpPort ?? 587));
    setSmtpUsername(settings.smtpUsername ?? "");
    setSmtpPassword("");
    setSmtpFromEmail(settings.smtpFromEmail ?? "");
    setSmtpUseTls(settings.smtpUseTls ?? true);
    setSmtpUseSsl(settings.smtpUseSsl ?? false);
  }, [settings]);

  const submitSettings = () => {
    onSave({
      smtpHost: smtpHost.trim(),
      smtpPort: Number(smtpPort || "587"),
      smtpUsername: smtpUsername.trim(),
      smtpPassword: smtpPassword.trim() || undefined,
      smtpFromEmail: smtpFromEmail.trim(),
      smtpUseTls,
      smtpUseSsl,
    });
  };

  const submitTest = () => {
    const recipients = testRecipients
      .split(/[\n,;]+/)
      .map((value) => value.trim())
      .filter(Boolean);
    onSendTest(recipients);
  };

  return (
    <section className="page-stack">
      <div className={`email-health ${health?.configured ? "email-health--ok" : "email-health--warning"}`}>
        <strong>{health?.configured ? "SMTP ready" : "SMTP not configured"}</strong>
        <span>
          Source: {health?.source ?? settings?.source ?? "env"} | {health?.message ?? "Waiting for SMTP configuration."}
        </span>
        {settings?.updatedAt ? <span>Updated: {formatTimestamp(settings.updatedAt)}</span> : null}
      </div>

      {saveError ? <div className="page-state page-state--error page-state--padded">{saveError}</div> : null}
      {testError ? <div className="page-state page-state--error page-state--padded">{testError}</div> : null}
      {testResultMessage ? <div className="page-state page-state--padded">{testResultMessage}</div> : null}

      <div className="editor__grid">
        <label className="editor__field">
          <span>SMTP host</span>
          <input value={smtpHost} onChange={(event) => setSmtpHost(event.target.value)} placeholder="smtp.office365.com" />
        </label>

        <label className="editor__field">
          <span>SMTP port</span>
          <input type="number" value={smtpPort} onChange={(event) => setSmtpPort(event.target.value)} min="1" />
        </label>

        <label className="editor__field">
          <span>Username</span>
          <input value={smtpUsername} onChange={(event) => setSmtpUsername(event.target.value)} placeholder="alerts@example.com" />
        </label>

        <label className="editor__field">
          <span>Password</span>
          <input
            type="password"
            value={smtpPassword}
            onChange={(event) => setSmtpPassword(event.target.value)}
            placeholder={settings?.hasPassword ? "Leave blank to keep existing password" : "Enter SMTP password"}
          />
        </label>

        <label className="editor__field">
          <span>From email</span>
          <input value={smtpFromEmail} onChange={(event) => setSmtpFromEmail(event.target.value)} placeholder="alerts@example.com" />
        </label>

        <div className="editor__field editor__field--group">
          <span>Security</span>
          <label className="editor__check">
            <input
              type="checkbox"
              checked={smtpUseTls}
              onChange={(event) => {
                const checked = event.target.checked;
                setSmtpUseTls(checked);
                if (checked) {
                  setSmtpUseSsl(false);
                }
              }}
            />
            <span>Use TLS</span>
          </label>
          <label className="editor__check">
            <input
              type="checkbox"
              checked={smtpUseSsl}
              onChange={(event) => {
                const checked = event.target.checked;
                setSmtpUseSsl(checked);
                if (checked) {
                  setSmtpUseTls(false);
                }
              }}
            />
            <span>Use SSL</span>
          </label>
        </div>
      </div>

      <div className="editor__actions">
        <button type="button" className="primary-button" onClick={submitSettings} disabled={saving}>
          {saving ? "Saving..." : "Save email settings"}
        </button>
      </div>

      <div className="editor__grid">
        <label className="editor__field">
          <span>Test recipients</span>
          <textarea
            className="editor__textarea"
            value={testRecipients}
            onChange={(event) => setTestRecipients(event.target.value)}
            placeholder="ops@example.com, admin@example.com"
          />
        </label>
      </div>

      <div className="editor__actions">
        <button type="button" className="ghost-button" onClick={submitTest} disabled={testing || testRecipients.trim().length === 0}>
          {testing ? "Sending..." : "Send test email"}
        </button>
      </div>
    </section>
  );
}
