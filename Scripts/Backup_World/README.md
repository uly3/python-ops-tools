# backup_world.py

Creates a timestamped `.tar.gz` archive of a Minecraft Bedrock world directory and prunes older archives down to a retention limit. Written to run unattended under a systemd timer.

Uses only the Python standard library — `tarfile` builds the gzipped archive directly, with no shelling out to `tar`.

## Usage

```bash
python3 backup_world.py <source> <destination> [--retention N]
```

| Argument | Default | Description |
|---|---|---|
| `source` | *(required)* | World directory to archive |
| `destination` | *(required)* | Directory to write archives into |
| `--retention N` | `7` | Number of most recent archives to keep |

## Examples

Back up a world, keeping the default seven archives:

```bash
$ python3 backup_world.py /opt/minecraft/bedrock/worlds /opt/minecraft/backups
Created: Minecraft_Bedrock_Server_Backup_2026-09-17_005541.tar.gz
Size: 421.00 B
Kept: 1 backups | Pruned: 0 | Elapsed: 0.0s
```

Once the retention limit is reached, each run prunes the oldest:

```bash
$ python3 backup_world.py /opt/minecraft/bedrock/worlds /opt/minecraft/backups
Created: Minecraft_Bedrock_Server_Backup_2026-09-17_005656.tar.gz
Size: 421.00 B
Pruned: Minecraft_Bedrock_Server_Backup_2026-09-17_005541.tar.gz
Kept: 7 backups | Pruned: 1 | Elapsed: 0.0s
```

Tightening the retention window prunes everything above the new limit in a single run:

```bash
$ python3 backup_world.py /opt/minecraft/bedrock/worlds /opt/minecraft/backups --retention 3
Created: Minecraft_Bedrock_Server_Backup_2026-09-17_005923.tar.gz
Pruned: Minecraft_Bedrock_Server_Backup_2026-09-17_005649.tar.gz
Pruned: Minecraft_Bedrock_Server_Backup_2026-09-17_005651.tar.gz
Pruned: Minecraft_Bedrock_Server_Backup_2026-09-17_005652.tar.gz
Pruned: Minecraft_Bedrock_Server_Backup_2026-09-17_005653.tar.gz
Pruned: Minecraft_Bedrock_Server_Backup_2026-09-17_005654.tar.gz
Kept: 3 backups | Pruned: 5 | Elapsed: 0.0s
```

## Archive naming

Archives are named `Minecraft_Bedrock_Server_Backup_YYYY-MM-DD_HHMMSS.tar.gz`.

The timestamp format is deliberate. Because every field runs largest-to-smallest and is zero-padded to a fixed width, a plain alphabetical sort of the filenames is also a chronological sort. That means retention can work off `sorted()` on names alone, without stat'ing every file for its modification time — and a directory listing reads in chronological order for free.

A format like `09-16-2026_1-44-55pm` has neither property: month sorts before year, and single-digit hours break alignment.

Timestamps are second-resolution, so two runs within the same second would produce the same filename and the second would overwrite the first. Not a concern for a scheduled job, but worth knowing when testing in a loop.

## Archive contents

Paths inside the archive are relative to the world directory's own name:

```
$ tar -tzf Minecraft_Bedrock_Server_Backup_2026-09-17_005541.tar.gz
worlds/
worlds/Bedrock_level/
worlds/Bedrock_level/db/
worlds/Bedrock_level/db/000001.log
worlds/Bedrock_level/level.dat
```

Storing relative paths means the archive can be extracted anywhere. An archive built from absolute paths would only ever unpack back over the original location, which is exactly the wrong behavior when you're restoring to a rebuilt server or inspecting a backup on a different machine.

## Atomic writes

The archive is written to a `.partial` file and renamed to its final name only after the tarball closes cleanly. A rename on the same filesystem is atomic, so a file bearing the real archive name never exists unless the backup completed.

Without this, a crash mid-write — disk full, a world file locked by a running server — leaves behind a truncated `.tar.gz` that looks like a valid backup. It would be counted by the retention logic, survive pruning, and eventually be the archive you reach for during an actual restore.

If the write does fail, the partial file is removed rather than left behind for the next run to trip over.

## Retention

After each successful backup, the destination is re-scanned and archives beyond the retention limit are deleted, oldest first.

Scanning happens *after* the new archive is written so the fresh backup is included in the count — otherwise the directory would grow by one every run.

Pruning removes every archive above the limit, not one per run. Lowering `--retention` from 7 to 3 takes effect in a single execution rather than over four scheduled runs.

When fewer archives exist than the retention limit, nothing is deleted.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Archive created successfully |
| `1` | Source or destination directory missing, or the archive failed to write |

A failed prune is reported but does not fail the run — the backup itself succeeded, which is the part that matters. Exit `1` is reserved for "there is no new backup," which is the condition worth waking up for.

## Notes

Output goes to stdout in a compact form — archive name, size, prune actions, and a one-line summary — so `journalctl -u <unit>` stays readable across months of scheduled runs.

The world is archived live, without stopping the server. A running Bedrock server holds open file handles, so an archive can capture a partially written chunk. For a homelab this is an accepted tradeoff; a stricter setup would stop the service or issue a save-hold before archiving.

Run as the same user that owns the world directory and the backup destination. A backup that works as root but fails as the service account is a permissions bug that will only surface once the timer runs it.
