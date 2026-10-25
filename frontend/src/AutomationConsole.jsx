import React, { useState } from "react";
import {
  Workflow,
  Mail,
  ShieldCheck,
  RefreshCw,
  Play,
  Download,
  ArrowUpRight,
  Check,
  AlertCircle,
} from "lucide-react";

const fresh = () => crypto.randomUUID();

export function LeadEmailPreview({ leadId, onChange, tools }) {
  const { api, useRemote, Loading, ErrorBox, Badge } = tools;
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const drafts = useRemote("/notifications");
  const latest = drafts.data?.find(
    (r) => r.lead_id === leadId && r.kind === "external_preview",
  );
  async function prepare() {
    setBusy(true);
    setError("");
    try {
      await api(`/leads/${leadId}/email-draft`, { method: "POST" });
      onChange(
        "Mailpit-only preview prepared. Review and approve it in Automations.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel preview-card">
      <div className="panel-heading">
        <div>
          <h2>Follow-up email preview</h2>
          <p>Separate review and approval. Local sink only.</p>
        </div>
        <Mail size={18} />
      </div>
      <div className="preview-card-body">
        <p>
          Prepare a factual follow-up using this lead’s stored details. Approval
          permits a test capture in Mailpit, never an email to the lead.
        </p>
        {error && <ErrorBox message={error} />}
        <button
          className="button secondary full"
          onClick={prepare}
          disabled={busy}
        >
          {busy ? "Preparing…" : "Prepare Mailpit preview"}
        </button>
        {latest && (
          <>
            <Badge tone="muted">{latest.status.replaceAll("_", " ")}</Badge>
            <pre>{latest.body}</pre>
            <p>
              Review this message under{" "}
              <strong>Automations → Notification outbox</strong>.
            </p>
          </>
        )}
      </div>
    </section>
  );
}

export default function AutomationConsole({ revision, onChange, tools }) {
  const { api, useRemote, Loading, ErrorBox, Badge, date } = tools;
  const [refresh, setRefresh] = useState(0),
    [selected, setSelected] = useState(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [ack, setAck] = useState(false),
    [cancelNote, setCancelNote] = useState(""),
    [filter, setFilter] = useState("all");
  const status = useRemote("/automations/status", revision + refresh),
    runs = useRemote("/automations/runs", revision + refresh),
    drafts = useRemote("/notifications", revision + refresh);
  const current = drafts.data?.find((r) => r.draft_id === selected);
  async function action(url, body, message) {
    setBusy(true);
    setError("");
    try {
      const result = await api(url, {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (
        result.status &&
        result.status !== "succeeded" &&
        result.status !== "approved" &&
        result.status !== "cancelled"
      )
        throw new Error(
          result.error || "Workflow needs attention. Inspect the recorded run.",
        );
      onChange(message);
      setAck(false);
      setCancelNote("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      setRefresh((v) => v + 1);
    }
  }
  const filtered = (drafts.data || []).filter(
    (r) =>
      filter === "all" ||
      (filter === "needs_review" && r.status === "pending_approval") ||
      (filter === "retry" && ["failed", "uncertain"].includes(r.status)) ||
      (filter === "sent" && r.status === "sent_to_sink"),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">WORKFLOW AUTOMATION</div>
          <h1>Follow through, without losing control.</h1>
          <p>
            Real n8n orchestration, durable reminders, and approval-controlled
            Mailpit captures.
          </p>
        </div>
        <div className="heading-actions">
          <button
            className="button secondary"
            disabled={busy}
            onClick={() =>
              action(
                "/automations/recovery",
                { idempotency_key: fresh() },
                "n8n recovery scan completed. Review the run and owner digests below.",
              )
            }
          >
            <Play size={16} />
            Run recovery workflow
          </button>
          <button
            className="button primary"
            disabled={busy}
            onClick={() =>
              action(
                "/notifications/dispatch",
                { idempotency_key: fresh() },
                "n8n outbox workflow completed. Only queued internal or approved test messages were eligible.",
              )
            }
          >
            <Mail size={16} />
            Process approved outbox
          </button>
        </div>
      </div>
      {error && <ErrorBox message={error} />}
      <div className="automation-status-grid">
        <section className="panel service-card">
          <Workflow size={22} />
          <div>
            <h2>n8n orchestration</h2>
            <p>
              {status.data?.services.n8n.reachable
                ? "Service reachable"
                : "Service unreachable / checking"}
            </p>
          </div>
          <Badge tone={status.data?.services.n8n.reachable ? "green" : "warm"}>
            {status.data?.services.n8n.reachable
              ? "Reachable"
              : "Check service"}
          </Badge>
        </section>
        <section className="panel service-card">
          <Mail size={22} />
          <div>
            <h2>Mailpit test sink</h2>
            <p>
              {status.data?.services.mailpit.reachable
                ? "Local capture service reachable"
                : "Capture service unreachable / checking"}
            </p>
          </div>
          <Badge
            tone={status.data?.services.mailpit.reachable ? "green" : "warm"}
          >
            {status.data?.services.mailpit.reachable
              ? "Reachable"
              : "Check service"}
          </Badge>
        </section>
        <section className="panel service-card">
          <ShieldCheck size={22} />
          <div>
            <h2>External email</h2>
            <p>No live transport is implemented.</p>
          </div>
          <Badge tone="muted">Disabled</Badge>
        </section>
      </div>
      {status.error && <ErrorBox message={status.error} />}
      <div className="automation-context">
        <div>
          <ClockDescription />
          <p>
            Hourly recovery and five-minute outbox checks run only while n8n is
            running and workflows are published. Manual buttons above also
            execute the real n8n workflows.
          </p>
        </div>
        <div className="heading-actions">
          <a
            className="text-button"
            href="http://127.0.0.1:5678"
            target="_blank"
            rel="noreferrer"
          >
            Open n8n
            <ArrowUpRight size={15} />
          </a>
          <a
            className="text-button"
            href="http://127.0.0.1:8025"
            target="_blank"
            rel="noreferrer"
          >
            Open Mailpit
            <ArrowUpRight size={15} />
          </a>
        </div>
      </div>
      <section className="panel run-panel">
        <div className="panel-heading">
          <div>
            <h2>Automation run history</h2>
            <p>
              Last 100 backend jobs. n8n execution IDs connect these records to
              workflow history.
            </p>
          </div>
          <button
            className="icon-button"
            aria-label="Refresh automation records"
            onClick={() => setRefresh((v) => v + 1)}
          >
            <RefreshCw size={16} />
          </button>
        </div>
        {runs.loading ? (
          <Loading />
        ) : runs.error ? (
          <ErrorBox message={runs.error} />
        ) : runs.data.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>WORKFLOW / N8N EXECUTION</th>
                  <th>STARTED · IST</th>
                  <th>STATUS</th>
                  <th>PROCESSED</th>
                  <th>SKIPPED</th>
                  <th>FAILED</th>
                  <th>ATTEMPTS</th>
                </tr>
              </thead>
              <tbody>
                {runs.data.map((r) => (
                  <tr key={r.run_id}>
                    <td>
                      <strong>{r.workflow.replaceAll("_", " ")}</strong>
                      <small>
                        n8n:{" "}
                        {r.execution_id || "Trigger unavailable / direct test"}{" "}
                        · {r.run_id.slice(0, 8)}
                      </small>
                      {r.error && (
                        <details>
                          <summary>Failure detail</summary>
                          <p className="run-error">{r.error}</p>
                        </details>
                      )}
                    </td>
                    <td>{date(r.started_at)}</td>
                    <td>
                      <Badge tone={r.status === "succeeded" ? "green" : "warm"}>
                        {r.status}
                      </Badge>
                    </td>
                    <td>{r.processed}</td>
                    <td>{r.skipped}</td>
                    <td>{r.failed}</td>
                    <td>{r.attempts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty">
            <Workflow size={26} />
            <h3>No automation runs yet</h3>
            <p>
              Run recovery to create real owner digests from eligible overdue
              leads.
            </p>
          </div>
        )}
      </section>
      <div className="outbox-header">
        <div>
          <h2>Notification outbox</h2>
          <p>
            One digest per owner. Exact-content approval for contact previews.
          </p>
        </div>
        <label>
          <span className="sr-only">Filter notification outbox</span>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All notifications</option>
            <option value="needs_review">Needs approval</option>
            <option value="retry">Failed / uncertain</option>
            <option value="sent">Sent to test sink</option>
          </select>
        </label>
      </div>
      <div className="outbox-layout">
        <section className="panel outbox-list">
          {drafts.loading ? (
            <Loading />
          ) : drafts.error ? (
            <ErrorBox message={drafts.error} />
          ) : filtered.length ? (
            filtered.map((r) => (
              <button
                className={`outbox-item ${selected === r.draft_id ? "selected" : ""}`}
                key={r.draft_id}
                onClick={() => {
                  setSelected(r.draft_id);
                  setAck(false);
                }}
              >
                <span className="exception-symbol">
                  <Mail size={17} />
                </span>
                <span>
                  <strong>{r.subject}</strong>
                  <small>
                    {r.kind.replaceAll("_", " ")} · {date(r.created_at)}
                  </small>
                </span>
                <Badge tone={r.status === "sent_to_sink" ? "green" : "warm"}>
                  {r.status.replaceAll("_", " ")}
                </Badge>
              </button>
            ))
          ) : (
            <div className="empty">
              <Mail size={26} />
              <h3>No notifications in this view</h3>
              <p>
                Run recovery for internal reminders, or prepare a Mailpit
                preview from an open lead.
              </p>
            </div>
          )}
        </section>
        <section className="panel notification-detail">
          {current ? (
            <>
              <div className="panel-heading">
                <h2>Review message &amp; delivery</h2>
                <Badge tone="muted">MAILPIT ONLY</Badge>
              </div>
              <div className="notification-body">
                <h3>{current.subject}</h3>
                <dl className="record-facts">
                  <div>
                    <dt>Intended contact</dt>
                    <dd>
                      {current.intended_recipient}
                      <small>
                        Reference only. This address is never used as an
                        external envelope.
                      </small>
                    </dd>
                  </div>
                  <div>
                    <dt>Actual test inbox</dt>
                    <dd>{current.sink_recipient}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{current.status.replaceAll("_", " ")}</dd>
                  </div>
                </dl>
                <pre className="message-preview">{current.body}</pre>
                {current.kind === "external_preview" && (
                  <div className="policy-note">
                    <ShieldCheck size={18} />
                    <div>
                      <strong>Live delivery is blocked</strong>
                      <ul>
                        {current.live_block_reasons.map((reason) => (
                          <li key={reason}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
                {current.status === "pending_approval" && (
                  <>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={ack}
                        onChange={(e) => setAck(e.target.checked)}
                      />
                      I approve this exact content for a local Mailpit preview
                      only.
                    </label>
                    <button
                      className="button primary full"
                      disabled={!ack || busy}
                      onClick={() =>
                        action(
                          `/email-drafts/${current.draft_id}/approve`,
                          { version: current.version, sink_only: true },
                          "Exact-content approval recorded for Mailpit only.",
                        )
                      }
                    >
                      <Check size={16} />
                      Approve Mailpit preview
                    </button>
                  </>
                )}
                {current.approval && (
                  <div className="approval-record">
                    <ShieldCheck size={17} />
                    <span>
                      Approved by {current.approval.approved_by} ·{" "}
                      {date(current.approval.approved_at)}
                      <small>
                        Content hash:{" "}
                        {current.approval.approved_hash.slice(0, 16)}… · Mailpit
                        only
                      </small>
                    </span>
                  </div>
                )}
                {current.status === "approved" && (
                  <button
                    className="button primary full"
                    disabled={busy}
                    onClick={() =>
                      action(
                        `/email-drafts/${current.draft_id}/send`,
                        { idempotency_key: fresh(), mode: "mailpit" },
                        "Approved preview processed through n8n and the Mailpit-only delivery ledger.",
                      )
                    }
                  >
                    <Mail size={16} />
                    Send approved preview to Mailpit
                  </button>
                )}
                {current.status === "queued" && (
                  <button
                    className="button secondary full"
                    disabled={busy}
                    onClick={() =>
                      action(
                        "/notifications/dispatch",
                        {
                          idempotency_key: fresh(),
                          draft_ids: [current.draft_id],
                        },
                        "Internal notification processed through n8n.",
                      )
                    }
                  >
                    <Mail size={16} />
                    Send this test notification
                  </button>
                )}
                {["failed", "uncertain"].includes(current.status) && (
                  <button
                    className="button secondary full"
                    disabled={busy || current.delivery?.attempts >= 3}
                    onClick={() =>
                      action(
                        "/notifications/dispatch",
                        {
                          idempotency_key: fresh(),
                          draft_ids: [current.draft_id],
                          force_retry: true,
                        },
                        "Delivery retry/reconciliation completed. Inspect the recorded outcome.",
                      )
                    }
                  >
                    <RefreshCw size={16} />
                    {current.status === "uncertain"
                      ? "Reconcile uncertain acceptance"
                      : "Retry failed sink delivery"}
                  </button>
                )}
                {current.delivery && (
                  <div className="delivery-record">
                    <h3>Delivery ledger</h3>
                    <p>
                      {current.delivery.status === "accepted"
                        ? "SMTP accepted by local sink. This is not a claim of external inbox delivery."
                        : current.delivery.error || current.delivery.status}
                    </p>
                    <dl className="record-facts">
                      <div>
                        <dt>Attempts</dt>
                        <dd>{current.delivery.attempts} / 3</dd>
                      </div>
                      <div>
                        <dt>Mailpit capture</dt>
                        <dd>
                          {current.delivery.sink_message_id
                            ? "Verified in Mailpit"
                            : "Not verified"}
                        </dd>
                      </div>
                      <div>
                        <dt>Message-ID</dt>
                        <dd>{current.delivery.message_id}</dd>
                      </div>
                      {current.delivery.retry_at && (
                        <div>
                          <dt>Retry eligible · IST</dt>
                          <dd>{date(current.delivery.retry_at)}</dd>
                        </div>
                      )}
                    </dl>
                  </div>
                )}
                {[
                  "pending_approval",
                  "queued",
                  "approved",
                  "failed",
                  "uncertain",
                ].includes(current.status) && (
                  <div className="cancel-notification">
                    <div className="field">
                      <label htmlFor="cancel-notification-note">
                        Cancellation note
                      </label>
                      <textarea
                        id="cancel-notification-note"
                        value={cancelNote}
                        maxLength={500}
                        onChange={(e) => setCancelNote(e.target.value)}
                        placeholder="Explain why this test message should be cancelled…"
                      />
                    </div>
                    <button
                      className="button secondary full"
                      disabled={busy || cancelNote.trim().length < 3}
                      onClick={() =>
                        action(
                          `/notifications/${current.draft_id}/cancel`,
                          { note: cancelNote.trim() },
                          "Test notification cancelled. Original approval and delivery evidence retained.",
                        )
                      }
                    >
                      Cancel pending test message
                    </button>
                  </div>
                )}
                {["cancelled", "stale"].includes(current.status) && (
                  <p className="footnote">
                    This message is no longer eligible. Lead changes, completed
                    follow-ups, closure, reassignment or suppression can cancel
                    stale work. Prepare a fresh preview if needed.
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="empty">
              <ShieldCheck size={28} />
              <h3>Preview before proceeding</h3>
              <p>
                Select a notification to inspect its content, approval and
                delivery evidence.
              </p>
            </div>
          )}
        </section>
      </div>
      <section className="panel workflow-downloads">
        <div>
          <h2>Original n8n workflows</h2>
          <p>
            Exports contain credential references only. Select your local
            credential after importing elsewhere.
          </p>
        </div>
        {[
          ["intake", "W1 · Intake"],
          ["overdue_recovery", "W2 · Recovery"],
          ["email_approval", "W3 · Outbox"],
          ["status_sync", "Status sync"],
        ].map(([file, label]) => (
          <a
            key={file}
            className="button secondary"
            href={`/api/automations/workflows/${file}`}
          >
            <Download size={14} />
            {label}
          </a>
        ))}
      </section>
    </>
  );
}
function ClockDescription() {
  return <strong>Visible, repeatable local operations</strong>;
}
