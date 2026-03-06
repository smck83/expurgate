![expurgate - simplify, hide and exceed SPF lookup limits](https://github.com/smck83/expurgate/blob/main/expurgate.png?raw=true)

> A dockerized, multi-domain SPF flattening solution. Expurgate resolves your SPF records into IP addresses, hides your vendor list behind an SPF macro, and eliminates the 10 DNS lookup limit — all without a UI or database.

- 🌐 **Don't want to self-host?** Try [spf.guru](https://spf.guru)
- 📦 **Single container?** See [Expurgate Solo](https://github.com/smck83/expurgate-solo)

---

## Table of Contents

- [What is Expurgate?](#what-is-expurgate)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
  - [Option 1: Live Demo](#option-1-live-demo)
  - [Option 2: Amazon Lightsail (Recommended)](#option-2-amazon-lightsail-recommended)
  - [Option 3: Manual / Docker Compose](#option-3-manual--docker-compose)
- [Environment Variables](#environment-variables)
- [Sample DNS Queries](#sample-dns-queries)
- [Performance](#performance)
- [Recent Enhancements](#recent-enhancements)

---

## What is Expurgate?

**expurgate** *(EK-spur-gayt)* — verb — *to remove matter thought to be objectionable or unsuitable.*

Expurgate is a self-hosted SPF flattening (compression) solution. It replaces your complex, over-limit SPF record with a single SPF macro, and handles all the DNS resolution behind the scenes using [rbldnsd](https://linux.die.net/man/8/rbldnsd).

There is no web UI and no database. Configuration is done entirely via environment variables and a source DNS TXT record on a subdomain of your choice.

> **SPF Primer:** SPF (Sender Policy Framework) records are DNS TXT records that tell receiving mail servers which IPs are authorised to send email on behalf of your domain. They apply to the `ENVELOPE FROM:` address (not the visible `From:` header). SPF alone does not prevent spoofing of the displayed sender — that requires [DMARC](https://en.wikipedia.org/wiki/DMARC). [Read more →](https://en.wikipedia.org/wiki/Sender_Policy_Framework)

---

## The Problem

SPF records have three hard constraints that cause real operational pain:

1. **10 DNS lookup limit** — Each `include:`, `a:`, and `mx:` directive counts toward the limit. A single `include:_spf.google.com` may chain to 2–3 more lookups underneath. Third-party providers can add new hostnames without warning, silently pushing you over the limit.
2. **255-character limit per TXT record line** — Managing multiple vendors across multiple domains quickly becomes unwieldy.
3. **Visibility** — Your SPF record publicly discloses every email vendor you use (e.g. `include:sendgrid.net`, `include:mailgun.org`), which can aid targeted phishing attacks using those vendors' branding.

With DMARC adoption accelerating, organisations that previously ignored SPF are now investing in it — and running straight into these limits.

---

## The Solution

### Simplify
Expurgate replaces your multi-include SPF record with a single SPF macro. No more counting lookups, no more juggling 255-byte line limits.

### Hide
Your current SPF record is moved to a private subdomain (your "source of truth"). The public-facing record becomes a macro that reveals nothing about your vendors:

**Before:**
```
v=spf1 include:sendgrid.net include:_spf.google.com include:mailgun.org include:spf.protection.outlook.com include:_netblocks.mimecast.com -all
```

**After:**
```
v=spf1 include:%{ir}.%{d}._spf.yourdomain.com -all
```

> **Disclaimer:** This is security by obscurity — a motivated attacker can still probe known vendor IP ranges against your macro. However, it does raise the bar for opportunistic reconnaissance.

### Exceed SPF Limits
Expurgate resolves all hostnames to IP addresses and subnets on a schedule (`DELAY=` seconds), and serves results from rbldnsd. Your public SPF record uses only **1 lookup**, regardless of how many vendors are in your source record. IPv4 and IPv6 are both supported.

---

## How It Works

Expurgate runs two containers (a third is optional):

| Container | Role |
|---|---|
| `expurgate-resolver` | Reads your source SPF record from a private subdomain, resolves all hostnames to IPs, and writes rbldnsd config files. Reruns every `DELAY` seconds. |
| `expurgate-rbldnsd` | A DNS server (rbldnsd) that answers SPF macro queries using the generated config files. Listens on UDP/53. |
| `dnsdist` *(optional)* | Load balancer in front of rbldnsd. Handles DDoS protection and adds TCP/53 support. Note: all traffic to rbldnsd will appear to originate from dnsdist. |

![Expurgate Architecture Diagram](https://github.com/smck83/expurgate/blob/main/expurgate-diagram.png)

When a receiving mail server evaluates your SPF record, it queries your macro (e.g. `1.128.85.209.yourdomain.com._spf.yourdomain.com`). Expurgate's rbldnsd responds with just the relevant IP — not your full vendor list.

> **Important:** Both containers must share the same volume path so the resolver can write config files that rbldnsd can read.

---

## Quick Start

### Option 1: Live Demo

A live demo is available for testing without any setup:

**[https://xpg8.ehlo.email/](https://xpg8.ehlo.email/)**

> ⚠️ Hosted on a single AWS Lightsail instance. No guarantee or warranty.

Common SPF records are pre-loaded so you can test your own queries.

---

### Option 2: Amazon Lightsail (Recommended)

#### Step 1 — Copy your SPF record to a private subdomain

Pick an obscure subdomain prefix (e.g. `_sd6sdyfn`) and publish your existing SPF record there:

```
_sd6sdyfn.yourdomain.com.   IN  TXT "v=spf1 include:sendgrid.net include:mailgun.org -all"
_sd6sdyfn.yourdomain2.com.  IN  TXT "v=spf1 include:mailgun.org -all"
_sd6sdyfn.yourdomain3.com.  IN  TXT "v=spf1 ip4:192.0.2.1 include:email.freshdesk.com include:sendgrid.net ~all"
```

#### Step 2 — Run the Lightsail install script

```bash
wget https://raw.githubusercontent.com/smck83/expurgate/main/install.sh && \
chmod 755 install.sh && ./install.sh && \
docker run -d \
  -v /opt/expurgate/:/spf-resolver/output/ \
  -e DELAY=300 \
  -e MY_DOMAINS='yourdomain.com yourdomain2.com yourdomain3.com' \
  -e SOURCE_PREFIX='_sd6sdyfn' \
  --dns 1.1.1.1 --dns 8.8.8.8 \
  smck83/expurgate-resolver && \
docker run -d \
  -p 53:53/udp \
  -v /opt/expurgate/:/var/lib/rbldnsd/:ro \
  -e OPTIONS='-e -t 5m -l -' \
  -e TYPE=combined \
  -e ZONE=_spf.yourdomain.com \
  smck83/expurgate-rbldnsd
```

Assign a static IP to your Lightsail instance and open UDP port 53.

#### Step 3 — Create DNS records pointing to your instance

```
; A record for your rbldnsd name server
spf-ns.yourdomain.com.   IN  A   192.0.2.1

; Delegate the _spf subdomain to your instance
_spf.yourdomain.com.     IN  NS  spf-ns.yourdomain.com.
```

#### Step 4 — Replace your old SPF record with the macro

Apply this to **all** domains you manage (they all point to the same `_spf.yourdomain.com` server):

```
v=spf1 include:%{ir}.%{d}._spf.yourdomain.com -all
```

---

### Option 3: Manual / Docker Compose

For full control, use [docker-compose.yaml](https://github.com/smck83/expurgate/blob/main/docker-compose.yaml) or follow the steps below.

#### Step 1 — Create DNS records

```
spf-ns.yourdomain.com.   IN  A   192.0.2.1
_spf.yourdomain.com.     IN  NS  spf-ns.yourdomain.com.
```

Consider using [dnsdist](https://dnsdist.org/) in front of rbldnsd if you need TCP/53 or DDoS protection.

#### Step 2 — Copy your SPF record to a private subdomain

Same as [Step 1 above](#step-1--copy-your-spf-record-to-a-private-subdomain).

#### Step 3 — Run expurgate-resolver

```bash
docker run -t \
  -v /xpg8/rbldnsd-configs:/spf-resolver/output \
  -e DELAY=300 \
  -e MY_DOMAINS="yourdomain.com yourdomain2.com yourdomain3.com" \
  -e RUNNING_CONFIG_ON=1 \
  -e SOURCE_PREFIX="_sd6sdyfn" \
  --dns 1.1.1.1 --dns 8.8.8.8 \
  smck83/expurgate-resolver
```

> **Tip:** For large domain volumes, consider running a [local DNS recursor](https://doc.powerdns.com/recursor/) instead of using public resolvers like `1.1.1.1` or `8.8.8.8`.

#### Step 4 — Run expurgate-rbldnsd

```bash
docker run -t \
  -p 53:53/udp \
  -v /xpg8/rbldnsd-configs:/var/lib/rbldnsd/:ro \
  -e OPTIONS='-e -t 5m -l -' \
  -e TYPE=combined \
  -e ZONE=_spf.yourdomain.com \
  smck83/expurgate-rbldnsd
```

#### Step 5 — Replace your old SPF record with the macro

```
v=spf1 include:%{ir}.%{d}._spf.yourdomain.com -all
```

---

## Environment Variables

### expurgate-resolver

| Variable | Required | Default | Description |
|---|---|---|---|
| `MY_DOMAINS` | Yes* | — | Space-separated list of domains to generate config files for. E.g. `yourdomain.com microsoft.com github.com` |
| `SOURCE_PREFIX` | No | `_xpg8` | Subdomain prefix where your source SPF record is hosted. E.g. `_sd6sdyfn` → reads from `_sd6sdyfn.yourdomain.com` |
| `DELAY` | No | `300` | Seconds between resolver runs |
| `RUNNING_CONFIG_ON` | No | `1` | When `1`, generates a single `running-config` file for all domains instead of one file per domain. Recommended — avoids rbldnsd restarts when adding/removing domains |
| `SOURCE_PREFIX_OFF` | No | `False` | Disables source prefix lookup. Only change for testing |
| `UPTIMEKUMA_PUSH_URL` | No | — | [Uptime Kuma](https://github.com/louislam/uptime-kuma) push URL for health monitoring. Must end in `ping=` |
| `TZ` | No | — | Timezone, e.g. `Australia/Sydney`. [Full list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| `SOA_HOSTMASTER` | No | — | Email address for the SOA record. Not required for function, but aids DNS standards compliance |
| `NS_RECORD` | No | — | Hostname for the NS record. Not required for function, but aids DNS standards compliance |

*If `MY_DOMAINS` is not set, `SOURCE_PREFIX_OFF` is automatically enabled and the container runs in demo mode using `microsoft.com`, `mimecast.com`, and `google.com`.

### expurgate-rbldnsd

| Variable | Required | Description |
|---|---|---|
| `OPTIONS` | Yes | rbldnsd run options. Recommended: `-e -t 5m -l -` (`-e` allows non-network CIDR addresses; `-t 5m` sets TTL; `-l -` logs to stdout) |
| `TYPE` | Yes | rbldnsd zone type. Recommended: `combined` |
| `ZONE` | Yes | The DNS zone served by rbldnsd. Must match the NS delegation from Step 1. E.g. `_spf.yourdomain.com` |

---

## Sample DNS Queries

When a receiving MTA checks SPF, it expands the macro in your SPF record and queries rbldnsd. The macro variables are:

- **`%{ir}`** — The sending IP address, reversed. E.g. `209.85.128.1` → `1.128.85.209`
- **`%{d}`** — The domain in the `ENVELOPE FROM:` address

### SPF Pass — IPv4 ([Test](https://ehlo.email/?domain=1.128.85.209._spf.google.com.s.ehlo.email#spf))

Sending IP: `209.85.128.1`, domain: `_spf.google.com`

```
Query:    1.128.85.209._spf.google.com.s.ehlo.email
Response: 1.128.85.209._spf.google.com.s.ehlo.email. 300 IN TXT "v=spf1 ip4:209.85.128.1 -all"
```

Only the queried IP is returned — not your full vendor list.

### SPF Pass — IPv6 ([Test](https://ehlo.email/?domain=1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.4.0.b.8.f.7.0.6.2._spf.google.com.s.ehlo.email#spf))

Sending IP: `2607:f8b0:4000::1`, reversed in dotted notation: `1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.4.0.b.8.f.7.0.6.2`

```
Query:    1.0.0.0...4.0.b.8.f.7.0.6.2._spf.google.com.s.ehlo.email
Response: ...300 IN TXT "v=spf1 ip6:2607:f8b0:4000::1 ~all"
```

### SPF Fail ([Test](https://ehlo.email/?domain=1.0.0.127._spf.google.com.s.ehlo.email#spf))

Sending IP: `127.0.0.1` (not in the authorised list)

```
Query:    1.0.0.127._spf.google.com.s.ehlo.email
Response: 1.0.0.127._spf.google.com.s.ehlo.email. 300 IN TXT "v=spf1 -all"
```

---

## Performance

Tested with **570+ domains** over 38 days:

| Runtime | Avg. time per loop |
|---|---|
| Python | ~2 minutes |
| PyPy | < 1 minute |

All Docker images use PyPy for the resolver script.

> **Note:** PyPy is more memory-intensive than Python. On low-spec instances (e.g. AWS Lightsail $3.50/month), the resolver may silently stop after several days of continuous running and restart. Monitor accordingly.

![Python vs PyPy performance graph](https://github.com/smck83/expurgate/blob/main/python-vs-pypy.png)

---

## Recent Enhancements

- **SOA/NS compliance** — Added `SOA_HOSTMASTER` and `NS_RECORD` env vars to comply with DNS standards.
- **Running config on by default** — A single `running-config` file for all domains avoids rbldnsd restarts when domains are added or removed.
- **Reliability improvement** — Domains in `MY_DOMAINS` must have a valid SPF TXT record (`v=spf1 ...`) before config files are written to disk.
- **PyPy** — Docker image switched to PyPy for 2–5x resolver performance improvement.
- **IPv6 (AAAA) support** — Hostname lookups now include AAAA records for IPv6 addresses.
- **Expurgate Solo** — Single-container variant using supervisord: [expurgate-solo](https://github.com/smck83/expurgate-solo).
- **Deduplication** — Duplicate IPs/subnets are only written once to config files.
- **Write-on-change** — Config files are only regenerated when a record change is detected, reducing unnecessary disk writes.
- **DNS cache** — Common includes (e.g. `sendgrid.net`, `_spf.google.com`) are cached in memory across domains, reducing redundant DNS queries.
- **RestDB support** — `MY_DOMAINS` can optionally be managed via RestDB instead of environment variables.

---

## Support the Project

If Expurgate has been useful, consider [buying me a coffee ☕](https://www.buymeacoffee.com/smc83)
