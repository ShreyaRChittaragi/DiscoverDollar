# AI Usage Disclosure

This document describes how AI tools assisted with the ShiftSwap hackathon project. It distinguishes AI-generated starting points from the decisions, edits, and verification performed during development.

## Where AI was used

- **Claude:** Used to generate an initial implementation/draft of the FastAPI backend, scheduling-rule logic, persistence layer, React frontend, seed data, tests, and documentation.
- **ChatGPT:** Used to clarify and organize the requirements, review business-rule behavior and API/UI alignment, identify edge cases, suggest frontend polish, help prepare the README, and explain deployment configuration and debugging steps.

The tools were used as development assistance. The project was reviewed and tested during implementation, but AI review is not a substitute for comprehensive independent testing.

## What was accepted

- A separate backend rule-validation layer so scheduling rules can be checked independently of UI rendering.
- A React/Vite frontend communicating with a FastAPI backend through API endpoints.
- A distinct claim and manager-approval workflow: claiming a shift does not immediately reassign it.
- Revalidation of relevant scheduling rules at approval time.
- Structured refusal responses with reasons, and an action history that records successful and refused actions.
- The additional user-facing features documented in `README.md`: weekly-hours projections, manager-only staff creation, filters, CSV export, the time-of-day strip, responsive layouts, and the acting-as demo selector.
- SQLite-based persistence and a one-time migration path from older JSON state, as implemented in the final project version.

## What was changed or refined

- The requirements and assumptions were made explicit, including certification checks, shift overlap, the minimum 11-hour rest period, the 40-hour weekly cap, and approval-time revalidation.
- The UI was refined toward a responsive teal-and-white dashboard with clearer statuses, filters, summary information, and manager actions.
- The API/frontend contract was reviewed for endpoint paths, request methods, actor IDs, and projected weekly-hours data.
- The persistence approach evolved from an earlier JSON-file implementation to SQLite in the described final version. The README should match the code that is actually submitted.
- Documentation and local/deployment run instructions were revised to make setup and limitations clearer.

## What was not adopted or remains a limitation

- The acting-as selector was not treated as real authentication. It is only a convenience for a no-login demo.
- The frontend was not treated as the authority for business-rule enforcement; the backend must validate each write request.
- A claim was not treated as an immediate reassignment. Manager approval and approval-time revalidation remain separate steps.
- The app was not presented as production-ready. Real deployment would require real authentication, durable hosted storage, stronger authorization, and concurrency testing.
- Suggestions that would add unnecessary complexity during the time-limited hackathon were weighed against the requirement to finish a working prototype.

## Verification performed

The following checks were reported during development:

- `npm ci` completed successfully.
- `npm run build` completed successfully with Vite.
- `python -m pytest -q tests` completed with **5 tests passing**.
- The backend API paths and frontend calls were reviewed for alignment.
- The Vite configuration was confirmed to proxy `/api` to `http://localhost:8000` during local development.
- The frontend entry point was confirmed to import `styles.css`.
- The deployed backend initially failed because the Render start command referenced `app.main:app`; the correct command for a Render service whose root directory is `backend` is `uvicorn main:app --host 0.0.0.0 --port $PORT`. A later Render log showed the service reporting its primary URL, but the frontend's complete live workflow should still be tested before the demo.

## Important accuracy note

The verification list above reflects checks reported during development. It does not claim that every possible edge case, concurrent request, browser interaction, or production deployment scenario has been tested. Before submission, make sure this file accurately describes the final repository and remove or correct any statement that no longer matches the submitted code.
