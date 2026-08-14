# Deploy — deimos, Docker Compose, Cloudflare Tunnel

Deployment target is `deimos` (Debian home server) via Docker Compose. The
`api` container is only bound to loopback (`127.0.0.1:8080`) — the Cloudflare
Tunnel is the sole ingress path, so nothing here needs a forwarded port or a
public IP.

## 1. One-time host setup

```
git clone <repo> /opt/fit-link   # or wherever you keep it on deimos
cd /opt/fit-link
cp .env.example .env
```

Fill in `.env`:

- `DATABASE_URL` — only read by local (non-compose) `uvicorn --reload` runs;
  under compose the `api` service builds its own from `POSTGRES_*` instead.
- `SECRET_KEY` — `openssl rand -hex 32`
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` — pick real values,
  not the `fitlink`/`changeme` placeholders.
- `CLOUDFLARE_TUNNEL_TOKEN` — from step 2 below.

## 2. Create the tunnel (Cloudflare Zero Trust dashboard)

1. **Zero Trust → Networks → Tunnels → Create a tunnel.**
2. Choose **Cloudflared**, name it (e.g. `fit-link`).
3. On the "Install connector" step, pick **Docker** — the dashboard shows a
   `docker run` command with a `--token <TOKEN>` flag. Copy just the token
   value into `CLOUDFLARE_TUNNEL_TOKEN` in `.env`. The `cloudflared` service
   in `docker-compose.yml` already runs `tunnel run` with that token; you
   don't need the dashboard's docker command itself.
4. **Public Hostname** tab, add a route:
   - Subdomain/domain: whatever you want the app reachable at (e.g.
     `fitlink.yourdomain.com`)
   - Service: `HTTP` → `api:8080` (the compose service name and port — the
     tunnel reaches it over the compose network, not localhost)
5. Save. The tunnel won't show "Healthy" until the `cloudflared` container is
   actually running (step 4 below).

## 3. Create the Access application (email OTP gate)

1. **Zero Trust → Access → Applications → Add an application → Self-hosted.**
2. Application domain: the same hostname from step 2.4.
3. Add a policy:
   - Action: **Allow**
   - Include: **Emails** → your email address(es)
4. Under **Login methods**, ensure **One-time PIN** is enabled (it's on by
   default).
5. Save. Hitting the hostname now prompts for an email OTP before it ever
   reaches the `api` container.

## 4. Bring the stack up

```
make up        # api + postgres only
make migrate
make seed
```

Verify locally first: `curl http://127.0.0.1:8080/health` on deimos itself
should return `{"status": "ok"}`.

Once `.env`'s `CLOUDFLARE_TUNNEL_TOKEN` is set and the Access application
exists:

```
docker compose --profile tunnel up -d --build
```

(`make deploy` does this plus `git pull`, `migrate`, and `seed` — use it for
subsequent deploys once the tunnel is already provisioned.)

Visit the public hostname from a phone — you should hit the Cloudflare Access
OTP prompt, then the app.

## 5. Ongoing deploys

```
make deploy
```

Pulls latest, rebuilds `api`, restarts the full stack including `cloudflared`,
runs migrations, and reloads content from `content/`.

## 6. Backups

```
./scripts/backup.sh
```

Dumps the `postgres` service to `backups/fitlink-<timestamp>.sql.gz`. See the
cron line documented at the top of `scripts/backup.sh` to automate it.

## Notes / things not done here

- The optional `Cf-Access-Jwt-Assertion` validation middleware (spec §8,
  "reached directly" hardening) is **not implemented in this phase** — the
  tunnel + Access policy is the only thing currently standing between the
  internet and `api`. Worth adding later as defense in depth, but it's a code
  change, not a deploy-docs change, so it's out of scope here.
- `docker-compose.yml` binds `api` to `127.0.0.1` only, so even a
  misconfigured firewall on deimos doesn't expose it directly — only
  `cloudflared` reaches it, over the compose-internal network.
