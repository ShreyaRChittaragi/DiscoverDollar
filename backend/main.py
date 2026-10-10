from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rules import check_claim, duration, week_start
from store import LOCK, Store

app = FastAPI(title="ShiftSwap")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
store = Store()
S = store.state


class ActorBody(BaseModel):
    actor_id: str


class PostBody(BaseModel):
    actor_id: str
    shift_id: str


# ---------- helpers ----------
def _find(items, id_, what):
    for i in items:
        if i["id"] == id_:
            return i
    raise HTTPException(404, detail={"code": "NOT_FOUND", "message": f"{what} '{id_}' not found", "violations": []})


def get_actor(aid):
    return _find(S["staff"], aid, "Person")


def get_shift(sid):
    return _find(S["shifts"], sid, "Shift")


def get_listing(lid):
    return _find(S["listings"], lid, "Listing")


def name_of(pid) -> Optional[str]:
    return next((p["name"] for p in S["staff"] if p["id"] == pid), None) if pid else None


def shifts_of(pid):
    return [s for s in S["shifts"] if s["assigned_to"] == pid]


def week_hours(pid):
    """Hours per week (key = Monday date) for shifts currently assigned to pid."""
    out = {}
    for s in shifts_of(pid):
        k = week_start(s).date().isoformat()
        out[k] = out.get(k, 0) + duration(s).total_seconds() / 3600
    return out


def new_person_id(role):
    p = "S" if role == "STAFF" else "M"
    nums = [int(x["id"][1:]) for x in S["staff"] if x["id"].startswith(p) and x["id"][1:].isdigit()]
    return f"{p}{max(nums, default=0) + 1}"


def active_listing(shift_id):
    return next((l for l in S["listings"] if l["shift_id"] == shift_id and l["status"] in ("OPEN", "CLAIMED")), None)


def log(actor, action, shift_id, listing_id, outcome, detail=""):
    S["history"].append({
        "id": store.next_id("history", "h"),
        "at": datetime.now().isoformat(timespec="seconds"),  # display only; never used by rules
        "actor_id": actor["id"], "actor_name": actor["name"],
        "action": action, "shift_id": shift_id, "listing_id": listing_id,
        "outcome": outcome, "detail": detail,
    })


def refuse(actor, action, shift_id, listing_id, message, status=409, code="REFUSED", violations=None):
    detail = message
    if violations:
        detail += " | " + " ; ".join(v["message"] for v in violations)
    log(actor, action, shift_id, listing_id, "REFUSED", detail)
    store.save()
    raise HTTPException(status, detail={"code": code, "message": message, "violations": violations or []})


def succeed(actor, action, shift_id, listing_id, detail=""):
    log(actor, action, shift_id, listing_id, "SUCCESS", detail)
    store.save()


def listing_view(l):
    s = get_shift(l["shift_id"])
    return {**l, "shift": s, "poster_name": name_of(l["poster_id"]), "claimed_by_name": name_of(l["claimed_by"])}


def unavailable(actor, action, l):
    refuse(actor, action, l["shift_id"], l["id"], "This listing is no longer available",
           409, "NO_LONGER_AVAILABLE")


# ---------- reads ----------
@app.get("/api/staff")
def staff():
    return S["staff"]


@app.get("/api/shifts")
def all_shifts():
    return sorted(S["shifts"], key=lambda s: s["start"])


@app.get("/api/me/{staff_id}")
def me(staff_id: str):
    with LOCK:
        actor = get_actor(staff_id)
        if actor["role"] != "STAFF":
            return {"shifts": [], "claims": [], "weeks": []}
        mine = []
        for s in sorted(shifts_of(staff_id), key=lambda s: s["start"]):
            l = active_listing(s["id"])
            mine.append({**s, "listing": None if not l else {
                "id": l["id"], "status": l["status"], "claimed_by": l["claimed_by"],
                "claimed_by_name": name_of(l["claimed_by"])}})
        claims = [listing_view(l) for l in S["listings"] if l["status"] == "CLAIMED" and l["claimed_by"] == staff_id]
        weeks = [{"week_start": k, "hours": h} for k, h in sorted(week_hours(staff_id).items())]
        return {"shifts": mine, "claims": claims, "weeks": weeks}


