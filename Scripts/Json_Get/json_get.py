import argparse, sys, json
from pathlib import Path

start_parse = argparse.ArgumentParser(description="Pulls a single value out of a JSON document by a dot-separated path.")
start_parse.add_argument('path', type=str, help='JSON dot-seperated path')
start_parse.add_argument('file', type=str, help='JSON file to check')
parser = start_parse.parse_args()

path_list = str(parser.path).split('.')
path_file = Path(parser.file).resolve()

if not path_file.exists():
    print(f"The file does not exist! --> {path_file}", file=sys.stderr)
    sys.exit(1)

if not path_file.is_file():
    print(f"Not a file! --> {path_file}", file=sys.stderr)
    sys.exit(1)

current_value = None

try:
    with open(path_file, 'r', encoding='utf-8') as json_file_obj:
        data = json.load(json_file_obj)
        current_value = data
except json.JSONDecodeError as e:
        print(f"Error: {path_file.name} is not valid JSON ({e})", file=sys.stderr)
        sys.exit(1)
try:
    for key in path_list:
        if isinstance(current_value, dict):
            current_value = current_value[key]

        elif isinstance(current_value, list) and key.isdigit():
            current_value = current_value[int(key)]
        else:
            raise KeyError

    if isinstance(current_value, str):
        print(current_value)
    else:
        print(json.dumps(current_value, indent=2))
    sys.exit(0)

except (KeyError, IndexError, TypeError):
    print(f"Error: path '{parser.path}' failed at '{key}'", file=sys.stderr)
    sys.exit(1)
