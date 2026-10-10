import React, { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";

const WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dayLabel = (d) => { const x = new Date(d + "T00:00:00Z"); return `${WD[x.getUTCDay()]}, ${d.slice(8, 10)} ${MO[x.getUTCMonth()]}`; };

const P = {
  cal: "M8 3v3M16 3v3M4 9h16M5 5h14v15H5z", search: "M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-4-4",
  file: "M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 16h5", users: "M9 11a3 3 0 100-6 3 3 0 000 6zM3 20c0-3 3-5 6-5s6 2 6 5M17 6a3 3 0 010 6M18 15c2 .5 3 2 3 5",
  clock: "M12 4a8 8 0 100 16 8 8 0 000-16zM12 8v4l3 2", user: "M12 12a4 4 0 100-8 4 4 0 000 8zM4 21c0-4 4-6 8-6s8 2 8 6",
};
const Icon = ({ n }) => <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={P[n]} /></svg>;

const Badge = ({ kind, children }) => <span className={"badge " + kind}>{children}</span>;
const Cert = ({ c }) => (c ? <Badge kind="info">{c}</Badge> : <span className="muted">none</span>);
const Reasons = ({ list }) => <ul className="reasons">{list.map((v, i) => <li key={i}>{v.message}</li>)}</ul>;
const mins = (t) => +t.slice(11, 13) * 60 + +t.slice(14, 16);
const kindOf = (h) => (h >= 5 && h < 13 ? ["morning", "Morning"] : h >= 13 && h < 21 ? ["evening", "Evening"] : ["night", "Night"]);
function When({ s }) {
  const a = mins(s.start), b = mins(s.end), cross = s.end.slice(0, 10) !== s.start.slice(0, 10);
  const [k, name] = kindOf(Math.floor(a / 60));
  const segs = cross ? [[a, 1440], [0, b]] : [[a, b]];
  return (
    <div className="when" title={name + " shift"}>
      <div>{dayLabel(s.start.slice(0, 10))}</div>
      <div className={"strip " + k} aria-hidden="true">{segs.map(([x, y], i) => <i key={i} style={{ left: (x / 1440) * 100 + "%", width: ((y - x) / 1440) * 100 + "%" }} />)}</div>
      <small><span className={"kind " + k} />{s.start.slice(11)} – {s.end.slice(11)}{cross ? " (+1 day)" : ""}</small>
    </div>
  );
}

function Card({ id, title, count, unit, tone = "blue", right, children }) {
  return (
    <section className="card" id={id}>
      <div className="card-h"><h2>{title}</h2>{count !== undefined && <span className={"pill " + tone}>{count} {unit}</span>}<div className="sp" />{right}</div>
      {children}
    </section>
  );
}

function Tbl({ head, count, empty, children }) {
  if (!count) return <p className="empty">{empty}</p>;
  const rows = React.Children.map(children, (tr) => tr && React.cloneElement(tr, {}, React.Children.map(tr.props.children, (td, i) => React.cloneElement(td, { "data-label": head[i] }))));
  return <div className="tbl"><table><thead><tr>{head.map((h, i) => <th key={i}>{h}</th>)}</tr></thead><tbody>{rows}</tbody></table></div>;
}

const Tile = ({ tone, icon, value, label }) => <div className={"tile " + tone}><span className="ti"><Icon n={icon} /></span><b>{value}</b><span>{label}</span></div>;

const fh = (n) => Number(n.toFixed(2));

const exportCsv = (rows) => {
  const esc = (v) => `"${String(v == null ? "" : v).replace(/"/g, '""')}"`;
  const lines = [["Time", "Who", "Action", "Shift", "Outcome", "Details"].map(esc).join(",")]
    .concat(rows.map((h) => [h.at, h.actor_name, h.action, h.shift_id, h.outcome, h.detail].map(esc).join(",")));
  const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url; a.download = "shiftswap-history.csv"; a.click();
  URL.revokeObjectURL(url);
};

function Meter({ label, hours }) {
  return (
    <div className="meter">
      <div className="meter-h"><span>{label}</span><b>{fh(hours)} / 40h</b></div>
      <div className="bar" role="progressbar" aria-label={label} aria-valuenow={fh(hours)} aria-valuemin="0" aria-valuemax="40">
        <i className={hours > 40 ? "over" : hours === 40 ? "full" : ""} style={{ width: Math.min(100, (hours / 40) * 100) + "%" }} />
      </div>
    </div>
  );
}

function People({ staff, onAdd }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("STAFF");
  const [certs, setCerts] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    const list = role === "MANAGER" ? [] : certs.split(",").map((c) => c.trim()).filter(Boolean);
    if (await onAdd(name.trim(), role, list)) { setName(""); setRole("STAFF"); setCerts(""); }
  };
  return (
    <Card id="people" title="People" count={staff.length} unit="people" tone="blue">
      <form className="addform" onSubmit={submit}>
        <label>Name<input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Kavya" required maxLength={60} /></label>
        <label>Role<select value={role} onChange={(e) => setRole(e.target.value)}><option value="STAFF">Staff</option><option value="MANAGER">Manager</option></select></label>
        <label>Certifications<input value={certs} onChange={(e) => setCerts(e.target.value)} placeholder="ICU, PEDS (optional)" disabled={role === "MANAGER"} /></label>
        <button type="submit">Add person</button>
      </form>
      <Tbl head={["ID", "Name", "Role", "Certifications"]} count={staff.length} empty="">
        {staff.map((p) => (
          <tr key={p.id}>
            <td className="id">{p.id}</td><td>{p.name}</td>
            <td><Badge kind={p.role === "MANAGER" ? "warn" : "info"}>{p.role === "MANAGER" ? "Manager" : "Staff"}</Badge></td>
            <td>{p.certifications.length ? p.certifications.map((c) => <Badge key={c} kind="info">{c}</Badge>) : <span className="muted">none</span>}</td>
          </tr>
        ))}
      </Tbl>
    </Card>
  );
}

