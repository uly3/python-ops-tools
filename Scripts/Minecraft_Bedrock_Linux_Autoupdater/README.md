# minecraft_bedrock_linux_autoupdater.py

Checks the official Minecraft download API for the latest Bedrock dedicated server release and, on request, performs the full update: stop, back up, download, extract, preserve configuration, restart, verify.

Safe to run as a bare check on a schedule — it only makes changes when `--push-update` is passed.

## Usage

```bash
python3 minecraft_bedrock_linux_autoupdater.py <version_file> [--push-update]
```

| Argument | Default | Description |
|---|---|---|
| `version_file` | *(required)* | File containing the currently installed version string |
| `--push-update` | off | Perform the update. Without it, only reports. |

The version file holds a single line, e.g. `1.21.44.01`.

## Examples

Check only:

```bash
$ python3 minecraft_bedrock_linux_autoupdater.py /opt/minecraft/version.txt
Installed: 1.21.44.01
Latest:    1.21.44.01

UP TO DATE — nothing to do.
```

When a release is available:

```bash
$ python3 minecraft_bedrock_linux_autoupdater.py /opt/minecraft/version.txt
Installed: 1.21.44.01
Latest:    1.21.51.02

UPDATE AVAILABLE
Run again with --push-update to apply it.
$ echo $?
1
```

Apply it:

```bash
$ sudo python3 minecraft_bedrock_linux_autoupdater.py /opt/minecraft/version.txt --push-update
Updating 1.21.44.01 -> 1.21.51.02

$ sudo systemctl stop bedrock
$ sudo -u minecraft python3 /opt/minecraft/backup_world.py ...
...
--- verification ---
[INFO] Version: 1.21.51.02
[INFO] Server started.
Update was a success!
```

## Version discovery

Queries `net-secondary.web.minecraft-services.net` for the download-links payload, selects the entry whose `downloadType` is `serverBedrockLinux`, and extracts the four-part version number from the download URL with a regular expression.

A browser `User-Agent` header is sent because the endpoint rejects default client agents.

There is no separate "current version" endpoint — the version is only present in the filename of the download URL, which is why it is parsed out rather than read from a field.

## What the update does

1. Stops the `bedrock` service
2. Runs `backup_world.py` to archive the world before anything is touched
3. Copies `server.properties`, `permissions.json`, and `allowlist.json` to `/tmp` as insurance
4. Downloads and extracts the new release to `/tmp/bds-new`
5. **Deletes `worlds/`, `server.properties`, `permissions.json`, and `allowlist.json` from the extracted copy**, so the live ones are never overwritten
6. Copies the remaining new files over the install
7. Restores the executable bit on `bedrock_server`
8. Starts the service and greps the journal for the new version banner

Step 5 is the one that matters. The Bedrock zip ships default configuration and an empty world; copying it over an existing install wholesale would reset the server settings and replace the world. Removing those entries from the *source* before the copy is safer than copying everything and restoring afterwards, because there is no window in which the live files are gone.

The `/tmp` copies in step 3 are never read during a successful run. They exist so the previous configuration is recoverable if something goes wrong mid-update.

## Version file

The version file is only rewritten **after** the journal confirms the running server reports the new version. If verification fails, the file keeps the old value — so the next run still sees an available update rather than silently recording a version that may not be installed.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Already up to date, or the update completed and verified |
| `1` | Update available and not applied, API unreachable, version file missing or empty, or verification failed |

Exit `1` for "update available" is deliberate: it makes the script usable as a monitoring check, and allows chaining.

```bash
python3 minecraft_bedrock_linux_autoupdater.py /opt/minecraft/version.txt || notify-me
```

Because exit `1` covers both "an update is waiting" and "something broke," anything automated on top of it should read the output rather than the code alone.

## Requirements

```bash
pip install requests
```

Also expects `wget` and `unzip` on the host, and `backup_world.py` present at `/opt/minecraft/backup_world.py`.

Needs `sudo` for the service control and file operations, and runs the download and extraction as the `minecraft` user so the resulting files carry the right ownership.

## Known limitations

**No automatic rollback.** If a step fails partway through, the update stops where it is. The world backup from step 2 and the configuration copies in `/tmp` make manual recovery possible, but nothing reverts automatically.

**Verification timing.** `systemctl start` returns when systemd considers the unit active, which can precede the server actually logging its version banner. On a slow start the grep may run too early and report a failure for an update that in fact succeeded — check the journal before assuming the worst.

**The update is not idempotent.** Re-running it after a partial failure repeats the download and extraction from the beginning.