@app.get("/api/listings/open")
def open_listings(viewer_id: str):
    with LOCK:
        viewer = get_actor(viewer_id)
        if viewer["role"] != "STAFF":
            raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Only staff can browse claimable listings", "violations": []})
        out = []
        for l in S["listings"]:
            if l["status"] != "OPEN" or l["poster_id"] == viewer_id:
                continue
            s = get_shift(l["shift_id"])
            vs = check_claim(viewer, s, l["poster_id"], shifts_of(viewer_id))
            wk = week_start(s).date().isoformat()
            now = week_hours(viewer_id).get(wk, 0)
            out.append({**listing_view(l), "can_claim": not vs, "reasons": vs, "week_start": wk,
                        "hours_now": now, "hours_after": now + duration(s).total_seconds() / 3600})
        return sorted(out, key=lambda x: x["shift"]["start"])


@app.get("/api/listings/claimed")
def claimed_listings(viewer_id: str):
    with LOCK:
        viewer = get_actor(viewer_id)
        if viewer["role"] != "MANAGER":
            raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "Only managers can see the approval queue", "violations": []})
        out = []
        for l in S["listings"]:
            if l["status"] != "CLAIMED":
                continue
            s = get_shift(l["shift_id"])
            c = _find(S["staff"], l["claimed_by"], "Person")
            vs = check_claim(c, s, l["poster_id"], shifts_of(c["id"]), rules=(2, 3, 4, 5))
            out.append({**listing_view(l), "can_approve": not vs, "reasons": vs})
        return sorted(out, key=lambda x: x["shift"]["start"])


@app.get("/api/history")
def history():
    return list(reversed(S["history"]))


# ---------- writes ----------
@app.post("/api/listings", status_code=201)
def post_listing(body: PostBody):
    with LOCK:
        actor = get_actor(body.actor_id)
        shift = get_shift(body.shift_id)
        A = "POST"
        if actor["role"] != "STAFF":
            refuse(actor, A, shift["id"], None, "Managers cannot post shifts", 403, "FORBIDDEN")
        if shift["assigned_to"] != actor["id"]:
            refuse(actor, A, shift["id"], None, "You can only post shifts assigned to you", 403, "FORBIDDEN")
        if active_listing(shift["id"]):
            refuse(actor, A, shift["id"], None, "This shift already has an OPEN or CLAIMED listing")
        l = {"id": store.next_id("listing", "l"), "shift_id": shift["id"], "poster_id": actor["id"],
             "status": "OPEN", "claimed_by": None}
        S["listings"].append(l)
        succeed(actor, A, shift["id"], l["id"], "Listing OPEN")
        return listing_view(l)


@app.post("/api/listings/{lid}/withdraw")
def withdraw(lid: str, body: ActorBody):
    with LOCK:
        actor, l, A = get_actor(body.actor_id), get_listing(lid), "WITHDRAW"
        if l["poster_id"] != actor["id"]:
            refuse(actor, A, l["shift_id"], lid, "Only the poster can withdraw this listing", 403, "FORBIDDEN")
        if l["status"] != "OPEN":
            refuse(actor, A, l["shift_id"], lid, f"Only OPEN listings can be withdrawn (this one is {l['status']})")
        l["status"] = "WITHDRAWN"
        succeed(actor, A, l["shift_id"], lid, "Listing WITHDRAWN")
        return listing_view(l)


@app.post("/api/listings/{lid}/claim")
def claim(lid: str, body: ActorBody):
    with LOCK:
        actor, l, A = get_actor(body.actor_id), get_listing(lid), "CLAIM"
        if actor["role"] != "STAFF":
            refuse(actor, A, l["shift_id"], lid, "Managers cannot claim shifts", 403, "FORBIDDEN")
        if l["status"] != "OPEN":
            unavailable(actor, A, l)
        shift = get_shift(l["shift_id"])
        vs = check_claim(actor, shift, l["poster_id"], shifts_of(actor["id"]))
        if vs:
            refuse(actor, A, shift["id"], lid, "Claim refused", 409, "RULE_VIOLATION", vs)
        l["status"], l["claimed_by"] = "CLAIMED", actor["id"]
        succeed(actor, A, shift["id"], lid, "Listing CLAIMED")
        return listing_view(l)


