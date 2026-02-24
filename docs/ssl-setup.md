# SSL Setup for rtbl.cloud

HTTPS is handled by **Let's Encrypt** via certbot. Run these steps once on the VPS.

## Prerequisites

- Cloudflare DNS A record for `rtbl.cloud` set to **grey cloud (DNS only)** pointing to `187.77.221.145`
- Containers are running (`docker ps` shows both up)

## One-time cert setup

```bash
# 1. Install certbot
apt update && apt install -y certbot

# 2. Stop nginx to free port 80 for the challenge
docker stop roundtable-nginx

# 3. Get the cert
certbot certonly --standalone -d rtbl.cloud -d www.rtbl.cloud

# 4. Create the certbot webroot dir (for future renewals)
mkdir -p /var/www/certbot
```

## Deploy the updated nginx image

On your Mac, build and push the new frontend image (tag 0.0.6 — nginx.conf now has SSL):

```bash
cd roundtable
TAG=0.0.6 make build-frontend && TAG=0.0.6 make push-frontend
```

Then on the VPS, pull and restart:

```bash
docker compose -f ~/roundtable/docker/docker-compose.yml pull nginx
docker compose -f ~/roundtable/docker/docker-compose.yml up -d
```

nginx now:
- Port 80  → redirects all traffic to HTTPS (serves ACME challenges for renewals)
- Port 443 → TLS termination with the Let's Encrypt cert, proxies to the app

## Auto-renewal cron

Certs expire in 90 days. Set up auto-renewal:

```bash
crontab -e
```

Add:
```
0 3 * * * certbot renew --webroot -w /var/www/certbot --quiet && docker exec roundtable-nginx nginx -s reload
```

## Verify

```bash
curl -v https://rtbl.cloud/api/health
```

Should return `200` with `{"status": "ok"}`.
