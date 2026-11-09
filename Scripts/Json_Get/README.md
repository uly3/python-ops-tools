# json_get.py

Pulls a single value out of a JSON file using a dot-separated path. Built for the everyday case of needing one field — a pod name, a port, a status — out of a large JSON document, without writing a parser each time.

Similar in spirit to `jq -r` and `kubectl -o jsonpath`, in plain Python.

## Usage

```bash
python3 json_get.py <path> <file>
```

| Argument | Description |
|---|---|
| `path` | Dot-separated path to the value, e.g. `items.0.metadata.name` |
| `file` | JSON file to read |

## Examples

Given a `pods.json` shaped like `kubectl get pods -o json` output:

```json
{
  "items": [
    {"metadata": {"name": "web-01"}, "status": {"phase": "Running", "restarts": 0}},
    {"metadata": {"name": "web-02"}, "status": {"phase": "Running", "restarts": 3}}
  ]
}
```

Fetch a string:

```bash
$ python3 json_get.py items.0.metadata.name pods.json
web-01
```

Fetch a number:

```bash
$ python3 json_get.py items.1.status.restarts pods.json
3
```

Fetch a whole object:

```bash
$ python3 json_get.py items.0.status pods.json
{
  "phase": "Running",
  "restarts": 0
}
```

## Path syntax

Each segment of the path steps one level deeper into the document:

- On an **object**, the segment is used as a key — `metadata`, `status`
- On an **array**, the segment must be a non-negative integer and is used as an index — `0`, `1`

The same text means different things depending on where it lands. `0` is an index into an array but would be a literal key name inside an object, which is why the type of each level is checked before the segment is applied.

Negative indices (`items.-1`) are not supported. A path either names a position counted from the start or it fails.

## Output

Strings print raw, without surrounding quotes. Everything else — numbers, booleans, null, objects, arrays — prints as JSON.

Raw strings let the result drop straight into a shell variable:

```bash
NAME=$(python3 json_get.py items.0.metadata.name pods.json)
echo "$NAME"     # web-01, not "web-01"
```

Non-strings go through JSON serialization so they print in JSON's spelling rather than Python's — `true` and `null`, not `True` and `None`.

## Errors

A path that can't be followed reports the exact segment where it broke:

```bash
$ python3 json_get.py items.3.status.restarts pods.json
Error: path 'items.3.status.restarts' failed at 'restarts'

$ python3 json_get.py items.9.metadata.name pods.json
Error: path 'items.9.metadata.name' failed at '9'

$ python3 json_get.py items.0.metadata.name.first pods.json
Error: path 'items.0.metadata.name.first' failed at 'first'
```

Those are three different problems — a missing key, an index past the end of an array, and an attempt to descend into a value that has no children. Naming the segment makes each one obvious at a glance, which matters on long paths.

Errors are written to stderr, never stdout. If a failed lookup printed to stdout, the error text would be captured into whatever variable or file was expecting the value, and passed along as if it were real data.

A missing file, a path that isn't a regular file, and invalid JSON are each reported with their own message rather than a traceback.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Value found and printed |
| `1` | File missing, not a regular file, not valid JSON, or the path could not be followed |
| `2` | Invalid arguments |

Usable as a guard:

```bash
python3 json_get.py items.0.status.phase pods.json || echo "lookup failed"
```

## Notes

Input is read from a file only, not from a pipe. That keeps usage explicit — every invocation names its source.

The file is read with UTF-8 encoding, which is what JSON is specified to use. On Windows, files written by PowerShell's `Out-File` default to UTF-16 and won't parse; save JSON from an editor instead.

Standard library only.
