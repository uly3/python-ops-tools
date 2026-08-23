# bulk_rename.py

Batch-renames files in a directory using substring replacement, a filename prefix, or both. Detects naming collisions before touching anything and skips them rather than overwriting.

**Dry run by default.** Renames only happen when `--apply` is passed.

## Usage

```bash
python3 bulk_rename.py <directory> [--pattern STR --replace STR] [--prefix STR] [--ext EXT] [--apply]
```

| Argument | Default | Description |
|---|---|---|
| `directory` | *(required)* | Directory containing the files (non-recursive) |
| `--pattern STR` | none | Substring to find in filenames; requires `--replace` |
| `--replace STR` | none | What to replace `--pattern` with |
| `--prefix STR` | none | String to prepend to each filename |
| `--ext EXT` | none | Only touch files with this extension, e.g. `.log` |
| `--apply` | off | Actually rename. Without it, nothing is changed. |

At least one rename operation (`--pattern` + `--replace`, or `--prefix`) is required.

## Examples

Preview a substring replacement:

```bash
$ python3 bulk_rename.py photos --pattern "IMG_" --replace "vacation_"
Would rename: IMG_athena.txt -> vacation_athena.txt
Would rename: IMG_siren.txt -> vacation_siren.txt
SKIPPED: IMG_terry.txt -> vacation_terry.txt (already exists on disk)
----------------------------------------
Would rename:         2
Skipped (collisions): 1
Unchanged:            5

Dry run — nothing was changed. Re-run with --apply to execute.
```

Execute it:

```bash
$ python3 bulk_rename.py photos --pattern "IMG_" --replace "vacation_" --apply
Renamed: IMG_athena.txt -> vacation_athena.txt
Renamed: IMG_siren.txt -> vacation_siren.txt
SKIPPED: IMG_terry.txt -> vacation_terry.txt (already exists on disk)
----------------------------------------
Renamed:              2
Skipped (collisions): 1
```

Prefix only files of one type:

```bash
$ python3 bulk_rename.py logs --prefix "archive_" --ext .log --apply
Renamed: app.log -> archive_app.log
Renamed: server.log -> archive_server.log
```

Change extensions — replacement operates on the whole filename, so the suffix can be rewritten like any other substring:

```bash
$ python3 bulk_rename.py drafts --pattern ".txt" --replace ".bak" --apply
Renamed: notes.txt -> notes.bak
Renamed: outline.txt -> outline.bak
```

Operations compose — `--pattern`/`--replace` runs first, then `--prefix` is prepended to the result.

## Dry run

Without `--apply`, the tool builds the complete rename plan, checks it for collisions, and prints it — but changes nothing on disk. The safe path is the default; the destructive path is opt-in.

The plan is computed in full **before** any rename executes. This matters: renaming files one at a time as you iterate changes what's on disk mid-run, so later collision checks would see a different filesystem than the dry run did. Planning first means the dry run shows exactly what `--apply` will do.

## Collision handling

A rename is skipped, never forced, when the target name is taken. Two cases are detected:

| Case | Example |
|---|---|
| **Already on disk** | `IMG_terry.txt` → `vacation_terry.txt`, but that file already exists |
| **Within the batch** | `report_draft_draft.txt` and `report_final_draft.txt` both map to `report_final_final.txt` |

The second case is the subtle one — neither target exists on disk when the run starts, so a disk-only check would approve both and the second rename would silently destroy the first.

This matters because `Path.rename()` **overwrites without warning** on Unix. An undetected collision is permanent data loss, so collisions are treated as a finding: they are reported to stderr and the tool exits non-zero.

Files are processed in sorted order, so when two files compete for the same name, the same one wins on every run and every machine.

## Behavior notes

**Replacement includes the extension.** The pattern is matched against the entire filename, suffix included, so `--pattern ".txt" --replace ".bak"` rewrites extensions. This is intentional — it makes changing a file type a normal use of the tool rather than a special case. Scope the operation with `--ext` when only part of a directory should be affected.

**Every occurrence is replaced.** `report_draft_draft.txt` with `draft`→`final` becomes `report_final_final.txt`, not `report_final_draft.txt`.

**`--prefix` is idempotent.** Files whose names already begin with the prefix are left alone rather than gaining a second copy of it, so repeated runs converge instead of producing `archive_archive_app.log`. This makes the tool safe to invoke from cron or any retry loop. Files skipped for this reason appear in the `Unchanged` count.

When `--prefix` is combined with `--pattern`/`--replace`, the idempotency check happens after the replacement, so an already-prefixed file can still have its body renamed:

```bash
$ python3 bulk_rename.py photos --pattern "IMG_" --replace "vacation_" --prefix "archive_" --apply
Renamed: archive_IMG_photo.txt -> archive_vacation_photo.txt
```

**Non-recursive by design.** Subdirectories are untouched — a recursive bulk rename has a far larger blast radius than the flags suggest.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All planned renames succeeded, or dry run completed with no collisions, or no files matched |
| `1` | Collisions were skipped, a rename failed, invalid arguments, or the path is missing / not a directory |

Collisions exit non-zero even in dry-run mode, so a scripted caller can gate on a clean plan:

```bash
python3 bulk_rename.py logs --prefix "archive_" && \
python3 bulk_rename.py logs --prefix "archive_" --apply
```

## Notes

Individual rename failures — permission denied, file removed mid-run — are caught and reported without aborting the remaining renames. The failure count appears in the summary so partial results are never silently presented as complete.
