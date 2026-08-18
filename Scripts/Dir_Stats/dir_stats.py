import argparse, sys
from pathlib import Path

#Convert a byte into a human-readable string.
def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.2f} {unit}'
        size /= 1024
    return f'{size:.2f} TB'

start_parse = argparse.ArgumentParser(description="Walks a directory tree and reports what's in it: file count, total size, breakdown by extension, and the largest files.")
start_parse.add_argument('directory', help='Directory to investigate')
start_parse.add_argument('--filter', help='Filter to one extension, e.g .py')
start_parse.add_argument('--verbose', action='store_true', help='Also list every file found')
start_parse.add_argument('--top', type=int, default=5, help='How many largest files to show')
start_parse.add_argument('--min-size', type=int, default=0, help='Ignore files under N bytes')
parser = start_parse.parse_args()

directory_to_check = Path(parser.directory).resolve()

if not directory_to_check.exists():
    print(f'ERROR: Path does not exist --> {directory_to_check}', file=sys.stderr)
    sys.exit(1)

if not directory_to_check.is_dir():
    print(f'ERROR: Path is a file, not a directory --> {directory_to_check}', file=sys.stderr)
    sys.exit(1)

pattern = '*'
if parser.filter:
    pattern = parser.filter if parser.filter.startswith('*') else '*' + parser.filter

files = []
file_extensions = {}
total_bytes = 0
skipped = 0

try:
    for file in directory_to_check.rglob(pattern):
        try:
            if not file.is_file():
                continue
            size = file.stat().st_size
        except (PermissionError, OSError):
            skipped += 1
            continue

        if size < parser.min_size:
            continue

        files.append((file, size))
        total_bytes += size
        ext = file.suffix if file.suffix else '(none)'
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
except PermissionError as e:
    print(f'ERROR: Cannot walk directory tree --> {e}', file=sys.stderr)
    sys.exit(1)

if not files:
    print(f'No files matched in {directory_to_check}', file=sys.stderr)
    sys.exit(1)

files.sort(key=lambda pair: pair[1], reverse=True)

print(f'Directory: {directory_to_check}')
print(f'Files:     {len(files)}')
print(f'Total:     {human_size(total_bytes)}')
if skipped:
    print(f'Skipped:   {skipped} unreadable')

print('\nBy extension:')
for ext, count in sorted(file_extensions.items(), key=lambda pair: pair[1], reverse=True):
    print(f'  {ext:<10} {count}')

print(f'\nTop {parser.top} largest:')
for path, size in files[:parser.top]:
    print(f'. {human_size(size):>10}  {path}')

if parser.verbose:
    print(f'\nAll {len(files)} files:')
    for path, size in files:
        print(f'  {human_size(size):>10}  {path}')

sys.exit(0)
