# FizX monorepo

A self-hosted video conferencing platform (Zoom alternative).

- `frontend/` — Next.js 15 + TypeScript + Tailwind + shadcn/ui app. See `frontend/AGENTS.md` for Next.js-version-specific notes.
- `backend/` — Django 5 + DRF + Channels API. Apps live under `backend/apps/*`.
- `infra/` — coturn, LiveKit, and nginx configuration used by the root `docker-compose.yml`.
- `FizX-Meet-App/` — React Native (Expo) Android client, a mobile clone of `frontend/`'s screens against the same backend. See `FizX-Meet-App/README.md` for how to run/test it (Expo Go for everything except calls; calls need an EAS dev-client build since LiveKit's React Native SDK needs native WebRTC modules Expo Go doesn't ship).

For **local development**, start the stack with `./scripts/start.sh` from the
repo root instead of a bare `docker compose up` — it detects this machine's
current LAN IP and updates `.env` plus the nginx TLS cert to match before
bringing everything up, so it keeps working no matter which network/WiFi
you're on. Pass through compose flags as needed, e.g. `./scripts/start.sh --build`.
For the production EC2 deploy (fixed public IP, no auto-detection needed),
see `DEPLOY.md`.
