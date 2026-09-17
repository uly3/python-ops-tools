import sys, argparse, tarfile
from pathlib import Path
from datetime import datetime

def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.2f} {unit}'
        size /= 1024
    return f'{size:.2f} TB'

start_parse = argparse.ArgumentParser(description='Backups a Minecraft Bedrock Server')
start_parse.add_argument('source', help='Source path of the /worlds directory')
start_parse.add_argument('destination', help='Destination path to send tar.gz backup')
start_parse.add_argument('--retention', type=int, default=7, help='Number of most recent backups to keep')
parser = start_parse.parse_args()

worlds_folder = Path(parser.source).resolve()
backups_folder = Path(parser.destination).resolve()

if not worlds_folder.is_dir():
    print(f'ERROR: source directory not found: {worlds_folder}', file=sys.stderr)
    sys.exit(1)
if not backups_folder.is_dir():
    print(f'ERROR: backup directory not found: {backups_folder}', file=sys.stderr)
    sys.exit(1)

start_time = datetime.now()
timestamp = start_time.strftime("%Y-%m-%d_%H%M%S")

archive_name = f"Minecraft_Bedrock_Server_Backup_{timestamp}.tar.gz"
archive_path = backups_folder / archive_name

temp_path = backups_folder / (archive_name + '.partial')

try:
    with tarfile.open(temp_path, 'w:gz') as tar:
        tar.add(worlds_folder, arcname=worlds_folder.name)

    temp_path.rename(archive_path)
except (OSError, tarfile.TarError) as e:
    print(f'ERROR: backup failed while writing {archive_name}: {e}', file=sys.stderr)
    if temp_path.exists():
        temp_path.unlink()
    sys.exit(1)

size = archive_path.stat().st_size
print(f"Created: {archive_name}")
print(f"Size: {human_size(size)}")

list_of_backups = []

for file in backups_folder.glob("Minecraft_Bedrock_Server_Backup_*.tar.gz"):
    if not file.is_file():
        continue
    list_of_backups.append(file)

#ASCENDING - OLDEST FIRST, newest last
list_of_backups = sorted(list_of_backups)

to_delete = list_of_backups[:-parser.retention] if parser.retention > 0 else []

pruned = 0

for old_backup in to_delete:
    try:
        old_backup.unlink()
        print(f"Pruned: {old_backup.name}")
        pruned += 1
    except OSError as e:
        print(f'ERROR: could not prune {old_backup.name}: {e}', file=sys.stderr)

elapsed = (datetime.now() - start_time).total_seconds()
print(f"Kept: {len(list_of_backups) - pruned} backups | Pruned: {pruned} | Elapsed: {elapsed:.1f}s")

sys.exit(0)
