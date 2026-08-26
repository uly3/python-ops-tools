# config_diff.py

Compares two `.env`-style configuration files and reports what's missing, extra, or different between them. Built for catching config drift — staging versus production, a deployed config versus the checked-in template, before versus after a change.

**The exit code is the finding**, so it can gate a deploy or fail a CI step when two environments have drifted apart.

## Usage

```bash
python3 config_diff.py <file_a> <file_b> [--ignore-values] [--json FILENAME]
```

| Argument | Default | Description |
|---|---|---|
| `file_a` | *(required)* | First config file |
| `file_b` | *(required)* | Second config file |
| `--ignore-values` | off | Compare key presence only; skip the value-mismatch section |
| `--json FILENAME` | none | Write the structured report to a JSON file |

## Examples

Compare two environments:

```bash
$ python3 config_diff.py staging.env prod.env
Keys in staging.env but not in prod.env...
KEY: CACHE_ENABLED
------------------------------------------------------------
Keys in prod.env but not in staging.env...
KEY: SENTRY_DSN
------------------------------------------------------------
Keys in both staging.env and prod.env but with different values...
API_KEY=***
DB_HOST=10.0.0.99
DB_PASSWORD=***
LOG_LEVEL=warn
------------------------------------------------------------
Count of keys in both staging.env and prod.env that match...
COUNT: 3
$ echo $?
1
```

Identical files:

```bash
$ python3 config_diff.py prod.env prod_copy.env
Count of keys in both prod.env and prod_copy.env that match...
COUNT: 8
$ echo $?
0
```

Check only that the same keys are defined, ignoring what they're set to:

```bash
$ python3 config_diff.py staging.env prod.env --ignore-values
```

Useful when environments are *supposed* to hold different values — different hosts, different credentials — but must define the same set of keys.

Write a machine-readable report:

```bash
$ python3 config_diff.py staging.env prod.env --json report.json
```

```json
{
  "file_a": "/path/to/staging.env",
  "file_b": "/path/to/prod.env",
  "only_in_a": ["CACHE_ENABLED"],
  "only_in_b": ["SENTRY_DSN"],
  "different_values": [
    {"key": "API_KEY", "value_b": "***"},
    {"key": "DB_HOST", "value_b": "10.0.0.99"},
    {"key": "DB_PASSWORD", "value_b": "***"},
    {"key": "LOG_LEVEL", "value_b": "warn"}
  ],
  "matching_count": 3
}
```

## What gets reported

| Category | Meaning |
|---|---|
| Only in A | Keys defined in the first file and absent from the second |
| Only in B | Keys defined in the second file and absent from the first |
| Different values | Keys present in both, holding different values |
| Matching count | Keys present in both **with identical values** |

The matching count deliberately counts identical entries, not shared keys. Two files can define all the same keys and still be entirely different configurations, so a count of shared keys would overstate how aligned they are.

## Parsing

Blank lines and lines beginning with `#` are ignored. Every other line must be a well-formed `KEY=VALUE` assignment; a malformed line aborts the comparison with an error rather than being silently skipped, since a config that can't be fully parsed can't be meaningfully diffed.

Values may contain `=` characters. Only the first `=` separates key from value, so connection strings and base64-padded tokens survive intact:

```
CONNECTION_STRING=host=db;port=5432
```

parses to the key `CONNECTION_STRING` and the value `host=db;port=5432`.

## Secret masking

Values are replaced with a fixed `***` when the key contains `KEY`, `PASSWORD`, `SECRET`, or `TOKEN` (case-insensitive). Masking applies to both terminal output and the JSON report.

The mask is fixed-width rather than one character per character, so it doesn't reveal how long the secret is.

Masking the JSON matters more than masking the terminal. Terminal output scrolls away; a report file gets written to disk, attached to tickets, and shipped to log aggregators. The tool still reports *that* a credential differs between environments — which is the useful signal — without disclosing either value.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Configurations are equivalent — no missing keys, no differing values |
| `1` | Differences found, a file is missing or unreadable, a file parsed to zero keys, or a line was malformed |

Under `--ignore-values`, differing values do not count toward the exit status — only key presence does.

Gate a deploy on config parity:

```bash
python3 config_diff.py template.env prod.env --ignore-values && ./deploy.sh
```

## Notes

Both paths are validated for existence and for being regular files before either is opened, so pointing at a directory produces a clear error rather than a traceback.

A file that parses to zero keys is treated as an error rather than an empty-but-valid config. An empty config file is far more often a wrong path or a failed write than a deliberate state.
