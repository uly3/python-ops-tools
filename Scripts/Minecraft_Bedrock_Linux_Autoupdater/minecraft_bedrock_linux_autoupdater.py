import subprocess, argparse, requests, re, sys
from pathlib import Path

version_regex = re.compile(r'([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)')

DOWNLOAD_LINKS_URL = "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
LATEST_BEDROCK_SERVER_URL = ''
LATEST_VERSION_NUMBER = ''

try:
    response = requests.get(DOWNLOAD_LINKS_URL, headers=HEADERS, timeout=10)
    links = response.json()['result']['links']

    for obj in links:
        if obj['downloadType'] == 'serverBedrockLinux':
            LATEST_BEDROCK_SERVER_URL = obj['downloadUrl']
            break

    LATEST_VERSION_NUMBER = version_regex.search(LATEST_BEDROCK_SERVER_URL).group(1)
except Exception as e:
    print(f"ERROR: could not reach the download API --> {e}", file=sys.stderr)
    sys.exit(1)

start_parse = argparse.ArgumentParser(description='Minecraft Bedrock Linux Server Autoupdater')
start_parse.add_argument('version', help='Path to the current version of Minecraft Bedrock Linux Server')
start_parse.add_argument('--push-update', action='store_true', help='Update the server to the latest version')
parser = start_parse.parse_args()

VERSION_FILE = Path(parser.version).resolve()

try:
    with open(VERSION_FILE, 'r', encoding='utf-8') as v_file:
        current_version = v_file.readline().strip()
except OSError as e:
    print(f"ERROR: cannot read {VERSION_FILE} --> {e}", file=sys.stderr)
    sys.exit(1)

if not current_version:
    print(f"ERROR: {VERSION_FILE} is empty", file=sys.stderr)
    sys.exit(1)

print(f'Installed: {current_version}')
print(f'Latest:    {LATEST_VERSION_NUMBER}\n')

if current_version == LATEST_VERSION_NUMBER:
    print('UP TO DATE — nothing to do.')
    sys.exit(0)

print('UPDATE AVAILABLE')

if not parser.push_update:
    print('Run again with --push-update to apply it.')
    sys.exit(1)

print(f'\nUpdating {current_version} -> {LATEST_VERSION_NUMBER}\n')

steps = [
    "sudo systemctl stop bedrock",

    "sudo -u minecraft python3 /opt/minecraft/backup_world.py "
    "/opt/minecraft/bedrock/worlds /opt/minecraft/backups",

    "sudo cp /opt/minecraft/bedrock/server.properties /tmp/server.properties.bak",
    "sudo cp /opt/minecraft/bedrock/permissions.json /tmp/ 2>/dev/null || true",
    "sudo cp /opt/minecraft/bedrock/allowlist.json  /tmp/ 2>/dev/null || true",

    # everything the minecraft user does, chained into one shell
    f"sudo -u minecraft bash -c '"
    f"rm -rf /tmp/bds-new /tmp/bds-new.zip && "
    f"cd /tmp && "
    f"wget -q --user-agent=\"Mozilla/5.0\" \"{LATEST_BEDROCK_SERVER_URL}\" -O bds-new.zip && "
    f"unzip -q bds-new.zip -d /tmp/bds-new && "
    f"cd /tmp/bds-new && "
    f"rm -rf worlds server.properties permissions.json allowlist.json && "
    f"cp -r /tmp/bds-new/* /opt/minecraft/bedrock/ && "
    f"chmod +x /opt/minecraft/bedrock/bedrock_server'",

    "sudo systemctl start bedrock",
]

for command in steps:
    print(f"$ {command}")
    subprocess.run(command, shell=True, check=True)

verify = subprocess.run(
    "sudo journalctl -u bedrock -n 50 --no-pager | "
    "grep -E 'Version:|Level Name:|Server started'",
    shell=True, capture_output=True, text=True
)

print("\n--- verification ---")
print(verify.stdout)

if LATEST_VERSION_NUMBER not in verify.stdout:
    print("ERROR: server did not report the new version. Check the journal.", file=sys.stderr)
    sys.exit(1)

subprocess.run(
    f"sudo -u minecraft bash -c 'echo {LATEST_VERSION_NUMBER} > {VERSION_FILE}'",
    shell=True, check=True
)

print('Update was a success!')
sys.exit(0)
