import json, sys, argparse, base64
from pathlib import Path
from datetime import datetime, timedelta, timezone

def b64url_decode(segment):
    segment += '=' * (-len(segment) % 4)    # JWTs strip the '=' padding; Python needs it back
    return base64.urlsafe_b64decode(segment)

start_parse = argparse.ArgumentParser(description="Reads a token from a JSON file, shows what's inside, and tells you whether it has expired.")

start_parse.add_argument("file", type=str, help="A JSON file holding tokens")
start_parse.add_argument("--key", type=str, default="Access_Token", help="Defaults to Access_Token")

parser = start_parse.parse_args()

file_path = Path(parser.file).resolve()
tokens_data = None
key_string = parser.key

#Check if file exists
if not file_path.exists():
    print(f"File does not exist... {file_path}", file=sys.stderr)
    sys.exit(1)
#Check if it's a file
if not file_path.is_file():
    print(f"{file_path} is not a file!", file=sys.stderr)
    sys.exit(1)
#Turn file as working python object + If not Valid JSON
try:
    with open(file_path, 'r', encoding='utf-8') as json_file_obj:
        tokens_data = json.load(json_file_obj)
        print("JSON file loaded successfully...")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e.msg}", file=sys.stderr)
    sys.exit(1)

#Check if Token is in file
if not key_string in tokens_data:
    print(f"{key_string} KEY not found!", file=sys.stderr)
    sys.exit(1)

#Check Valid JWT Token by 3 periods.
token = tokens_data.get(key_string, "N/A")
jwt_parts = token.split(".")

if len(jwt_parts) != 3:
    print(f"ERROR: {key_string} is not a JWT (expected 3 parts, found {len(jwt_parts)})", file=sys.stderr)
    sys.exit(1)

try:
    header = json.loads(b64url_decode(jwt_parts[0]))
    payload = json.loads(b64url_decode(jwt_parts[1]))
except ValueError as e:
    print(f"ERROR: {key_string} could not be decoded: {e}", file=sys.stderr)
    sys.exit(1)

print(json.dumps(header, indent=2))
print(json.dumps(payload, indent=2))
print("Signature: NOT verified - decoded only") 

if "exp" in payload:

    current_time = datetime.now(timezone.utc)
    exp_UTC_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    time_left_token = exp_UTC_time - current_time

    print(f"Current Time:   {current_time}")
    print(f"Token EXP Time: {exp_UTC_time}")

    if time_left_token <= timedelta(0):
        print(f"Token EXPIRED {current_time - exp_UTC_time} ago", file=sys.stderr)
        sys.exit(1)

    print(f"Time Left on Token: {time_left_token}")

else:
    print("Token has no expiration...", file=sys.stderr)
    sys.exit(1)

sys.exit(0)
