# port_check.py

Checks whether TCP ports are open on one or more hosts. Answers "is the service actually listening?" — and when it isn't, distinguishes *refused* from *no response*, which point to different problems.

## Usage

```bash
python3 port_check.py <host:port> [<host:port> ...] [--timeout SECONDS]
```

| Argument | Default | Description |
|---|---|---|
| `targets` | *(required)* | One or more `host:port` pairs. Hosts may be IPs or hostnames. |
| `--timeout` | `2` | Seconds to wait for each connection |

## Examples

Check services on a homelab host:

```bash
$ python3 port_check.py 192.168.1.233:22 10.0.1.100:53
REFUSED     192.168.1.233:22
OPEN        10.0.1.100:53
1/2 OPEN
```

Hostnames work the same as IPs:

```bash
$ python3 port_check.py google.com:443 1.1.1.1:53
OPEN        google.com:443
OPEN        1.1.1.1:53
2/2 OPEN
```

Malformed targets are reported individually, and the valid ones are still checked:

```bash
$ python3 port_check.py 192.168.1.233 192.168.1.233:abc 192.168.1.233:99999 192.168.1.233:22
INVALID     192.168.1.233 (expected host:port)
INVALID     192.168.1.233:abc (port is not a number)
INVALID     192.168.1.233:99999 (port must be 1-65535)
REFUSED     192.168.1.233:22
0/4 OPEN
```

## Outcomes

Every target produces exactly one line:

| Result | Meaning | Usually points to |
|---|---|---|
| `OPEN` | TCP handshake completed | Service is listening |
| `REFUSED` | Host answered with a reset | Host is up, but nothing is listening on that port — or a firewall is set to *reject* |
| `TIMEOUT` | No answer at all | Host is down, unreachable, or a firewall is silently *dropping* the traffic |
| `HOSTNAME_UNRESOLVED` | DNS lookup failed | Typo, or a DNS problem upstream |
| `INVALID` | Target couldn't be parsed | Missing colon, non-numeric port, or port outside 1–65535 |

The `REFUSED` / `TIMEOUT` split is the useful one. A refusal comes back instantly — something on the far end actively answered "no." A timeout means nothing answered. Against a host you know is running, a timeout usually isn't a dead service at all; it's a firewall configured to drop rather than reject, eating the packets without reply.

## Parsing

Targets are split on the **last** colon, so the host portion can be an IP or a hostname. The host is not validated separately — if it can't be resolved or reached, the connection attempt itself reports why.

The port is checked for being an integer in the valid range before any connection is attempted, so a bad argument produces a clear message rather than whatever the socket library does with an out-of-range number.

A malformed target never stops the run. Each target is handled independently, so one typo in a list of twenty doesn't hide the results for the other nineteen.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Every target is open |
| `1` | At least one target was refused, timed out, unresolved, invalid, or errored |

Usable as a gate or a check:

```bash
python3 port_check.py 10.0.1.100:22 10.0.1.100:53 || echo "a service is down"
```

## Notes

**TCP only.** A UDP port has no handshake, so there's nothing to connect to and no reliable way to tell "open" from "silently ignored." Services on UDP — DNS's primary transport, Minecraft Bedrock on 19132, WireGuard — can't be checked this way. DNS happens to answer on TCP 53 as well, which is why it appears in the examples.

**The timeout is per connection.** Five unreachable targets at `--timeout 2` take about ten seconds. Lower the timeout for large lists on a reliable network.

**A dead host can report two ways.** If nothing on the path responds, the connection times out. If a router along the way returns an ICMP "unreachable," the OS reports that immediately instead, and it appears as an `An error occurred...` line with the system's message. Both mean the host isn't reachable; which one you see depends on the network in between.

Each connection is opened and closed immediately — nothing is sent once the handshake completes, so the check is harmless to the services it probes.

Standard library only.
