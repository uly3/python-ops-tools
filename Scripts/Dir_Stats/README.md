# dir_stats.py

Walks a directory tree and reports what's in it: total file count, total size, a breakdown by file extension, and the largest files. Answers the "what's taking up space in here" question without leaving the terminal.

Cross-platform — uses `pathlib` rather than shelling out, so it behaves identically on macOS, Linux, and Windows.

## Usage

```bash
python3 dir_stats.py <directory> [--filter EXT] [--top N] [--min-size N] [--verbose]
```

| Argument | Default | Description |
|---|---|---|
| `directory` | *(required)* | Directory to scan, recursively |
| `--filter EXT` | none | Only count files with this extension, e.g. `.py` |
| `--top N` | `5` | How many of the largest files to list |
| `--min-size N` | `0` | Ignore files smaller than N bytes |
| `--verbose` | off | Also list every matching file, largest first |

## Examples

Scan a directory:

```bash
$ python3 dir_stats.py ~/Desktop/Automation_Practice
Directory: /Users/uly/Desktop/Automation_Practice
Files:     31
Total:     67.18 KB

By extension:
  .py        11
  .csv       11
  .db        2
  .sqlite    2
  .json      2
  .log       1
  .xml       1
  .tsv       1

Top 5 largest:
    12.00 KB  /Users/uly/Desktop/Automation_Practice/backup.db
    12.00 KB  /Users/uly/Desktop/Automation_Practice/example.sqlite
     8.78 KB  /Users/uly/Desktop/Automation_Practice/Chapter16.py
     8.00 KB  /Users/uly/Desktop/Automation_Practice/logs.sqlite
     8.00 KB  /Users/uly/Desktop/Automation_Practice/ops.db
```

Narrow to a single file type:

```bash
$ python3 dir_stats.py ~/Desktop/Automation_Practice --filter .py
Files:     11
Total:     24.00 KB

By extension:
  .py        11
```

Skip small files and show fewer results:

```bash
$ python3 dir_stats.py ~/Desktop/Automation_Practice --min-size 2046 --top 3
Files:     9
Total:     58.56 KB
```

## Filtering behavior

`--filter` and `--min-size` narrow the entire report, not just the "largest files" list. The file count, the total size, and the extension breakdown all reflect only the files that passed the filters — so the numbers always describe the same set of files that gets listed.

`--filter` accepts either `.py` or `*.py`; a leading `*` is added when missing.

`--min-size N` keeps files of exactly N bytes and drops anything smaller.

## Output format

Sizes are scaled to the largest unit that keeps the number under 1024, so a report never shows a raw byte count for a multi-gigabyte tree, and never mislabels the unit.

Extensions are left-aligned and sizes right-aligned, which puts the digits in a scannable column when comparing magnitudes.

Files with no extension are grouped under `(none)`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Scan completed and at least one file matched |
| `1` | Path missing, path is a file rather than a directory, or no files matched |

Zero matches exits non-zero on purpose. In a directory scan, an empty result almost always means a wrong path or a typo'd filter rather than a genuinely empty tree, so it's reported as a failure rather than a silent success.

## Notes

Files that can't be read — permission denied, or removed mid-scan — are skipped and counted rather than aborting the run. The number skipped is reported alongside the totals so the figures aren't silently incomplete. This matters on any real filesystem, where a recursive walk will eventually reach something it isn't allowed to open.

Reported sizes are logical file sizes from `stat()`, not disk usage. Actual space consumed differs because of filesystem block allocation, so totals here will not match `du` exactly.

Symlinks are followed by the underlying walk, so a link pointing back into the scanned tree could cause files to be counted more than once.
