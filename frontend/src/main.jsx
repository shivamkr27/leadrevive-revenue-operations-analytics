import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  LayoutDashboard,
  Workflow,
  ListFilter,
  ShieldCheck,
  Settings,
  ArrowUpRight,
  ArrowRight,
  ArrowLeft,
  Download,
  Plus,
  Search,
  ChevronLeft,
  ChevronRight,
  X,
  Check,
  Clock3,
  Users,
  IndianRupee,
  Target,
  Activity,
  Upload,
  FileCheck2,
  AlertCircle,
  CircleHelp,
  Sprout,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import "./styles.css";
import AutomationConsole, { LeadEmailPreview } from "./AutomationConsole.jsx";
import Analytics from "./Analytics.jsx";
import Reports from "./Reports.jsx";

const SOURCES = ["Web", "Referral", "Event", "InboundEmail", "Manual"];
const STAGES = [
  "New",
  "Contacted",
  "Qualified",
  "Meeting",
  "Proposal",
  "Won",
  "Lost",
];
const currency = (v) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(v ?? 0);
const percent = (v) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const date = (v) =>
  v
    ? new Intl.DateTimeFormat("en-IN", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Asia/Kolkata",
      }).format(new Date(v))
    : "Not scheduled";
const localInput = (v) =>
  v
    ? new Date(new Date(v).getTime() + 19800000).toISOString().slice(0, 16)
    : "";
const utcInput = (v) => (v ? new Date(`${v}:00+05:30`).toISOString() : null);

