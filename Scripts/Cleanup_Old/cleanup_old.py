import argparse, sys, os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from send2trash import send2trash

def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.2f} {unit}'
        size /= 1024
    return f'{size:.2f} TB'

start_parse = argparse.ArgumentParser(description='Finds files older than N days and removes them.')

start_parse.add_argument('directory', help='Takes in a directory to scan')
start_parse.add_argument('--days', type=int, default=30, help='Delete files older than this many days')
start_parse.add_argument('--ext', help='Filter by file extension (e.g. .log .txt .py)')
start_parse.add_argument('--apply', action='store_true', help='Actually delete. Without it, dry run only.')
start_parse.add_argument('--permanent', action='store_true', help='With --apply, delete permanently instead of moving to trash')

parser = start_parse.parse_args()

dry_run = not parser.apply

directory = Path(parser.directory).resolve()

if not directory.exists():
    print(f'ERROR: This directory does not exist! {directory}', file=sys.stderr)
    sys.exit(1)

if not directory.is_dir():
    print(f'ERROR: This is not a directory! {directory}', file=sys.stderr)
    sys.exit(1)

pattern = '*'
if parser.ext:
    pattern = parser.ext if parser.ext.startswith('*') else '*' + parser.ext

THRESHOLD_DAYS = parser.days
age_threshold = timedelta(days=THRESHOLD_DAYS)
current_time = datetime.now(timezone.utc)

files_marked = []
files_skipped = 0

for file in directory.glob(pattern):
    #Checks if its a file only
    if not file.is_file():
        continue

    stats = file.stat()
    file_UTC_time = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
    time_elapsed = current_time - file_UTC_time

    if time_elapsed > age_threshold:
        files_marked.append((file, file.name, time_elapsed.days, stats.st_size))
    else:
        files_skipped += 1

if not files_marked:
    print(f'Nothing older than {THRESHOLD_DAYS} days in {directory}')
    print(f'({files_skipped} files checked)')
    sys.exit(0)

if dry_run:
    print(f'DRY RUN — showing files older than {THRESHOLD_DAYS} days\n')
else:
    mode = 'PERMANENTLY DELETING' if parser.permanent else 'MOVING TO TRASH'
    print(f'{mode} files older than {THRESHOLD_DAYS} days\n')

space_reclaimed = 0
deleted = 0
failed = 0

for path, name, age, size in sorted(files_marked, key=lambda x: (-x[2], x[1])):
    print(f'  {name}  |  {age} days  |  {human_size(size)}')

    if dry_run:
        space_reclaimed += size
        continue

    try:
        if parser.permanent:
            path.unlink()        
        else:
            send2trash(str(path))
        deleted += 1
        space_reclaimed += size
    except OSError as e:
        print(f'ERROR: Could not delete {name} ---> {e}', file=sys.stderr)
        failed += 1

print()
if dry_run:
    print(f'Would delete: {len(files_marked)} files')
    print(f'Would reclaim: {human_size(space_reclaimed)}')
    print(f'\nDry run — nothing was deleted. Re-run with --apply to execute.')
else:
    print(f'Deleted: {deleted} files')
    print(f'Space reclaimed: {human_size(space_reclaimed)}')
    if failed:
        print(f'Failed: {failed} files')
print(f'Skipped (newer): {files_skipped} files')

sys.exit(1 if failed else 0)
    