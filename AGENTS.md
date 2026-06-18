# FizX monorepo

A self-hosted video conferencing platform (Zoom alternative).

- `frontend/` — Next.js 15 + TypeScript + Tailwind + shadcn/ui app. See `frontend/AGENTS.md` for Next.js-version-specific notes.
- `backend/` — Django 5 + DRF + Channels API. Apps live under `backend/apps/*`.
- `infra/` — coturn, LiveKit, and nginx configuration used by the root `docker-compose.yml`.

Run the whole stack with `docker compose up` from the repo root.
