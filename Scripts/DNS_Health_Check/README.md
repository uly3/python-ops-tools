# dns_health_check.py

Verifies a Pi-hole + Unbound DNS stack layer by layer: that Pi-hole resolves real domains, that it blocks ad domains, that Unbound resolves on its own, and that Unbound enforces DNSSEC. Each layer can fail independently, so each gets its own check.

Runs on the Pi itself, because Unbound only listens on `127.0.0.1`.

## Usage

```bash
python3 dns_health_check.py [--dns-server IP] [--unbound-port PORT] [--timeout SECONDS]
```

| Argument | Default | Description |
|---|---|---|
| `--dns-server` | `10.0.1.100` | Pi-hole address |
| `--unbound-port` | `5335` | Port Unbound listens on at `127.0.0.1` |
| `--timeout` | `10` | Seconds to wait for each query |

## Example

```bash
$ python3 dns_health_check.py
PASS  google.com via Pi-hole             status=NOERROR ip=142.251.32.14
PASS  doubleclick.net blocked            status=NOERROR ip=0.0.0.0
PASS  google.com via Unbound             status=NOERROR ip=142.251.32.14
PASS  DNSSEC enforcement                 status=SERVFAIL ip=None

4/4 checks passed
```

With Pi-hole unreachable, the Unbound checks still pass on their own — which tells you which layer is broken:

```bash
$ python3 dns_health_check.py --dns-server 10.0.1.99
FAIL  google.com via Pi-hole             UNREACHABLE (no response)
FAIL  doubleclick.net blocked            UNREACHABLE (no response)
PASS  google.com via Unbound             status=NOERROR ip=142.251.32.14
PASS  DNSSEC enforcement                 status=SERVFAIL ip=None

2/4 checks passed
```

## The four checks

| # | Query | Sent to | Pass condition |
|---|---|---|---|
| 1 | `google.com` | Pi-hole | A real IP, not `0.0.0.0` |
| 2 | `doubleclick.net` | Pi-hole | Exactly `0.0.0.0` (blocked) |
| 3 | `google.com` | Unbound | A real IP, not `0.0.0.0` |
| 4 | `fail01.dnssec.works` | Unbound | **`SERVFAIL`** |

Checks 1 and 3 reject `0.0.0.0` explicitly. A domain that has been blocked by mistake still returns a non-empty answer, so "got an answer back" isn't the same as "resolution works."

Check 3 bypasses Pi-hole entirely. Pi-hole caches answers, so with Unbound down, Pi-hole can keep returning cached results for popular domains — checks 1 and 2 would stay green while the actual resolver is dead. Querying Unbound directly is the only way to see that.

## Why check 4 passes on a failure

`fail01.dnssec.works` is a test domain with deliberately invalid DNSSEC signatures. A resolver that validates DNSSEC must refuse to return it, and does so with `SERVFAIL`.

So the result is inverted from the other three: `SERVFAIL` means validation is working. Getting an IP back would mean Unbound handed over data whose signature didn't verify — the exact attack DNSSEC exists to prevent.

## Timeout versus SERVFAIL

These are reported differently on purpose, because they mean different things and lead to different fixes:

| Result | Meaning | Where to look |
|---|---|---|
| `UNREACHABLE (no response)` | Nothing came back — service down, wrong port, host unreachable | `systemctl status`, firewall, network |
| `status=SERVFAIL` | The server answered and reported failure — it's running | Upstream reachability, DNSSEC, logs |

This matters most for check 4. A stopped Unbound also returns no IP, so if "no IP" were treated as the pass condition, a dead resolver would report healthy DNSSEC. A timeout always fails check 4, regardless of what didn't come back.

Detection covers both dig's own timeout (exit code `9`) and Python's subprocess timeout as a backstop, which is set slightly longer than dig's so dig's own message wins when both are in play.

## Parsing

dig is run once per check with full output, and both the response code and the answer are read from it. Using `+short` would be simpler for extracting an IP but drops the status line, which check 4 depends on.

IP addresses are taken from the ANSWER section only. dig's output also contains the server address in its footer, so searching the whole output would find an IP on every query — including ones that returned nothing.

## Scheduling

Runs nightly from cron, notifying only on failure:

```
0 20 * * * /usr/bin/python3 /home/uly/Desktop/dns_health_check.py > /home/uly/Desktop/dns_health.log 2>&1 || curl -s -d "DNS health check failed — check the Pi" ntfy.sh/<topic>
```

`||` sends the push notification only when the script exits non-zero. A notification on every successful run would quickly become noise that trains you to ignore the one that matters.

The log is overwritten (`>`) rather than appended, so it always holds just the most recent run and never grows.

## Cold cache and the timeout

The first query for a DNSSEC-failing domain is slow. Unbound has to fetch DNSKEY and DS records and walk the chain of trust before it can reject the signature, and on a Raspberry Pi that can take several seconds. Bogus results are cached only briefly, so a once-a-day scheduled run nearly always hits a cold cache.

The default timeout is set to 10 seconds for that reason. At 5, check 4 intermittently reported a false `UNREACHABLE` on cold runs — which, with failure notifications wired up, means a false alert.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All four checks passed |
| `1` | One or more checks failed or were unreachable |

## Requirements

`dig` (from `dnsutils` / `bind9-dnsutils`). Python standard library only.

Arguments are passed to `subprocess.run()` as a list rather than through a shell — dig needs no pipes, globbing, or chaining, so there is no reason to involve one.