@app.post("/api/listings/{lid}/unclaim")
def unclaim(lid: str, body: ActorBody):
    with LOCK:
        actor, l, A = get_actor(body.actor_id), get_listing(lid), "UNCLAIM"
        if l["claimed_by"] != actor["id"] or l["status"] not in ("CLAIMED",):
            if l["status"] == "CLAIMED":
                refuse(actor, A, l["shift_id"], lid, "Only the claimer can unclaim this listing", 403, "FORBIDDEN")
            refuse(actor, A, l["shift_id"], lid, f"Only CLAIMED listings can be unclaimed (this one is {l['status']})")
        l["status"], l["claimed_by"] = "OPEN", None
        succeed(actor, A, l["shift_id"], lid, "Listing back to OPEN")
        return listing_view(l)


@app.post("/api/listings/{lid}/approve")
def approve(lid: str, body: ActorBody):
    with LOCK:
        actor, l, A = get_actor(body.actor_id), get_listing(lid), "APPROVE"
        if actor["role"] != "MANAGER":
            refuse(actor, A, l["shift_id"], lid, "Only managers can approve", 403, "FORBIDDEN")
        if l["status"] != "CLAIMED":
            refuse(actor, A, l["shift_id"], lid, f"Only CLAIMED listings can be approved (this one is {l['status']})")
        shift, claimer = get_shift(l["shift_id"]), _find(S["staff"], l["claimed_by"], "Person")
        vs = check_claim(claimer, shift, l["poster_id"], shifts_of(claimer["id"]), rules=(2, 3, 4, 5))
        if vs:
            refuse(actor, A, shift["id"], lid, "Approval refused; listing stays CLAIMED", 409, "RULE_VIOLATION", vs)
        shift["assigned_to"] = claimer["id"]
        l["status"] = "APPROVED"
        succeed(actor, A, shift["id"], lid, f"Shift reassigned {name_of(l['poster_id'])} -> {claimer['name']}")
        return listing_view(l)


@app.post("/api/listings/{lid}/reject")
def reject(lid: str, body: ActorBody):
    with LOCK:
        actor, l, A = get_actor(body.actor_id), get_listing(lid), "REJECT"
        if actor["role"] != "MANAGER":
            refuse(actor, A, l["shift_id"], lid, "Only managers can reject", 403, "FORBIDDEN")
        if l["status"] != "CLAIMED":
            refuse(actor, A, l["shift_id"], lid, f"Only CLAIMED listings can be rejected (this one is {l['status']})")
        who = name_of(l["claimed_by"])
        l["status"], l["claimed_by"] = "OPEN", None
        succeed(actor, A, l["shift_id"], lid, f"Claim by {who} rejected; listing back to OPEN")
        return listing_view(l)


class PersonBody(BaseModel):
    actor_id: str
    name: str
    role: str
    certifications: list[str] = []


@app.post("/api/staff", status_code=201)
def add_person(body: PersonBody):
    with LOCK:
        actor, A = get_actor(body.actor_id), "ADD_PERSON"
        name = " ".join(body.name.split())
        role = body.role.upper()
        certs = []
        for c in body.certifications:
            c = c.strip().upper()
            if c and c not in certs:
                certs.append(c)
        if actor["role"] != "MANAGER":
            refuse(actor, A, None, None, "Only managers can add people", 403, "FORBIDDEN")
        if not name or len(name) > 60:
            refuse(actor, A, None, None, "Name is required (60 characters at most)", 422, "INVALID")
        if role not in ("STAFF", "MANAGER"):
            refuse(actor, A, None, None, "Role must be STAFF or MANAGER", 422, "INVALID")
        if any(p["name"].lower() == name.lower() for p in S["staff"]):
            refuse(actor, A, None, None, f"A person named '{name}' already exists", 409, "DUPLICATE")
        p = {"id": new_person_id(role), "name": name, "role": role, "certifications": certs if role == "STAFF" else []}
        S["staff"].append(p)
        succeed(actor, A, None, None, f"Added {name} as {role}")
        return p