const BASE = import.meta.env.VITE_API_URL || "";

async function req(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data && data.detail;
    if (d && typeof d === "object" && !Array.isArray(d)) throw d;
    throw { message: Array.isArray(d) ? "Invalid request" : d || "Request failed", violations: [] };
  }
  return data;
}

const post = (path, body) => req(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  staff: () => req("/api/staff"),
  addPerson: (actor_id, name, role, certifications) => post("/api/staff", { actor_id, name, role, certifications }),
  me: (id) => req(`/api/me/${id}`),
  open: (id) => req(`/api/listings/open?viewer_id=${id}`),
  claimed: (id) => req(`/api/listings/claimed?viewer_id=${id}`),
  history: () => req("/api/history"),
  clearHistory: (actor_id) => post("/api/history/clear", { actor_id }),
  post: (actor_id, shift_id) => post("/api/listings", { actor_id, shift_id }),
  withdraw: (actor_id, lid) => post(`/api/listings/${lid}/withdraw`, { actor_id }),
  claim: (actor_id, lid) => post(`/api/listings/${lid}/claim`, { actor_id }),
  unclaim: (actor_id, lid) => post(`/api/listings/${lid}/unclaim`, { actor_id }),
  approve: (actor_id, lid) => post(`/api/listings/${lid}/approve`, { actor_id }),
  reject: (actor_id, lid) => post(`/api/listings/${lid}/reject`, { actor_id }),
};