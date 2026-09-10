# cleanup_old.py

Finds files older than a given age and removes them. Built for log retention, backup rotation, and clearing out scratch directories on a schedule.

**Dry run by default**, and deletions go to the system trash unless explicitly told otherwise. Both safety layers must be turned off deliberately.

## Usage

```bash
python3 cleanup_old.py <directory> [--days N] [--ext EXT] [--apply] [--permanent]
```

| Argument | Default | Description |
|---|---|---|
| `directory` | *(required)* | Directory to scan (non-recursive) |
| `--days N` | `30` | Delete files older than this many days |
| `--ext EXT` | none | Only consider files with this extension, e.g. `.log` |
| `--apply` | off | Actually delete. Without it, nothing is removed. |
| `--permanent` | off | With `--apply`, delete permanently instead of moving to trash |

## Examples

Preview what would be removed:

```bash
$ python3 cleanup_old.py ~/logs
DRY RUN — showing files older than 30 days

  ancient.txt  |  100 days  |  0.00 B
  hundred_days.log  |  100 days  |  0.00 B
  forty_days.log  |  40 days  |  0.00 B
  old_backup.zip  |  40 days  |  0.00 B
  thirty_days.log  |  30 days  |  0.00 B

Would delete: 5 files
Would reclaim: 0.00 B

Dry run — nothing was deleted. Re-run with --apply to execute.
Skipped (newer): 2 files
```

Move them to the trash:

```bash
$ python3 cleanup_old.py ~/logs --apply
MOVING TO TRASH files older than 30 days

  ancient.txt  |  100 days  |  0.00 B
  ...

Deleted: 5 files
Space reclaimed: 0.00 B
Skipped (newer): 2 files
```

Restrict to one file type and a longer retention window:

```bash
$ python3 cleanup_old.py ~/logs --days 90 --ext .log --apply
```

Permanent deletion, for cases where trash isn't available or wanted:

```bash
$ python3 cleanup_old.py /var/tmp/scratch --days 7 --apply --permanent
```

## Two layers of safety

Deleting files is not reversible in the way a rename or a copy is, so the destructive paths are gated twice:

| Flags | Behavior |
|---|---|
| *(none)* | Dry run — lists candidates, deletes nothing |
| `--permanent` alone | **Still a dry run.** `--permanent` selects *how* to delete, not *whether* to |
| `--apply` | Moves matching files to the system trash — recoverable |
| `--apply --permanent` | Unlinks the files — unrecoverable |

`--permanent` on its own is deliberately inert. A flag that becomes destructive only in combination with another means a mistyped or half-remembered command falls back to the harmless behavior rather than the irreversible one.

The dry run lists every candidate by name, age, and size — not just a count. A preview that only says "5 files" gives you no way to notice it's about to delete the wrong five.

## Age calculation

File age comes from the modification time (`st_mtime`), converted to a timezone-aware UTC datetime and compared against the current time. Files are selected when the elapsed time is **strictly greater** than the threshold, so a file exactly at the boundary is kept.

Reported ages are whole days, truncated — a file 30 days and 20 hours old displays as `30 days`.

Modification time is the right basis for retention: it reflects when the file's contents last changed. Access time (`st_atime`) is unreliable because merely reading a file updates it, and `st_ctime` means metadata-change time on Unix but creation time on Windows, so anything built on it behaves differently across platforms.

## Output ordering

Candidates are listed oldest first, with ties broken alphabetically by filename. Identical input produces identical output on every run, so two cleanup reports can be diffed meaningfully.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Ran successfully — including when files were found and deleted, and when nothing matched |
| `1` | Directory missing or not a directory, or one or more deletions failed |

Finding old files is normal operation for a retention job, not an anomaly, so it does not affect the exit status. A scheduled cleanup that exited non-zero every time it did its job would train whoever reads the alerts to ignore them.

Exit `1` is reserved for genuine operational failure — a file that could not be removed because of permissions, a lock, or a vanished path. That is the condition a cron wrapper or CI step actually needs to hear about.

## Notes

A failed deletion is reported and counted without aborting the run, so one locked file does not prevent the rest of the cleanup from completing. The failure count appears in the summary, so a partial run is never presented as a complete one.

Non-recursive by design. Subdirectories are skipped entirely, and directories are never candidates for deletion — only regular files. A recursive delete has a far larger blast radius than the flags suggest, and a directory passed to a trash operation would take its entire contents with it.

Requires the `send2trash` package for the default (recoverable) deletion path:

```bash
pip install send2trash
```