function History({ items }) {
  const [f, setF] = useState("all");
  const rows = f === "refused" ? items.filter((h) => h.outcome === "REFUSED") : items;
  return (
    <Card id="history" title="Action history" count={rows.length} unit="actions" tone="purple"
      right={<div className="tools"><button className="ghost sm" onClick={() => exportCsv(rows)} disabled={!rows.length}>Export CSV</button><label className="filter">Filter <select value={f} onChange={(e) => setF(e.target.value)}><option value="all">All actions</option><option value="refused">Refused only</option></select></label></div>}>
      <Tbl head={["Time", "Who", "Action", "Shift", "Outcome", "Details"]} count={rows.length} empty="No actions to show yet.">
        {rows.map((h) => (
          <tr key={h.id}>
            <td className="nw">{h.at.replace("T", " ")}</td><td>{h.actor_name}</td><td>{h.action}</td><td className="id">{h.shift_id || ""}</td>
            <td>{h.outcome === "SUCCESS" ? <Badge kind="ok">Success</Badge> : <Badge kind="err">Refused</Badge>}</td>
            <td className="wrap muted">{h.detail}</td>
          </tr>
        ))}
      </Tbl>
    </Card>
  );
}

export default function App() {
  const [staff, setStaff] = useState([]);
  const [actorId, setActorId] = useState(localStorage.getItem("shiftswap.actor") || "");
  const [me, setMe] = useState({ shifts: [], claims: [], weeks: [] });
  const [open, setOpen] = useState([]);
  const [queue, setQueue] = useState([]);
  const [history, setHistory] = useState([]);
  const [msg, setMsg] = useState(null);
  const [active, setActive] = useState("");
  const [fCert, setFCert] = useState("all");
  const [fDay, setFDay] = useState("all");
  const [fOk, setFOk] = useState(false);

  const actor = staff.find((p) => p.id === actorId);
  const isMgr = !!actor && actor.role === "MANAGER";

  const refresh = useCallback(async () => {
    try {
      setHistory(await api.history());
      if (!actor) return;
      if (actor.role === "STAFF") {
        const [m, o] = await Promise.all([api.me(actor.id), api.open(actor.id)]);
        setMe(m); setOpen(o);
      } else setQueue(await api.claimed(actor.id));
    } catch (e) { setMsg({ ok: false, message: e.message || "Could not load data", violations: [] }); }
  }, [actor]);

  useEffect(() => { api.staff().then(setStaff).catch(() => setMsg({ ok: false, message: "Backend not reachable. Is it running on port 8000?", violations: [] })); }, []);
  useEffect(() => { refresh(); const i = setInterval(refresh, 5000); return () => clearInterval(i); }, [refresh]);
  useEffect(() => { if (msg && msg.ok) { const t = setTimeout(() => setMsg(null), 4500); return () => clearTimeout(t); } }, [msg]);

  const act = async (fn, okMessage) => {
    let ok = false;
    try { await fn(); setMsg({ ok: true, message: okMessage }); ok = true; }
    catch (e) { setMsg({ ok: false, message: e.message || "Action failed", violations: e.violations || [] }); }
    refresh();
    return ok;
  };
  const addPerson = (name, role, certs) => act(async () => { await api.addPerson(actor.id, name, role, certs); setStaff(await api.staff()); }, `Added ${name}`);
  const pick = (id) => { setActorId(id); localStorage.setItem("shiftswap.actor", id); setMsg(null); setActive(""); };
  const go = (k) => { setActive(k); const el = document.getElementById(k); if (el) el.scrollIntoView({ behavior: "smooth", block: "start" }); };

  const certOpts = [...new Set(open.map((l) => l.shift.required_certification || "none"))];
  const dayOpts = [...new Set(open.map((l) => l.shift.start.slice(0, 10)))].sort();
  const shown = open.filter((l) => (fCert === "all" || (l.shift.required_certification || "none") === fCert) && (fDay === "all" || l.shift.start.slice(0, 10) === fDay) && (!fOk || l.can_claim));

  const nav = !actor ? [] : isMgr
    ? [["queue", "Manager Approvals", "users"], ["people", "People", "user"], ["history", "History", "clock"]]
    : [["shifts", "My Shifts", "cal"], ["open", "Available Shifts", "search"], ["claims", "My Claims", "file"], ["history", "History", "clock"]];

  const tiles = !actor ? [] : isMgr
    ? [["orange", "clock", queue.length, "Pending claims"], ["green", "users", queue.filter((l) => l.can_approve).length, "Ready to approve"], ["red", "file", queue.filter((l) => !l.can_approve).length, "Would be refused"]]
    : [["orange", "clock", me.claims.length, "Pending claims"], ["blue", "cal", me.shifts.length, "My shifts"], ["green", "search", open.length, "Open listings"]];

  return (
    <>
      <header className="top">
        <div className="brand"><span className="mark"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 8h14l-3-3M20 16H6l3 3"/></svg></span><b>ShiftSwap</b><small>CityCare Clinic</small></div>
        <label className="who"><span>Acting as</span>
          <span className="sel"><Icon n="user" />
            <select value={actorId} onChange={(e) => pick(e.target.value)} aria-label="Acting as">
              <option value="">Choose a person</option>
              <optgroup label="Staff">{staff.filter((p) => p.role === "STAFF").map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</optgroup>
              <optgroup label="Managers">{staff.filter((p) => p.role === "MANAGER").map((p) => <option key={p.id} value={p.id}>{p.name} (Manager)</option>)}</optgroup>
            </select>
          </span>
        </label>
      </header>

      <div className="layout">
        <aside className="side"><nav aria-label="Sections">
          {nav.map(([k, label, ic]) => <button key={k} className={active === k ? "on" : ""} aria-current={active === k ? "true" : undefined} onClick={() => go(k)}><Icon n={ic} />{label}</button>)}
        </nav></aside>

        <main>
          <div className="hero">
            <div className="banner">
              {actor ? <><h1>Welcome, <em>{actor.name.split(" ")[0]}</em></h1><p>{isMgr ? "Manager" : "Staff"} • CityCare Clinic{!isMgr && actor.certifications.length ? " • " + actor.certifications.join(", ") : ""}</p></>
                : <><h1>Welcome to <em>ShiftSwap</em></h1><p>Pick a person below to see the roster from their side.</p></>}
            </div>
            {actor && <div className="tiles">{tiles.map(([t, i, v, l]) => <Tile key={l} tone={t} icon={i} value={v} label={l} />)}</div>}
          </div>

          {!actor && staff.length > 0 && (
            <Card id="pick" title="Who are you acting as?">
              <div className="picker">{staff.map((p) => (
                <button key={p.id} className={"person" + (p.role === "MANAGER" ? " mgr" : "")} onClick={() => pick(p.id)}>
                  <span className="av">{p.name[0]}</span><b>{p.name}</b>
                  <small>{p.role === "MANAGER" ? "Manager" : p.certifications.join(", ") || "Staff"}</small>
                </button>))}</div>
            </Card>
          )}

          {msg && (
            <div className={"alert " + (msg.ok ? "ok" : "err")} role={msg.ok ? "status" : "alert"}>
              <div><b>{msg.message}</b>{msg.violations && msg.violations.length > 0 && <Reasons list={msg.violations} />}</div>
              <button className="x" onClick={() => setMsg(null)} aria-label="Dismiss message">×</button>
            </div>
          )}

          {actor && !isMgr && (
            <>
              <Card id="hours" title="My weekly hours">
                <p className="note">Assigned shifts only, maximum 40h per week. Pending claims do not count until approved.</p>
                <div className="meters">{(me.weeks || []).map((w) => <Meter key={w.week_start} label={"Week of " + dayLabel(w.week_start)} hours={w.hours} />)}</div>
              </Card>

              <div className="two">
                <Card id="shifts" title="My shifts" count={me.shifts.length} unit="shifts" tone="blue">
                  <Tbl head={["Shift", "When", "Certification", "Listing", ""]} count={me.shifts.length} empty="You have no shifts on the roster.">
                    {me.shifts.map((s) => (
                      <tr key={s.id}>
                        <td className="id">{s.id}</td><td><When s={s} /></td><td><Cert c={s.required_certification} /></td>
                        <td>{!s.listing ? <span className="muted">Not listed</span> : s.listing.status === "OPEN" ? <Badge kind="info">Open</Badge> : <Badge kind="warn">Claimed by {s.listing.claimed_by_name}</Badge>}</td>
                        <td className="r">
                          {!s.listing && <button onClick={() => act(() => api.post(actor.id, s.id), `Posted ${s.id} for swap`)}>Post for swap</button>}
                          {s.listing && s.listing.status === "OPEN" && <button className="ghost" onClick={() => act(() => api.withdraw(actor.id, s.listing.id), `Withdrew ${s.id}`)}>Withdraw</button>}
                          {s.listing && s.listing.status === "CLAIMED" && <span className="muted">Awaiting manager</span>}
                        </td>
                      </tr>
                    ))}
                  </Tbl>
                </Card>

                <Card id="open" title="Open listings from colleagues" count={shown.length} unit={shown.length === 1 ? "listing" : "listings"} tone="green">
                  <div className="filters">
                    <label>Certification<select value={fCert} onChange={(e) => setFCert(e.target.value)}><option value="all">All</option>{certOpts.map((c) => <option key={c} value={c}>{c === "none" ? "No certification" : c}</option>)}</select></label>
                    <label>Day<select value={fDay} onChange={(e) => setFDay(e.target.value)}><option value="all">All days</option>{dayOpts.map((d) => <option key={d} value={d}>{dayLabel(d)}</option>)}</select></label>
                    <label className="chk"><input type="checkbox" checked={fOk} onChange={(e) => setFOk(e.target.checked)} />Claimable only</label>
                  </div>
                  <Tbl head={["Shift", "When", "Certification", "Posted by", "Can you claim it?", ""]} count={shown.length} empty={open.length ? "No listings match your filters." : "No colleague has a shift up for swap right now."}>
                    {shown.map((l) => (
                      <tr key={l.id} className={l.can_claim ? "" : "bad"}>
                        <td className="id">{l.shift.id}</td><td><When s={l.shift} /></td><td><Cert c={l.shift.required_certification} /></td><td>{l.poster_name}</td>
                        <td className="wrap">{l.can_claim ? <Badge kind="ok">Yes</Badge> : <><Badge kind="err">No</Badge><Reasons list={l.reasons} /></>}<p className="hrs">Week of {dayLabel(l.week_start)}: {fh(l.hours_now)}h → {fh(l.hours_after)}h of 40h</p></td>
                        <td className="r"><button disabled={!l.can_claim} onClick={() => act(() => api.claim(actor.id, l.id), `Claimed ${l.shift.id}. Waiting for manager approval.`)}>Claim</button></td>
                      </tr>
                    ))}
                  </Tbl>
                </Card>
              </div>

              <Card id="claims" title="My pending claims" count={me.claims.length} unit={me.claims.length === 1 ? "claim" : "claims"} tone="orange">
                <p className="note">Claiming does not reassign a shift. It changes hands only after a manager approves.</p>
                <Tbl head={["Shift", "When", "Certification", "Original owner", "Status", ""]} count={me.claims.length} empty="You have no pending claims.">
                  {me.claims.map((l) => (
                    <tr key={l.id}>
                      <td className="id">{l.shift.id}</td><td><When s={l.shift} /></td><td><Cert c={l.shift.required_certification} /></td><td>{l.poster_name}</td>
                      <td><Badge kind="warn">Awaiting approval</Badge></td>
                      <td className="r"><button className="ghost" onClick={() => act(() => api.unclaim(actor.id, l.id), `Unclaimed ${l.shift.id}`)}>Unclaim</button></td>
                    </tr>
                  ))}
                </Tbl>
              </Card>
            </>
          )}

          {isMgr && (
            <Card id="queue" title="Claims awaiting approval" count={queue.length} unit={queue.length === 1 ? "claim" : "claims"} tone="red">
              <Tbl head={["Shift", "When", "Certification", "From", "Claimed by", "Status check", "Actions"]} count={queue.length} empty="No claims are waiting for approval.">
                {queue.map((l) => (
                  <tr key={l.id} className={l.can_approve ? "" : "bad"}>
                    <td className="id">{l.shift.id}</td><td><When s={l.shift} /></td><td><Cert c={l.shift.required_certification} /></td><td>{l.poster_name}</td><td>{l.claimed_by_name}</td>
                    <td className="wrap">{l.can_approve ? <Badge kind="ok">Rules pass</Badge> : <><Badge kind="err">Would be refused</Badge><Reasons list={l.reasons} /></>}</td>
                    <td className="r acts">
                      <button disabled={!l.can_approve} title={l.can_approve ? "" : "A rule currently fails for this claim"} onClick={() => act(() => api.approve(actor.id, l.id), `Approved ${l.shift.id}`)}>Approve</button>
                      <button className="ghost" onClick={() => act(() => api.reject(actor.id, l.id), `Rejected claim on ${l.shift.id}`)}>Reject</button>
                    </td>
                  </tr>
                ))}
              </Tbl>
            </Card>
          )}

          {isMgr && <People staff={staff} onAdd={addPerson} />}

          <History items={history} />
        </main>
      </div>
    </>
  );
}