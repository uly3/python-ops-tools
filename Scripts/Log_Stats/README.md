# log_stats.py

Parses a web-server access log and reports traffic statistics: requests per status code, the busiest client IPs, the most-requested paths, and total bytes transferred. Handles malformed lines without aborting.

Answers the questions you actually ask of a log — who's hitting us hardest, what's being requested, and which endpoints are throwing errors.

## Usage

```bash
python3 log_stats.py <logfile> [--top N] [--status CODE] [--json FILENAME]
```

| Argument | Default | Description |
|---|---|---|
| `logfile` | *(required)* | Access log to parse |
| `--top N` | `5` | How many top IPs and paths to list |
| `--status CODE` | none | Restrict the entire report to one status code |
| `--json FILENAME` | none | Write the structured report to a JSON file |

## Examples

Full report:

```bash
$ python3 log_stats.py access.log

Requests: 10

Requests per status code...
  200: 7
  404: 1
  500: 2

Top 5 IPs...
  10.0.0.5: 4
  10.0.0.7: 3
  10.0.0.9: 2
  10.0.0.11: 1

Top 5 paths...
  /api/health: 4
  /api/login: 2
  /api/users: 2
  /api/metrics: 1
  /api/users/42: 1

Total bytes transferred: 13.06 KB
Unparseable lines: 2
```

Investigate errors — which clients and endpoints are producing 500s:

```bash
$ python3 log_stats.py access.log --status 500
Filtered to status 500

Requests: 2

Top 5 IPs...
  10.0.0.5: 1
  10.0.0.9: 1

Top 5 paths...
  /api/login: 1
  /api/users: 1
```

Machine-readable output:

```bash
$ python3 log_stats.py access.log --json report.json
```

```json
{
  "status_codes": {"200": 7, "404": 1, "500": 2},
  "top_ips": {"10.0.0.5": 4, "10.0.0.7": 3},
  "top_paths": {"/api/health": 4, "/api/login": 2},
  "total_requests": 10,
  "total_bytes": 13373,
  "total_bytes_human": "13.06 KB",
  "unparseable_lines": 2
}
```

Both the raw byte count and the formatted string are included — the first for arithmetic downstream, the second for display.

## Log format

Expects the Common Log Format produced by Apache and nginx:

```
10.0.0.5 - - [15/Sep/2026:09:14:22 +0000] "GET /api/health HTTP/1.1" 200 1543
```

Six fields are extracted: client IP, timestamp, HTTP method, request path, status code, and response size in bytes.

A single regular expression captures all six in one pass. Matching the whole line at once means every field is guaranteed to come from the same request — separate patterns applied independently could each match a different part of a malformed line and silently assemble a record that never existed.

## Filtering

`--status CODE` filters the entire report rather than just adding a line to it. IP counts, path counts, and the byte total all reflect only matching requests, which turns the tool from "how much traffic" into "who is causing these errors and where."

The unparseable-line count is a property of the file, not of the filtered subset, so it stays the same regardless of `--status`.

## Malformed lines

Lines that don't match the expected format are counted and skipped, and the total is reported at the end. Real logs contain truncated writes, health-check probes from other tooling, and occasional garbage; a tool that aborts on the first unrecognized line is useless against production data.

Reporting the count rather than silently discarding matters too — a sudden jump in unparseable lines usually means the log format changed or something upstream is writing to the wrong file.

## Determinism

Top-N lists are sorted by request count descending, with ties broken alphabetically. Identical input produces byte-identical output on every run and every machine:

```bash
$ python3 log_stats.py access.log > run1.txt
$ python3 log_stats.py access.log > run2.txt
$ diff run1.txt run2.txt && echo "IDENTICAL"
IDENTICAL
```

Without the tie-break, two paths with equal counts could appear in either order, producing spurious differences when comparing reports across time or between servers.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Report generated from at least one parsed request |
| `1` | File missing or not a regular file, no parseable lines, or `--status` matched nothing |

A filter matching zero requests exits non-zero — usually it means a typo'd status code rather than a genuinely clean log.

## Notes

Reads the file line by line, so memory use is constant regardless of log size. A multi-gigabyte access log is handled the same as a ten-line sample.

Response sizes are taken from the log's own byte field, which reflects the response body as the server recorded it — not bytes on the wire, and not including headers.
