# Deploying FizX to the server

Target: AWS EC2 instance at `51.20.85.58`, user `ubuntu`, repo checked out at
`~/FizX`. Docker needs `sudo` on this box. The instance is small (~900MB RAM)
and swaps heavily under a `next build` while the rest of the stack is also
running — a frontend rebuild can take 15-30+ minutes. That's normal, not
stuck; just let it run.

This server has a fixed public IP, so none of this needs the LAN-IP
auto-detection `./scripts/start.sh` does for local dev (see `AGENTS.md`) —
use the plain `docker compose` commands below directly.

## Connecting

```bash
ssh -i /path/to/your-key.pem ubuntu@51.20.85.58
cd ~/FizX
```

## Domain: fizx.work.gd

This domain now points at the box (DNS A record → `51.20.85.58`), with a
real Let's Encrypt certificate replacing the old self-signed one. To bring
the server's own checkout in sync with that:

1. **Copy the cert onto the box** - `infra/nginx/certs/` is gitignored (on
   every checkout, including this one), so it never travels via `git pull`.
   From your machine:
   ```bash
   scp infra/nginx/certs/cert.pem infra/nginx/certs/key.pem \
     ubuntu@51.20.85.58:~/FizX/infra/nginx/certs/
   ```
2. **Pull the nginx.conf change** (`server_name` now lists `fizx.work.gd`
   explicitly alongside the `_` catch-all - this doesn't change routing by
   itself since there's still only one server block per port, it just
   documents the real target):
   ```bash
   git pull
   sudo docker compose restart nginx
   ```
3. **Update `~/FizX/.env` on the box** - add the domain to the existing
   comma-separated lists rather than replacing the IP (keeps IP-based
   access working as a fallback):
   ```bash
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,51.20.85.58,fizx.work.gd
   DJANGO_CSRF_TRUSTED_ORIGINS=https://51.20.85.58,https://fizx.work.gd
   CORS_ALLOWED_ORIGINS=https://51.20.85.58,https://fizx.work.gd
   ```
   Leave `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_WS_URL`/`NEXT_PUBLIC_LIVEKIT_URL`
   unset - the frontend already derives these from whatever origin the
   browser used to load the page (see the comment above them in
   `.env.example`), so the same build serves the IP and the domain without
   a rebuild. `LIVEKIT_NODE_IP`/`TURN_PUBLIC_IP` also stay as the raw IP -
   ICE candidates are IP:port pairs, not hostnames, regardless of domain.
4. **Turn on HSTS now that the cert is CA-trusted** (it was off specifically
   *because* the old cert was self-signed - see the comment next to
   `DJANGO_SECURE_HSTS_SECONDS` in `backend/config/settings/production.py`):
   ```bash
   DJANGO_SECURE_HSTS_SECONDS=31536000
   ```
5. Apply the `.env` changes:
   ```bash
   sudo docker compose up -d --force-recreate backend celery_worker celery_beat frontend
   sudo docker compose restart nginx
   ```
6. Verify:
   ```bash
   curl -sI https://fizx.work.gd/login | head -5   # 200, no cert warning
   ```

**Renewal**: this cert expires **2026-09-22** (Let's Encrypt, 90-day
validity). It was issued manually and pasted in rather than provisioned via
an ACME client running on the box, so there's no automatic renewal set up -
whoever holds the domain/DNS needs to reissue and re-`scp` it (steps 1-2
above) before then, or set up `certbot` on the box against this same
`infra/nginx/certs/` path.

## Day-to-day: ship a code change

This is the 95% case — you changed something in `backend/` or `frontend/`
and want it live.

```bash
cd ~/FizX
git pull

# rebuild whichever side(s) changed
sudo docker compose build backend
sudo docker compose build frontend

# recreate the containers from the new image
sudo docker compose up -d --force-recreate backend celery_worker celery_beat
sudo docker compose up -d --force-recreate frontend

# REQUIRED after recreating backend or frontend - nginx resolves their
# container IP once at its own startup and caches it. Skip this and you'll
# get stale 502s even though the new container is healthy.
sudo docker compose restart nginx
```

