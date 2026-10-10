# ShiftSwap - CityCare Clinic

Web app for posting, claiming and approving shift swaps, with every labour rule validated server-side and every refusal explained.

- **Backend:** FastAPI (Python 3.10+), JSON-file persistence (`backend/data/state.json`)
- **Frontend:** React 18 + Vite

## Run locally

### 1. Backend (port 8000)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Put the provided seed.json in backend/ (replace the sample one)
uvicorn main:app --port 8000
```
Run rule tests: `cd backend && python -m pytest -q tests`

### 2. Frontend (port 5173)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (Vite proxies `/api` to `localhost:8000`).
If the API lives elsewhere: `VITE_API_URL=https://your-api npm run dev` (or at build time).

### Reset state
Stop the backend and delete `backend/data/state.json`; the seed is reloaded on next start.
Env overrides: `SHIFTSWAP_DATA` (state file path), `SHIFTSWAP_SEED` (seed path).

## How it works
- `backend/rules.py` - pure claim-rule logic (rules 1-5). Never reads the real clock.
- `backend/main.py` - endpoints and state transitions; all mutations run under a lock.
- `backend/store.py` - loads seed only if no saved state; atomic write (temp file + rename) after every action.

### API (all writes take `{"actor_id": "..."}`)
| Method | Path | Notes |
|---|---|---|
| GET | `/api/staff` | people |
| GET | `/api/me/{id}` | own shifts + listing status, own pending claims |
| GET | `/api/listings/open?viewer_id=` | others' OPEN listings with `can_claim` and all `reasons` |
| GET | `/api/listings/claimed?viewer_id=` | manager queue, with a live re-check (`can_approve`, `reasons`) |
| GET | `/api/history` | newest first |
| POST | `/api/listings` | `{actor_id, shift_id}` post |
| POST | `/api/listings/{id}/withdraw \| claim \| unclaim \| approve \| reject` | |

Refusals return HTTP 403/404/409 with `detail: {code, message, violations:[{rule, message, conflicting_shift}]}`.
`NO_LONGER_AVAILABLE` is returned (nothing else checked) when claiming a non-OPEN listing.

## Assumptions
1. Rule order for a claim: unknown person/listing (404) -> managers cannot claim (403) -> listing not OPEN ("no longer available", nothing else checked) -> rules 1-5.
2. If the claimer is the poster, only rule 1 is reported.
3. A shift's full duration counts toward the week in which it starts (a Sunday-night shift crossing into Monday counts for the earlier week).
4. Rule 4 checks every non-overlapping shift assigned to the claimer, including ones in adjacent weeks. Exactly 11h rest and exactly 40h are allowed.
5. Rule 3 and rule 4 violations are reported once per conflicting shift.
6. Approval re-checks rules 2-5 only (rule 1 cannot change). On failure the approval is refused and the listing stays CLAIMED.
7. Reject returns the listing to OPEN and clears the claimer. Unclaim does the same.
8. Withdraw is only allowed while OPEN (not while CLAIMED), per the spec table.
9. A person may hold several pending claims; they are only validated against actual assignments, so approvals are checked one at a time and a later approval can be refused after an earlier one.
10. Refused attempts (permission or rule failures) are also written to the history with outcome `REFUSED` and the reasons. Timestamps in the history are wall-clock for display only and are not used by any rule.
11. No login: the "acting as" dropdown sends `actor_id`; the backend enforces roles and ownership regardless of the UI.
12. Single backend process assumed (in-process lock + JSON file).
