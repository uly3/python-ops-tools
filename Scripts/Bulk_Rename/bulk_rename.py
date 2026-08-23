from pathlib import Path
import sys, argparse

start_parse = argparse.ArgumentParser(description="Batch-renames files in a directory.")

start_parse.add_argument('directory', help='Directory containing files to rename')
start_parse.add_argument('--pattern', help='Substring to find in filenames')
start_parse.add_argument('--replace', help='Replacement for --pattern')
start_parse.add_argument('--prefix', help='String to prepend to filenames')
start_parse.add_argument('--ext', help='Only touch files with this extension, e.g. .log')
start_parse.add_argument('--apply', action='store_true', help='Actually rename. Without it, dry run only.')

parser = start_parse.parse_args()

dry_run = not parser.apply

directory_to_check = Path(parser.directory).resolve()

glob_pattern = '*'
if parser.ext:
    ext = parser.ext if parser.ext.startswith('.') else '.' + parser.ext
    glob_pattern = '*' + ext

has_replace = bool(parser.pattern and parser.replace)
has_prefix = bool(parser.prefix)

collisions = []
file_check = set()
planned_file_renames = []

failed = 0
renamed = 0
unchanged_files = 0

if not directory_to_check.exists():
    print(f'ERROR: The directory does not exist: {directory_to_check}', file=sys.stderr)
    sys.exit(1)

if not directory_to_check.is_dir():
    print(f'ERROR: This is not a directory: {directory_to_check}', file=sys.stderr)
    sys.exit(1)

if parser.pattern and not parser.replace:
    print('ERROR: --pattern requires --replace.', file=sys.stderr)
    sys.exit(1)

if not has_replace and not has_prefix:
    print('ERROR: Provide --pattern with --replace, and/or --prefix.', file=sys.stderr)
    sys.exit(1)

for file in sorted(directory_to_check.glob(glob_pattern)):
    if not file.is_file():
        continue

    new_file = file.name

    if has_replace:
        new_file = new_file.replace(parser.pattern, parser.replace)

    if has_prefix and not new_file.startswith(parser.prefix):
        new_file = parser.prefix + new_file

    if new_file == file.name:
        unchanged_files += 1
        continue

    new_file_path = file.parent / new_file

    if new_file_path.exists():
        collisions.append((file.name, new_file, 'already exists on disk'))
        continue

    if new_file in file_check:
        collisions.append((file.name, new_file, 'another file in this batch renames to it'))
        continue

    file_check.add(new_file)
    planned_file_renames.append((file, new_file_path))

if not planned_file_renames and not collisions:
    print(f'No files matched the rename criteria in {directory_to_check}', file=sys.stderr)
    sys.exit(0)

for old_file_path, new_file_path in planned_file_renames:
    if dry_run:
        print(f'Would rename: {old_file_path.name} -> {new_file_path.name}')
    else:
        try:
            old_file_path.rename(new_file_path)
            print(f'Renamed: {old_file_path.name} -> {new_file_path.name}')
            renamed += 1
        except OSError as e:
            print(f'ERROR: could not rename {old_file_path}: {e}', file=sys.stderr)
            failed += 1

for old_file_name, new_file_name, reason in collisions:
    print(f'SKIPPED: {old_file_name} -> {new_file_name} ({reason})', file=sys.stderr)

print('-' * 40)

if dry_run:
    print(f'Would rename:         {len(planned_file_renames)}')
else:
    print(f'Renamed:              {renamed}')
print(f'Skipped (collisions): {len(collisions)}')
if unchanged_files:
    print(f'Unchanged: {unchanged_files}')
if failed:
    print(f'Failed:               {failed}')
if dry_run and planned_file_renames:
    print('\nDry run — nothing was changed. Re-run with --apply to execute.')

sys.exit(1 if (collisions or failed) else 0)