Database migrations run automatically — the backend's entrypoint
(`backend/docker/entrypoint.sh`) runs `migrate` and `collectstatic` every
time the `daphne`/`gunicorn` container starts, before the app boots.

Verify:

```bash
sudo docker compose ps                     # everything should say "Up"
curl -sk https://51.20.85.58/login -o /dev/null -w '%{http_code}\n'   # 200
sudo docker compose logs backend --tail 50
```

## Starting everything from a stopped state

```bash
cd ~/FizX
sudo docker compose up -d
sudo systemctl start whatsapp-otp     # see below, separate from compose
```

## whatsapp-otp service

This one is **not** in docker-compose — it runs directly on the host as a
systemd service so it can keep its WhatsApp session (`whatsapp-otp/auth/`)
across deploys without living inside an image.

```bash
# status / logs
sudo systemctl status whatsapp-otp
sudo journalctl -u whatsapp-otp -f

# restart (e.g. after pulling new whatsapp-otp/ code)
cd ~/FizX/whatsapp-otp
npm install            # only if package.json changed
npm run build
sudo systemctl restart whatsapp-otp

# re-link WhatsApp (e.g. session got logged out)
# 1. make sure port 3210 is reachable (EC2 Security Group, TCP 3210)
# 2. open http://51.20.85.58:3210 in a browser and scan the QR
#    - scan it FAST: until a device links, anyone who can load that page
#      can also scan it and hijack the session
curl http://localhost:3210/api/status     # {"status":"open"} once linked
```

Its `.env` (`whatsapp-otp/.env`, not in git) holds `API_KEY` — this must
match `WHATSAPP_OTP_API_KEY` in the root `.env` that the backend reads, or
the backend's OTP requests will get 401s from it.

## One-time / rare operations

**Reset the database** (only if you genuinely want to wipe all users/data —
this is what we did once already when the auth model changed in a way old
rows couldn't migrate forward):

```bash
sudo docker compose stop backend celery_worker celery_beat frontend
sudo docker compose exec postgres psql -U fizx -d postgres -c "DROP DATABASE fizx;"
sudo docker compose exec postgres psql -U fizx -d postgres -c "CREATE DATABASE fizx;"
sudo docker compose up -d backend celery_worker celery_beat frontend
sudo docker compose restart nginx
```

**Regenerate the TLS cert**: now that `fizx.work.gd` has a real Let's
Encrypt cert (see "Domain: fizx.work.gd" above for renewal), that's the one
that should be in `infra/nginx/certs/`. The self-signed fallback below is
only for if the domain/cert lapses and the box needs to stay reachable by
IP in the meantime — remember it disables HSTS again if used (see the
comment next to `DJANGO_SECURE_HSTS_SECONDS` in
`backend/config/settings/production.py`):

```bash
./infra/nginx/generate-cert.sh 51.20.85.58
sudo docker compose restart nginx
```

**Full rebuild of everything:**

```bash
sudo docker compose build
sudo docker compose up -d --force-recreate
sudo docker compose restart nginx
```

## Where things live

| What | Where |
|---|---|
| App code, compose file, `.env` | `~/FizX` |
| whatsapp-otp source | `~/FizX/whatsapp-otp` |
| whatsapp-otp session (don't delete) | `~/FizX/whatsapp-otp/auth/` |
| whatsapp-otp systemd unit | `/etc/systemd/system/whatsapp-otp.service` |
| nginx config | `~/FizX/infra/nginx` |

## Gotchas worth remembering

- **Stale nginx upstream**: any time `backend` or `frontend` gets
  recreated, `restart nginx` right after. This is the single most common
  cause of a 502 right after a deploy that otherwise looked successful.
- **No bind mounts**: code is baked into the image at build time. Editing
  a file on the server directly does nothing until you `build` + recreate.
- **Slow builds, not stuck builds**: the box swaps hard under `next build`
  while everything else keeps running. Check `free -h` / `uptime` if
  you're unsure whether it's progressing — if `node`/`next build` CPU time
  (`ps -o etimes,cmd -C node`) is still climbing, it's working.