async function api(url, options = {}) {
  const response = await fetch(`/api${url}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(
        `Request failed (${response.status}). Check that the local backend is running.`,
      );
    }
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  }
  return response.json();
}
function useRemote(url, revision = 0) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true, data: null, error: "" });
    api(url, { signal: controller.signal })
      .then((data) => setState({ loading: false, data, error: "" }))
      .catch((e) => {
        if (e.name !== "AbortError")
          setState({ loading: false, data: null, error: e.message });
      });
    return () => controller.abort();
  }, [url, revision]);
  return state;
}
function Loading() {
  return (
    <div className="empty" role="status">
      <RefreshCw className="spin" size={23} />
      <h3>Loading your workspace</h3>
      <p>Reading the latest database records.</p>
    </div>
  );
}
function ErrorBox({ message, retry }) {
  return (
    <div className="error" role="alert">
      <AlertCircle size={20} />
      <div>
        <strong>Something needs attention</strong>
        <p>{message}</p>
        {retry && (
          <button className="text-button" onClick={retry}>
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
function Badge({ children, tone = "" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function Stage({ stage }) {
  return (
    <span className={`stage stage-${stage.toLowerCase()}`}>
      <i />
      {stage}
    </span>
  );
}
function Help({ text }) {
  return (
    <span
      className="help"
      role="img"
      tabIndex="0"
      aria-label={text}
      title={text}
    >
      <CircleHelp size={13} />
    </span>
  );
}
function Modal({ title, onClose, children }) {
  const ref = useRef();
  useEffect(() => {
    ref.current.showModal();
    return () => ref.current?.close();
  }, []);
  return (
    <dialog ref={ref} onCancel={onClose} aria-label={title}>
      <div className="modal-top">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
function App() {
  const [page, setPage] = useState("overview"),
    [selected, setSelected] = useState(null),
    [revision, setRevision] = useState(0),
    [newLead, setNewLead] = useState(false),
    [toast, setToast] = useState("");
  const health = useRemote("/health", revision),
    owners = useRemote("/owners", revision);
  const navigate = (name) => {
    setSelected(null);
    setPage(name);
  };
  const changed = (message) => {
    setRevision((v) => v + 1);
    setToast(message);
  };
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  const title = selected
    ? "Lead detail"
    : {
        overview: "Executive overview",
        queue: "Recovery queue",
        quality: "Data quality",
        automations: "Automations",
        analytics: "Analytics",
        reports: "Reports",
        settings: "Workspace settings",
      }[page];
  return (
    <div className="app-shell">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">
        <button className="brand" onClick={() => navigate("overview")}>
          <span className="brand-icon">
            <Sprout size={24} />
          </span>
          <span>
            LeadRevive<span className="brand-sub">REVENUE OPERATIONS</span>
          </span>
        </button>
        <div className="workspace">
          <span className="workspace-avatar">LR</span>
          <span>
            <strong>Demo workspace</strong>
            <small>B2B services · India</small>
          </span>
          <Badge tone="muted">LOCAL</Badge>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {[
            ["overview", LayoutDashboard, "Overview"],
            ["queue", ListFilter, "Recovery queue"],
            ["quality", ShieldCheck, "Data quality"],
            ["automations", Workflow, "Automations"],
            ["analytics", Target, "Analytics"],
            ["reports", FileCheck2, "Reports"],
            ["settings", Settings, "Settings"],
          ].map(([id, Icon, label]) => (
            <button
              key={id}
              className={page === id ? "nav-item active" : "nav-item"}
              onClick={() => navigate(id)}
              aria-current={page === id ? "page" : undefined}
            >
              <Icon size={18} />
              {label}
              {page === id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <div className="note-icon">
            <ShieldCheck size={18} />
          </div>
          <strong>Safe by design</strong>
          <p>
            Synthetic records only.
            <br />
            External email is disabled.
          </p>
        </div>
        <div className="sidebar-bottom">
          <span className="user-avatar">DA</span>
          <div>
            <strong>Demo analyst</strong>
            <small>Local single-user workspace</small>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{title}</strong>
          </div>
          <div className="top-status">
            <Badge tone="synthetic">SYNTHETIC DATA</Badge>
            <span className="connection">
              <i className={health.data ? "connected" : ""} />
              {health.data ? "Local database connected" : "Checking database"}
            </span>
            <button
              className="icon-button"
              aria-label="Refresh workspace data"
              onClick={() => setRevision((v) => v + 1)}
            >
              <RefreshCw size={15} />
            </button>
          </div>
        </header>
        <main id="main" tabIndex="-1">
          {health.error && (
            <ErrorBox
              message={health.error}
              retry={() => setRevision((v) => v + 1)}
            />
          )}
          {selected ? (
            <LeadDetail
              id={selected}
              owners={owners.data || []}
              revision={revision}
              onChange={changed}
              onBack={() => setSelected(null)}
            />
          ) : page === "overview" ? (
            <Overview
              revision={revision}
              health={health.data}
              openLead={setSelected}
              navigate={navigate}
            />
          ) : page === "queue" ? (
            <Queue
              revision={revision}
              owners={owners.data || []}
              openLead={setSelected}
              onNew={() => setNewLead(true)}
            />
          ) : page === "quality" ? (
            <Quality
              revision={revision}
              onChange={changed}
              openLead={(id) => {
                setPage("queue");
                setSelected(id);
              }}
            />
          ) : page === "analytics" ? (
            <Analytics revision={revision} tools={{useRemote,Loading,ErrorBox}} />
          ) : page === "reports" ? (
            <Reports revision={revision} tools={{api,useRemote,Loading,ErrorBox}} />
          ) : page === "automations" ? (
            <AutomationConsole
              revision={revision}
              onChange={changed}
              tools={{ api, useRemote, Loading, ErrorBox, Badge, date }}
            />
          ) : (
            <SettingsPage revision={revision} onChange={changed} />
          )}
          <footer>
            <span>
              LeadRevive <span className="footer-dot">·</span> Revenue
              Operations &amp; Lead Recovery Intelligence
            </span>
            <span>
              Asia/Kolkata ·{" "}
              {health.data?.fixed_clock
                ? "Fixed demo clock"
                : "Live evaluation clock"}
              {health.data && ` · ${date(health.data.as_of_utc)}`}
            </span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={18} />
          {toast}
        </div>
      )}
      {newLead && (
        <NewLead
          owners={owners.data || []}
          onClose={() => setNewLead(false)}
          onCreated={(id) => {
            setNewLead(false);
            changed("Synthetic lead created");
            setSelected(id);
          }}
        />
      )}
    </div>
  );
}
function PageHeading({ eyebrow, title, description, children }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="heading-actions">{children}</div>
    </div>
  );
}
function Overview({ revision, health, openLead, navigate }) {
  const [source, setSource] = useState(""),
    [period, setPeriod] = useState("all");
  let start = "1900-01-01T00:00:00Z";
  if (period !== "all" && health)
    start = new Date(
      new Date(health.as_of_utc).getTime() - Number(period) * 86400000,
    ).toISOString();
  const query = new URLSearchParams({ source, start });
  const { data, loading, error } = useRemote(`/overview?${query}`, revision);
  return (
    <>
      <PageHeading
        eyebrow="REVENUE INTELLIGENCE"
        title="A clearer view. A stronger follow-up."
        description="Understand your pipeline exposure and focus on the leads that need you."
      >
        <button
          className="button secondary"
          onClick={() => navigate("quality")}
        >
          <Upload size={16} />
          Import leads
        </button>
        <button className="button primary" onClick={() => navigate("queue")}>
          Open recovery queue
          <ArrowUpRight size={17} />
        </button>
      </PageHeading>
      <div className="context-line">
        <div className="context-pill">
          <i />
          Synthetic portfolio case <span>·</span> Estimated values in INR
        </div>
        <div className="inline-filters">
          <label className="sr-only" htmlFor="overview-source">
            Overview source
          </label>
          <select
            id="overview-source"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="">All sources</option>
            {SOURCES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <label className="sr-only" htmlFor="overview-period">
            Creation cohort
          </label>
          <select
            id="overview-period"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          >
            <option value="all">All-time cohort</option>
            <option value="90">Last 90 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </div>
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : (
        <>
          <div className="kpi-grid">
            {[
              [
                "Total leads",
                data.kpis.new_leads,
                Users,
                `${data.kpis.contacted} contacted · ${data.kpis.uncontacted} uncontacted`,
                "Distinct accepted leads in the selected creation cohort.",
              ],
              [
                "Median first response",
                data.kpis.median_first_response_hours == null
                  ? "—"
                  : `${data.kpis.median_first_response_hours.toFixed(1)}h`,
                Clock3,
                `${percent(data.kpis.first_response_coverage)} response coverage`,
                "Median elapsed hours for contacted leads only; uncontacted leads excluded.",
              ],
              [
                "Overdue follow-ups",
                data.kpis.overdue,
                Activity,
                `${data.kpis.overdue} of ${data.kpis.active_scheduled} scheduled open leads`,
                "Open leads with next action strictly before evaluation time. Missing schedules are excluded.",
              ],
              [
                "Qualified rate",
                percent(data.kpis.qualified_rate),
                Target,
                `${data.kpis.qualified} of ${data.kpis.new_leads} cohort leads`,
                "Unique leads ever evidenced Qualified, Meeting, Proposal or Won, divided by cohort leads.",
              ],
              [
                "Pipeline exposure",
                currency(data.kpis.pipeline_exposure_inr),
                IndianRupee,
                "Estimated opportunity value · not lost revenue",
                "Sum of estimated open deal values for overdue leads. Includes unassigned leads.",
              ],
            ].map(([label, value, Icon, sub, help], i) => (
              <article
                className={`kpi-card ${i === 4 ? "exposure" : ""}`}
                key={label}
              >
                <div className="kpi-label">
                  {label}
                  <Help text={help} />
                  <Icon size={17} />
                </div>
                <div className="kpi-value">{value}</div>
                <div className="kpi-sub">{sub}</div>
              </article>
            ))}
          </div>
          <div className="insight-strip">
            <span className="insight-icon">
              <Target size={21} />
            </span>
            <div>
              <strong>Your next best operational move</strong>
              <p>
                {data.kpis.overdue} overdue follow-ups need attention.{" "}
                {data.unassigned} open leads have no owner, and{" "}
                {data.missing_schedule} have no next action.
              </p>
            </div>
            <button className="text-button" onClick={() => navigate("queue")}>
              Review the queue <ArrowRight size={16} />
            </button>
          </div>
          <div className="overview-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Lead inflow</h2>
                  <p>Accepted leads by creation week</p>
                </div>
                <Badge tone="muted">Last 8 weeks</Badge>
              </div>
              <div
                className="bar-chart"
                role="img"
                aria-label={`Weekly lead inflow: ${data.trend.map((t) => `${t.week}: ${t.leads}`).join(", ")}`}
              >
                {data.trend.map((t) => (
                  <div className="bar-column" key={t.week}>
                    <span>{t.leads}</span>
                    <div className="bar-track">
                      <div
                        style={{
                          height: `${Math.max(0, (t.leads / Math.max(1, ...data.trend.map((x) => x.leads))) * 100)}%`,
                        }}
                      />
                    </div>
                    <small>{t.week}</small>
                  </div>
                ))}
              </div>
              <div className="chart-caption">
                <span className="legend-dot" /> Lead count{" "}
                <span>Based on selected source and cohort</span>
              </div>
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Pipeline by stage</h2>
                  <p>Current state of the selected lead cohort</p>
                </div>
                <ListFilter size={18} />
              </div>
              <div className="stage-bars">
                {data.stages.map((s) => (
                  <div className="stage-row" key={s.stage}>
                    <span>{s.stage}</span>
                    <div className="horizontal-track">
                      <div
                        style={{
                          width: `${(s.count / Math.max(1, ...data.stages.map((x) => x.count))) * 100}%`,
                        }}
                        className={
                          s.stage === "Won"
                            ? "won"
                            : s.stage === "Lost"
                              ? "lost"
                              : ""
                        }
                      />
                    </div>
                    <strong>{s.count}</strong>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <div className="overview-bottom">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Follow-ups to focus on</h2>
                  <p>Overdue leads, ordered by transparent priority</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => navigate("queue")}
                >
                  View queue
                  <ArrowRight size={15} />
                </button>
              </div>
              <div className="focus-list">
                {data.urgent.length ? (
                  data.urgent.map((r) => (
                    <button
                      className="focus-row"
                      key={r.lead_id}
                      onClick={() => openLead(r.lead_id)}
                    >
                      <span className="company-avatar">
                        {r.company
                          .split(" ")
                          .map((w) => w[0])
                          .slice(0, 2)
                          .join("")}
                      </span>
                      <span>
                        <strong>{r.company}</strong>
                        <small>
                          {r.full_name} · {r.lead_source}
                        </small>
                      </span>
                      <span className="focus-score">
                        <Badge tone="warm">
                          {r.priority.score.toFixed(0)} priority
                        </Badge>
                        <small>{currency(r.estimated_deal_value_inr)}</small>
                      </span>
                      <ArrowUpRight size={16} />
                    </button>
                  ))
                ) : (
                  <div className="empty small">
                    <Check />
                    <p>No overdue follow-ups in this cohort.</p>
                  </div>
                )}
              </div>
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Source performance</h2>
                  <p>Where follow-up gaps appear</p>
                </div>
              </div>
              <div className="source-table">
                <div className="source-header">
                  <span>SOURCE</span>
                  <span>LEADS</span>
                  <span>OVERDUE</span>
                </div>
                {data.sources.map((s) => (
                  <div key={s.source}>
                    <span>
                      <i className="source-dot" />
                      {s.source}
                    </span>
                    <strong>{s.total}</strong>
                    <span>{s.overdue}</span>
                  </div>
                ))}
              </div>
              <div className="quality-link">
                <ShieldCheck size={16} />
                <span>
                  {data.unresolved_exceptions} exceptions await review
                </span>
                <button
                  aria-label="Review data quality"
                  onClick={() => navigate("quality")}
                >
                  <ArrowRight size={16} />
                </button>
              </div>
            </section>
          </div>
        </>
      )}
    </>
  );
}
function Queue({ revision, owners, openLead, onNew }) {
  const [filters, setFilters] = useState({
      q: "",
      stage: "",
      owner: "",
      source: "",
      priority_label: "",
      followup: "",
      open_only: "true",
      sort: "priority",
    }),
    [page, setPage] = useState(1);
  const update = (key, value) => {
    setFilters((v) => ({ ...v, [key]: value }));
    setPage(1);
  };
  const { data, loading, error } = useRemote(
    `/leads?${new URLSearchParams({ ...filters, page, page_size: 12 })}`,
    revision,
  );
  return (
    <>
      <PageHeading
        eyebrow="TAKE ACTION"
        title="Keep good opportunities moving."
        description="Prioritize, assign, and follow up. Every change is saved to your lead history."
      >
        <a className="button secondary" href="/api/leads/export">
          <Download size={16} />
          Export all leads
        </a>
        <button className="button primary" onClick={onNew}>
          <Plus size={17} />
          New synthetic lead
        </button>
      </PageHeading>
      <section className="panel queue-panel">
        <div className="queue-toolbar">
          <div className="search-input">
            <Search size={17} />
            <label className="sr-only" htmlFor="queue-search">
              Search leads
            </label>
            <input
              id="queue-search"
              placeholder="Search company, contact, or lead ID…"
              value={filters.q}
              onChange={(e) => update("q", e.target.value)}
            />
          </div>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={filters.open_only === "true"}
              onChange={(e) => update("open_only", String(e.target.checked))}
            />
            Open opportunities only
          </label>
        </div>
        <div className="queue-filters">
          <SlidersHorizontal size={16} />
          {[
            ["stage", "Stage", STAGES.map((x) => [x, x])],
            [
              "owner",
              "Owner",
              [
                ...owners.map((o) => [o.owner_id, o.name]),
                ["unassigned", "Unassigned"],
              ],
            ],
            ["source", "Source", SOURCES.map((x) => [x, x])],
            [
              "priority_label",
              "Priority",
              ["High", "Medium", "Low"].map((x) => [x, x]),
            ],
            [
              "followup",
              "Follow-up",
              [
                ["overdue", "Overdue"],
                ["missing", "Missing schedule"],
                ["scheduled", "Upcoming / due now"],
              ],
            ],
          ].map(([key, label, options]) => (
            <label key={key}>
              <span className="sr-only">Filter by {label.toLowerCase()}</span>
              <select
                aria-label={`Filter by ${label.toLowerCase()}`}
                value={filters[key]}
                onChange={(e) => update(key, e.target.value)}
              >
                <option value="">All {label.toLowerCase()}s</option>
                {options.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <label className="sort-select">
            <span>Sort:</span>
            <select
              aria-label="Sort leads"
              value={filters.sort}
              onChange={(e) => update("sort", e.target.value)}
            >
              <option value="priority">Priority score</option>
              <option value="value">Deal value</option>
              <option value="next_action">Next action</option>
              <option value="created">Oldest first</option>
            </select>
          </label>
        </div>
        {loading ? (
          <Loading />
        ) : error ? (
          <ErrorBox message={error} />
        ) : (
          <>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>COMPANY / CONTACT</th>
                    <th>STAGE</th>
                    <th>OWNER</th>
                    <th>EST. VALUE</th>
                    <th>FOLLOW-UP · IST</th>
                    <th>PRIORITY</th>
                    <th>
                      <span className="sr-only">Open lead</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((r) => (
                    <tr key={r.lead_id}>
                      <td>
                        <button
                          className="lead-name"
                          onClick={() => openLead(r.lead_id)}
                        >
                          {r.company}
                        </button>
                        <small>
                          {r.full_name} · {r.lead_source}
                        </small>
                      </td>
                      <td>
                        <Stage stage={r.stage} />
                      </td>
                      <td>
                        <span className={r.owner_id ? "" : "unassigned"}>
                          {owners.find((o) => o.owner_id === r.owner_id)
                            ?.name || "Unassigned"}
                        </span>
                      </td>
                      <td className="money">
                        {currency(r.estimated_deal_value_inr)}
                      </td>
                      <td>
                        <span className={r.overdue ? "overdue-date" : ""}>
                          {date(r.next_action_at)}
                        </span>
                        <small>{r.recommended_action}</small>
                      </td>
                      <td>
                        <Badge
                          tone={
                            r.priority_label === "High"
                              ? "warm"
                              : r.priority_label === "Medium"
                                ? "green"
                                : "muted"
                          }
                        >
                          {r.priority
                            ? `${r.priority.score.toFixed(0)} · `
                            : ""}
                          {r.priority_label}
                        </Badge>
                      </td>
                      <td>
                        <button
                          className="icon-button"
                          aria-label={`Open ${r.lead_id}`}
                          onClick={() => openLead(r.lead_id)}
                        >
                          <ArrowUpRight size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!data.items.length && (
              <div className="empty">
                <Search size={25} />
                <h3>No leads match these filters</h3>
                <p>
                  Adjust your search or reset filters to see more opportunities.
                </p>
                <button
                  className="button secondary"
                  onClick={() => {
                    setFilters({
                      q: "",
                      stage: "",
                      owner: "",
                      source: "",
                      priority_label: "",
                      followup: "",
                      open_only: "true",
                      sort: "priority",
                    });
                    setPage(1);
                  }}
                >
                  Reset filters
                </button>
              </div>
            )}
            <div className="pagination">
              <span>
                {data.total} matching leads ·{" "}
                {data.items.length
                  ? `${(page - 1) * 12 + 1}–${Math.min(page * 12, data.total)}`
                  : "0"}{" "}
                shown
              </span>
              <div>
                <button
                  className="icon-button"
                  aria-label="Previous page"
                  disabled={page === 1}
                  onClick={() => setPage((v) => v - 1)}
                >
                  <ChevronLeft size={18} />
                </button>
                <span>
                  Page {page} of {Math.max(1, Math.ceil(data.total / 12))}
                </span>
                <button
                  className="icon-button"
                  aria-label="Next page"
                  disabled={page * 12 >= data.total}
                  onClick={() => setPage((v) => v + 1)}
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
      <p className="footnote">
        <CircleHelp size={14} /> Priority is a rule-based action score, not a
        purchase probability. Open any lead to inspect its score and take
        action.
      </p>
    </>
  );
}
function LeadDetail({ id, owners, revision, onChange, onBack }) {
  const { data, loading, error } = useRemote(`/leads/${id}`, revision);
  return (
    <>
      <button className="back-link" onClick={onBack}>
        <ArrowLeft size={16} />
        Back to workspace
      </button>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : (
        <DetailContent
          key={`${id}-${data.version}-${revision}`}
          lead={data}
          owners={owners}
          onChange={onChange}
        />
      )}
    </>
  );
}
function DetailContent({ lead, owners, onChange }) {
  const [form, setForm] = useState({
      stage: lead.stage,
      owner_id: lead.owner_id || "",
      next_action_at: localInput(lead.next_action_at),
      lost_reason: lead.lost_reason || "",
      suppressed: lead.suppressed,
    }),
    [note, setNote] = useState(""),
    [kind, setKind] = useState("contacted"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [tab, setTab] = useState("activities");
  const update = (key, value) => setForm((v) => ({ ...v, [key]: value }));
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/leads/${lead.lead_id}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...form,
          version: lead.version,
          owner_id: form.owner_id || null,
          next_action_at: utcInput(form.next_action_at),
        }),
      });
      onChange("Lead changes saved");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function activity(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/leads/${lead.lead_id}/activity`, {
        method: "POST",
        body: JSON.stringify({ version: lead.version, kind, note }),
      });
      onChange(
        kind === "contacted"
          ? "Contact recorded. Schedule the next action if needed."
          : "Note added to timeline",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const events = lead.timeline.filter((e) =>
    tab === "audit"
      ? e.category === "audit_events"
      : e.category !== "audit_events",
  );
  return (
    <>
      <PageHeading
        eyebrow={`${lead.lead_id} · SYNTHETIC`}
        title={lead.company}
        description={`${lead.full_name} · ${lead.lead_source} · ${lead.campaign}`}
      >
        <Stage stage={lead.stage} />
        <Badge tone="muted">Version {lead.version}</Badge>
      </PageHeading>
      {error && <ErrorBox message={error} />}
      <div className="detail-layout">
        <div>
          <section className="panel detail-summary">
            <div className="panel-heading">
              <h2>Opportunity at a glance</h2>
              <Badge tone={lead.overdue ? "warm" : "green"}>
                {lead.overdue ? "Follow-up overdue" : "Follow-up tracked"}
              </Badge>
            </div>
            <dl className="detail-facts">
              <div>
                <dt>Estimated deal value</dt>
                <dd>{currency(lead.estimated_deal_value_inr)}</dd>
              </div>
              <div>
                <dt>Next action · IST</dt>
                <dd>{date(lead.next_action_at)}</dd>
              </div>
              <div>
                <dt>First response SLA</dt>
                <dd>
                  {lead.sla.breached ? "Breached" : "Within SLA"} ·{" "}
                  {lead.response_sla_hours} elapsed hours
                </dd>
              </div>
              <div>
                <dt>First response due · IST</dt>
                <dd>{date(lead.sla.due_at)}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{lead.email}</dd>
              </div>
              <div>
                <dt>Fictional phone</dt>
                <dd>{lead.phone}</dd>
              </div>
              <div>
                <dt>First contacted · IST</dt>
                <dd>
                  {lead.first_contacted_at
                    ? date(lead.first_contacted_at)
                    : "Not contacted"}
                </dd>
              </div>
              <div>
                <dt>Last contacted · IST</dt>
                <dd>
                  {lead.last_contacted_at
                    ? date(lead.last_contacted_at)
                    : "Not contacted"}
                </dd>
              </div>
            </dl>
            <div className="consent-note">
              <ShieldCheck size={17} />
              <span>
                Email consent:{" "}
                {lead.consent_to_email ? "recorded" : "not given"} · Email
                verified: {lead.email_verified ? "yes" : "no"}. Synthetic
                recipients cannot receive live email.
              </span>
            </div>
          </section>
          <section className="panel activity-panel">
            <div className="panel-heading">
              <div>
                <h2>Record a follow-up</h2>
                <p>A recorded contact is an action, not a recovered deal.</p>
              </div>
            </div>
            <form onSubmit={activity}>
              <div className="field">
                <label htmlFor="activity-kind">Activity type</label>
                <select
                  id="activity-kind"
                  value={kind}
                  onChange={(e) => setKind(e.target.value)}
                >
                  <option
                    value="contacted"
                    disabled={["Won", "Lost"].includes(lead.stage)}
                  >
                    Mark contacted
                  </option>
                  <option value="note">Internal note</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="activity-note">Activity note</label>
                <textarea
                  id="activity-note"
                  required
                  maxLength="2000"
                  placeholder="What happened, and what should happen next?"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
              </div>
              <button
                className="button primary"
                disabled={
                  busy ||
                  !note.trim() ||
                  (kind === "contacted" && ["Won", "Lost"].includes(lead.stage))
                }
              >
                <Check size={16} />
                {busy ? "Saving…" : "Record activity"}
              </button>
            </form>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>Lead timeline</h2>
              <div className="tabs">
                <button
                  className={tab === "activities" ? "selected" : ""}
                  onClick={() => setTab("activities")}
                >
                  Activities
                </button>
                <button
                  className={tab === "audit" ? "selected" : ""}
                  onClick={() => setTab("audit")}
                >
                  Audit history
                </button>
              </div>
            </div>
            <div className="timeline">
              {events.length ? (
                events.map((e) => (
                  <article key={e.event_id}>
                    <span className="timeline-dot" />
                    <div>
                      <div className="timeline-head">
                        <strong>{e.event_type.replaceAll("_", " ")}</strong>
                        <time>{date(e.created_at)}</time>
                      </div>
                      {e.details.note && <p>{e.details.note}</p>}
                      {e.details.after && (
                        <p>
                          {Object.entries(e.details.after)
                            .filter(
                              ([key]) =>
                                !["updated_at", "version"].includes(key),
                            )
                            .map(
                              ([key, value]) =>
                                `${key.replaceAll("_", " ")}: ${value == null ? "cleared" : key.endsWith("_at") ? date(value) : key === "owner_id" ? owners.find((o) => o.owner_id === value)?.name || value : typeof value === "boolean" ? (value ? "yes" : "no") : value}`,
                            )
                            .join(" · ")}
                        </p>
                      )}
                      <details>
                        <summary>View recorded evidence</summary>
                        <pre>{JSON.stringify(e.details, null, 2)}</pre>
                      </details>
                    </div>
                  </article>
                ))
              ) : (
                <div className="empty small">
                  No records in this timeline category.
                </div>
              )}
            </div>
          </section>
        </div>
        <div>
          <section className="panel manage-panel">
            <div className="panel-heading">
              <h2>Manage this lead</h2>
            </div>
            <form onSubmit={save}>
              <div className="field">
                <label htmlFor="lead-owner">Assigned owner</label>
                <select
                  id="lead-owner"
                  value={form.owner_id}
                  onChange={(e) => update("owner_id", e.target.value)}
                >
                  <option value="">Unassigned</option>
                  {owners.map((o) => (
                    <option key={o.owner_id} value={o.owner_id}>
                      {o.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="lead-stage">Sales stage</label>
                <select
                  id="lead-stage"
                  value={form.stage}
                  onChange={(e) => update("stage", e.target.value)}
                >
                  {STAGES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
              {form.stage === "Lost" && (
                <div className="field">
                  <label htmlFor="lost-reason">Lost reason</label>
                  <input
                    id="lost-reason"
                    required
                    value={form.lost_reason}
                    onChange={(e) => update("lost_reason", e.target.value)}
                  />
                </div>
              )}
              <div className="field">
                <label htmlFor="lead-next">Next action · Asia/Kolkata</label>
                <input
                  id="lead-next"
                  type="datetime-local"
                  value={form.next_action_at}
                  onChange={(e) => update("next_action_at", e.target.value)}
                />
                <small>Clear this field to remove the schedule.</small>
              </div>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={form.suppressed}
                  onChange={(e) => update("suppressed", e.target.checked)}
                />
                Suppress recovery reminders
              </label>
              <button className="button primary full" disabled={busy}>
                <Check size={16} />
                {busy ? "Saving…" : "Save lead changes"}
              </button>
            </form>
          </section>
          <LeadEmailPreview
            leadId={lead.lead_id}
            onChange={onChange}
            tools={{ api, useRemote, Loading, ErrorBox, Badge, date }}
          />
          <section className="panel score-panel">
            <div className="panel-heading">
              <div>
                <h2>Why this priority?</h2>
                <p>Transparent rules. No prediction.</p>
              </div>
            </div>
            {lead.priority ? (
              <>
                <div className="score-total">
                  {lead.priority.score.toFixed(1)}
                  <span>/ 100</span>
                  <Badge tone="green">{lead.priority_label}</Badge>
                </div>
                {Object.entries(lead.priority.breakdown).map(([key, value]) => (
                  <div className="score-factor" key={key}>
                    <span>{key}</span>
                    <strong>{value.toFixed(1)} pts</strong>
                  </div>
                ))}
                {lead.priority.missing.length > 0 && (
                  <p className="footnote">
                    Missing factors: {lead.priority.missing.join(", ")}. They
                    contribute zero.
                  </p>
                )}
                <div className="recommendation">
                  <Target size={18} />
                  <span>{lead.recommended_action}</span>
                </div>
              </>
            ) : (
              <p className="closed-note">
                Closed leads do not receive a recovery priority.
              </p>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
function Quality({ revision, onChange, openLead }) {
  const [status, setStatus] = useState("all"),
    [selected, setSelected] = useState(null),
    [file, setFile] = useState(null),
    [result, setResult] = useState(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const {
    data,
    loading,
    error: loadError,
  } = useRemote(`/quality?status=${status}`, revision);
  const current = data?.items.find((r) => r.rejection_id === selected);
  async function upload(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const imported = await api("/leads/import", {
        method: "POST",
        body: form,
      });
      setResult(imported);
      onChange(
        imported.replay
          ? "Already imported; no duplicate writes"
          : "Import complete. Review the results below.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="TRUST YOUR DATA"
        title="Good decisions start with clean leads."
        description="Inspect invalid records and identity collisions. Existing leads and original evidence stay intact."
      >
        <a className="button secondary" href="/api/quality/export">
          <Download size={16} />
          Export exceptions
        </a>
      </PageHeading>
      <section className="panel import-panel">
        <div className="import-icon">
          <Upload size={24} />
        </div>
        <div>
          <h2>Import synthetic leads</h2>
          <p>
            CSV · up to 2 MB · consent is never inferred. Use the generated
            project CSV.
          </p>
        </div>
        <form onSubmit={upload}>
          <label className="sr-only" htmlFor="import-file">
            Choose synthetic CSV
          </label>
          <input
            id="import-file"
            type="file"
            accept=".csv,text/csv"
            required
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button className="button primary" disabled={!file || busy}>
            {busy ? "Importing…" : "Import CSV"}
            <ArrowUpRight size={16} />
          </button>
        </form>
      </section>
      {error && <ErrorBox message={error} />}{" "}
      {result && (
        <div className="import-result" role="status">
          <FileCheck2 size={20} />
          <strong>
            {result.replay ? "Existing import recognized" : "Import processed"}
          </strong>
          <span>
            {result.accepted} accepted · {result.invalid} invalid ·{" "}
            {result.duplicates} duplicates · {result.review_required} conflicts
          </span>
        </div>
      )}
      {loading ? (
        <Loading />
      ) : loadError ? (
        <ErrorBox message={loadError} />
      ) : (
        <>
          <div className="quality-stats">
            <span>
              <strong>{data.total}</strong> Total exceptions
            </span>
            <span>
              <strong>{data.pending}</strong> Awaiting review
            </span>
            <span>
              <strong>{data.total - data.pending}</strong> Reviewed
            </span>
            <label>
              <span className="sr-only">Exception status</span>
              <select
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setSelected(null);
                }}
              >
                <option value="all">All exceptions</option>
                <option value="pending">Awaiting review</option>
                <option value="reviewed">Reviewed</option>
              </select>
            </label>
          </div>
          <div className="quality-layout">
            <section className="panel">
              <div className="panel-heading">
                <h2>Validation &amp; identity review</h2>
                <Badge tone="muted">{data.items.length} records</Badge>
              </div>
              <div className="exception-list">
                {data.items.length ? (
                  data.items.map((r) => (
                    <button
                      key={r.rejection_id}
                      className={`exception-item ${selected === r.rejection_id ? "selected" : ""}`}
                      onClick={() => setSelected(r.rejection_id)}
                    >
                      <span className="exception-symbol">
                        {r.reason.includes("collision") ? (
                          <Users size={18} />
                        ) : (
                          <AlertCircle size={18} />
                        )}
                      </span>
                      <span>
                        <strong>
                          {r.raw.company || r.raw.full_name || "Invalid record"}
                        </strong>
                        <small>
                          Row {r.row_number} · {r.reason}
                        </small>
                      </span>
                      <Badge tone={r.review ? "green" : "warm"}>
                        {r.review ? "Reviewed" : "Review"}
                      </Badge>
                    </button>
                  ))
                ) : (
                  <div className="empty">
                    <ShieldCheck />
                    <h3>No exceptions here</h3>
                    <p>Import a fixture or change the status filter.</p>
                  </div>
                )}
              </div>
            </section>
            <section className="panel review-panel">
              {current ? (
                <ExceptionReview
                  key={current.rejection_id}
                  item={current}
                  onChange={onChange}
                  openLead={openLead}
                />
              ) : (
                <div className="empty">
                  <ShieldCheck size={30} />
                  <h3>Review with confidence</h3>
                  <p>
                    Select a record to compare identities, inspect validation
                    errors, and record a decision.
                  </p>
                  <Badge tone="muted">No automatic merging</Badge>
                </div>
              )}
            </section>
          </div>
          <section className="panel batch-panel">
            <div className="panel-heading">
              <h2>Import history</h2>
              <p>Each file is identified by its content hash.</p>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>IMPORTED · IST</th>
                    <th>ACCEPTED</th>
                    <th>INVALID</th>
                    <th>DUPLICATES</th>
                    <th>CONFLICTS</th>
                    <th>FILE HASH</th>
                  </tr>
                </thead>
                <tbody>
                  {data.batches.map((b) => (
                    <tr key={b.batch_id}>
                      <td>{date(b.created_at)}</td>
                      <td>{b.summary.accepted}</td>
                      <td>{b.summary.invalid}</td>
                      <td>{b.summary.duplicates}</td>
                      <td>{b.summary.review_required}</td>
                      <td>
                        <code title={b.sha256}>{b.sha256.slice(0, 16)}…</code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  );
}
function ExceptionReview({ item, onChange, openLead }) {
  const [note, setNote] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const collision =
    item.reason.includes("collision") || item.reason.includes("duplicate");
  async function review(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/quality/${item.rejection_id}/review`, {
        method: "POST",
        body: JSON.stringify({
          decision: collision ? "keep_existing" : "discard_invalid",
          note,
        }),
      });
      onChange("Review decision saved. Original evidence preserved.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="panel-heading">
        <div>
          <h2>Record inspection</h2>
          <p>Input row {item.row_number}</p>
        </div>
        <Badge tone="warm">
          {collision ? "Identity review" : "Validation error"}
        </Badge>
      </div>
      <div className="review-content">
        <div className="review-reason">
          <AlertCircle size={18} />
          <p>{item.reason}</p>
        </div>
        <h3>Incoming record</h3>
        <dl className="record-facts">
          {[
            "lead_id",
            "full_name",
            "company",
            "email",
            "phone",
            "stage",
            "estimated_deal_value_inr",
          ].map((key) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>{item.raw[key] || "(empty)"}</dd>
            </div>
          ))}
        </dl>
        {item.candidates.length > 0 && (
          <>
            <h3>Existing candidate records</h3>
            {item.candidates.map((c) => (
              <div className="candidate" key={c.lead_id}>
                <button
                  className="lead-name"
                  onClick={() => openLead(c.lead_id)}
                >
                  {c.company}
                  <ArrowUpRight size={14} />
                </button>
                <p>
                  {c.full_name}
                  <br />
                  {c.email}
                  <br />
                  {c.phone}
                </p>
              </div>
            ))}
          </>
        )}
        {item.review ? (
          <div className="reviewed">
            <ShieldCheck size={20} />
            <h3>Decision recorded</h3>
            <strong>{item.review.decision.replaceAll("_", " ")}</strong>
            <p>{item.review.note}</p>
            <small>{date(item.review.reviewed_at)}</small>
          </div>
        ) : (
          <form onSubmit={review}>
            <div className="field">
              <label htmlFor="review-note">Decision note</label>
              <textarea
                id="review-note"
                required
                minLength="3"
                maxLength="2000"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Explain why this record is excluded…"
              />
            </div>
            <p className="footnote">
              {collision
                ? "Keeps existing lead data and history; excludes this incoming row. No fields are merged."
                : "Excludes the invalid row. Correct the source and reimport it as a new file if needed."}
            </p>
            {error && <ErrorBox message={error} />}
            <button
              className="button primary full"
              disabled={busy || note.trim().length < 3}
            >
              <Check size={16} />
              {busy
                ? "Saving…"
                : collision
                  ? "Keep existing · record decision"
                  : "Discard invalid · record decision"}
            </button>
          </form>
        )}
        <details>
          <summary>Original source evidence</summary>
          <pre>{JSON.stringify(item.raw, null, 2)}</pre>
        </details>
      </div>
    </>
  );
}
function SettingsPage({ revision, onChange }) {
  const state = useRemote("/settings", revision);
  return (
    <>
      <PageHeading
        eyebrow="WORKSPACE CONTROLS"
        title="Clear rules. Consistent decisions."
        description="Configure response expectations and transparent prioritization for this local workspace."
      />
      {state.loading ? (
        <Loading />
      ) : state.error ? (
        <ErrorBox message={state.error} />
      ) : (
        <SettingsForm
          key={state.data.version}
          data={state.data}
          onChange={onChange}
        />
      )}
    </>
  );
}
function SettingsForm({ data, onChange }) {
  const transport = useRemote("/automations/status");
  const [sla, setSla] = useState(data.response_sla_hours),
    [weights, setWeights] = useState(data.scoring_weights),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const total = Object.values(weights).reduce((a, b) => a + Number(b), 0);
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/settings", {
        method: "PUT",
        body: JSON.stringify({
          version: data.version,
          response_sla_hours: Number(sla),
          scoring_weights: Object.fromEntries(
            Object.entries(weights).map(([k, v]) => [k, Number(v)]),
          ),
        }),
      });
      onChange("Workspace rules updated");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="settings-layout">
      <form className="panel settings-form" onSubmit={save}>
        <div className="panel-heading">
          <div>
            <h2>Response &amp; priority rules</h2>
            <p>Changes are recorded in the workspace audit log.</p>
          </div>
        </div>
        <div className="settings-body">
          <div className="field">
            <label htmlFor="sla-hours">
              First-response SLA · elapsed hours
            </label>
            <input
              id="sla-hours"
              type="number"
              min="1"
              max="720"
              required
              value={sla}
              onChange={(e) => setSla(e.target.value)}
            />
            <small>
              Applied to new manually created leads. Existing leads retain their
              stored SLA. CSV imports use each row’s SLA. Weekends count.
            </small>
          </div>
          <div className="section-divider" />
          <h3>Priority score weights</h3>
          <p>Weights must total 100. Queue scores recalculate immediately.</p>
          {Object.entries(weights).map(([key, value]) => (
            <div className="weight-field" key={key}>
              <label htmlFor={`weight-${key}`}>{key}</label>
              <input
                id={`weight-${key}`}
                type="number"
                min="0"
                max="100"
                step="0.1"
                required
                value={value}
                onChange={(e) =>
                  setWeights((v) => ({ ...v, [key]: e.target.value }))
                }
              />
              <span>points</span>
            </div>
          ))}
          <div className={`weight-total ${total !== 100 ? "invalid" : ""}`}>
            <strong>Total weight</strong>
            <strong>{total} / 100</strong>
          </div>
          {error && <ErrorBox message={error} />}
          <button className="button primary" disabled={busy || total !== 100}>
            <Check size={16} />
            {busy ? "Saving…" : "Save workspace rules"}
          </button>
        </div>
      </form>
      <div>
        <section className="panel safety-panel">
          <ShieldCheck size={28} />
          <h2>Safe test environment</h2>
          <Badge tone="green">DRY RUN ONLY</Badge>
          <dl>
            <div>
              <dt>External email</dt>
              <dd>Disabled</dd>
            </div>
            <div>
              <dt>SMTP connection</dt>
              <dd>
                {transport.data?.services.mailpit.reachable
                  ? "Mailpit reachable"
                  : "Mailpit offline / checking"}
              </dd>
            </div>
            <div>
              <dt>Data origin</dt>
              <dd>Synthetic</dd>
            </div>
            <div>
              <dt>Business timezone</dt>
              <dd>Asia/Kolkata</dd>
            </div>
            <div>
              <dt>Automation</dt>
              <dd>
                {transport.data?.services.n8n.reachable
                  ? "n8n reachable"
                  : "n8n offline / checking"}
              </dd>
            </div>
          </dl>
          <p>
            Internal test notifications and explicitly approved previews can be
            captured by Mailpit. External sending is disabled.
          </p>
        </section>
        <AuditLog />
      </div>
    </div>
  );
}
function AuditLog() {
  const [show, setShow] = useState(false);
  const state = useRemote("/audit");
  return (
    <section className="panel audit-panel">
      <div className="panel-heading">
        <h2>Workspace audit</h2>
        <button className="text-button" onClick={() => setShow((v) => !v)}>
          {show ? "Hide" : "Show latest"}
        </button>
      </div>
      {show &&
        (state.loading ? (
          <Loading />
        ) : state.error ? (
          <ErrorBox message={state.error} />
        ) : (
          <div className="audit-entries">
            {state.data.map((r) => (
              <div key={r.event_id}>
                <strong>{r.event_type.replaceAll("_", " ")}</strong>
                <small>{date(r.created_at)}</small>
                <details>
                  <summary>Evidence</summary>
                  <pre>{JSON.stringify(r.details, null, 2)}</pre>
                </details>
              </div>
            ))}
          </div>
        ))}
    </section>
  );
}
function NewLead({ owners, onClose, onCreated }) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(new FormData(event.target));
    values.owner_id = values.owner_id || null;
    values.next_action_at = utcInput(values.next_action_at);
    try {
      const row = await api("/leads", {
        method: "POST",
        body: JSON.stringify(values),
      });
      onCreated(row.lead_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Create a synthetic lead" onClose={onClose}>
      <form onSubmit={save} className="new-lead-form">
        <p className="form-intro">
          Use fictional identities, a reserved .example email, and a
          FICTIONAL-IN- phone token. Consent defaults to false.
        </p>
        <div className="form-grid">
          {[
            ["full_name", "Contact name", "text", "Fictional Contact"],
            ["company", "Company", "text", "Synthetic Business"],
            ["email", "Email", "email", "contact@business.example"],
            ["phone", "Fictional phone", "text", "FICTIONAL-IN-DEMO-001"],
            [
              "estimated_deal_value_inr",
              "Estimated deal value · INR",
              "number",
              "100000",
            ],
          ].map(([name, label, type, placeholder]) => (
            <div className="field" key={name}>
              <label htmlFor={`new-${name}`}>{label}</label>
              <input
                autoFocus={name === "full_name"}
                id={`new-${name}`}
                name={name}
                type={type}
                placeholder={placeholder}
                required
                min={type === "number" ? "0" : undefined}
                step={type === "number" ? "0.01" : undefined}
              />
            </div>
          ))}
          <div className="field">
            <label htmlFor="new-source">Lead source</label>
            <select id="new-source" name="lead_source" defaultValue="Manual">
              {SOURCES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="new-owner">Assigned owner</label>
            <select id="new-owner" name="owner_id">
              <option value="">Unassigned</option>
              {owners.map((o) => (
                <option key={o.owner_id} value={o.owner_id}>
                  {o.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="new-next">Next action · Asia/Kolkata</label>
            <input id="new-next" name="next_action_at" type="datetime-local" />
          </div>
        </div>
        {error && <ErrorBox message={error} />}
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="button primary" disabled={busy}>
            {busy ? "Creating…" : "Create lead"}
            <Plus size={16} />
          </button>
        </div>
      </form>
    </Modal>
  );
}

createRoot(document.getElementById("root")).render(<App />);
