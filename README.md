# ShiftSwap — CityCare Clinic

ShiftSwap is a staff shift-swapping web application for a clinic. Staff can post shifts they are willing to give up, claim shifts posted by other staff, and track the approval process. Managers review claimed shifts and approve or reject them.

The central design principle is that **a claim is not an assignment**. A shift remains assigned to its original staff member until a manager approves the claim and the backend revalidates the scheduling rules.

## Features

### Core workflow
- Staff can post their own assigned shifts, withdraw open listings, claim other staff members' open listings, and unclaim their own pending claims.
- Managers can review the approval queue, approve valid claims, and reject claims.
- A claim is checked against the scheduling rules, and the backend reports all applicable violations.
- Approval rechecks the relevant rules against current assignments. If the claim is no longer valid, approval is refused and the original assignment remains unchanged.
- Successful and refused actions are recorded in the action history.

### Scheduling rules
- A staff member cannot claim their own listing.
- The claimant must have the required certification.
- The proposed shift cannot overlap an existing assigned shift.
- There must be at least **11 hours of rest** between non-overlapping shifts.
- The claimant's assigned hours in the week when the proposed shift starts cannot exceed **40 hours**.
- A shift belongs to the Monday-to-Monday week in which it starts. Its full duration counts in that week, even if it crosses midnight.
- Exactly 11 hours of rest and exactly 40 weekly hours are allowed.
- If a listing is no longer open, the system returns a “no longer available” result rather than evaluating other claim rules.

### Additional features
- **Weekly-hours meter:** Shows assigned hours out of 40 and the projected hours after claiming an open shift.
- **Manager-only Add Person:** Adds a staff member or manager, supports certifications, rejects duplicate names, and logs the action.
- **Available-shift filters:** Filter by certification, day, and claimable-only status.
- **History CSV export:** Exports the history currently shown in the interface.
- **Time-of-day strip:** Visually marks morning, evening, and night shifts, including overnight shifts.
- **Acting-as picker:** Makes it easy to switch demo identities without login.
- **Refused-only history filter:** Makes refused actions easier to inspect.
- **Responsive UI:** Tables become card-style layouts on smaller screens.
- **Local fonts:** Figtree and Bricolage Grotesque are bundled locally for offline use.

## Tech stack

- **Frontend:** React 18, Vite, JavaScript, CSS
- **Backend:** Python, FastAPI, Pydantic
- **Persistence:** SQLite, with transactional updates for application actions
- **Testing:** pytest and HTTPX (where used by the test suite)

React makes the interactive UI easier to organize into reusable components. Vite provides a fast development server and production build. FastAPI offers a clear API structure, typed request validation, and automatically generated API documentation. SQLite avoids a separate database server and supports transactions. The stack was chosen to keep the implementation practical within a three-hour hackathon while concentrating effort on the scheduling rules.

## Run locally

Requirements:
- Python 3.10 or newer
- Node.js and npm

### 1. Start the backend

From the repository root:

**Windows PowerShell**
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

**macOS/Linux**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

FastAPI's interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

Open a second terminal from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`. During local development, Vite proxies `/api` requests to `http://localhost:8000`.

For a separately hosted API, set `VITE_API_URL` to the backend's base URL before building the frontend. Vite environment variables are embedded at build time, so rebuild/redeploy the frontend after changing the value.

### 3. Run tests

From the repository root:

```bash
cd backend
python -m pytest -q tests
```

## Main API endpoints

All write requests identify the demo actor with `actor_id`. This is for the no-login hackathon demo and is not secure authentication.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/staff` | List people |
| `GET` | `/api/shifts` | List shifts |
| `GET` | `/api/me/{id}` | Get a staff member's assigned shifts, pending claims, and weekly hours |
| `GET` | `/api/listings/open?viewer_id={id}` | List open listings with eligibility reasons and projected weekly hours |
| `GET` | `/api/listings/claimed?viewer_id={id}` | Manager approval queue with live approval validation |
| `GET` | `/api/history` | View recent action history |
| `POST` | `/api/listings` | Post an assigned shift |
| `POST` | `/api/listings/{id}/withdraw` | Withdraw an open listing |
| `POST` | `/api/listings/{id}/claim` | Claim an open listing |
| `POST` | `/api/listings/{id}/unclaim` | Release the current user's pending claim |
| `POST` | `/api/listings/{id}/approve` | Approve a valid claim |
| `POST` | `/api/listings/{id}/reject` | Reject a pending claim |
| `POST` | `/api/staff` | Add a person (manager only) |

Rule refusals use structured error details that include a code, message, and applicable violations. The API's `/docs` page can be used to inspect request and response schemas.

## Persistence and seed data

The application uses SQLite for persisted state. Existing saved state should be retained across backend restarts, and seed data should only be imported when the database has no saved state. The project also includes a one-time migration path for importing an older `state.json` into an empty database.

For a hosted deployment, ensure the SQLite database is stored on persistent storage. A database file on an ephemeral hosting filesystem may be lost when the service is replaced or redeployed. Do not commit local runtime databases or private state to Git.

> Confirm the database path and any environment-variable overrides in the current `backend/store.py` before deploying. Keep the seed file in the repository, but keep runtime state out of version control.

## Assumptions and design decisions

1. The “acting as” selector is a demo identity switcher. It does not authenticate a real user.
2. The backend is authoritative for eligibility checks; the frontend's claimability indicators are informational and do not replace server validation.
3. A claim remains pending until a manager approves it.
4. Approval rechecks the relevant scheduling rules against current assignments.
5. The application records refused attempts as well as successful actions to make outcomes explainable.
6. The app is a hackathon prototype, not a production clinical staffing system. Production use would require authenticated identities, stronger authorization, durable database hosting, concurrency testing, and deployment hardening.

## Deployment

The backend can be deployed as a Render Web Service with:
- **Root directory:** `backend`
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

The frontend can be deployed as a Render Static Site with:
- **Root directory:** `frontend`
- **Build command:** `npm ci && npm run build`
- **Publish directory:** `dist`
- **Environment variable:** `VITE_API_URL` set to the deployed backend URL

Configure CORS to allow the deployed frontend origin where appropriate. Verify that the deployed database is on persistent storage before relying on saved state during a demonstration.

## Repository layout

```text
.
├── backend/
│   ├── main.py
│   ├── rules.py
│   ├── store.py
│   ├── requirements.txt
│   ├── seed.json
│   └── tests/
└── frontend/
    ├── src/
    │   ├── api.js
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── styles.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```
