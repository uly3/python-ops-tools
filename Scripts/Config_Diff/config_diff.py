import json, argparse, sys, re
from pathlib import Path

variable_regex = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$')

SENSITIVE = ('KEY', 'PASSWORD', 'SECRET', 'TOKEN')

def mask(key, value):
    if any(word in key.upper() for word in SENSITIVE):
        return '***'
    return value

def file_obj_to_dict(file):
    dict_to_return = {}

    for line in file:

        #Take '/n' white space per line
        stripped_line = line.strip()
    
        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith('#'):
            continue
    
        match_variable = variable_regex.search(stripped_line)
    
        if match_variable is None:
            print(f'There is malformed code here. Line: {stripped_line}', file=sys.stderr)
            sys.exit(1)

        #Variable of .env file
        key = match_variable.group(1)
        value = match_variable.group(2)

        dict_to_return[key] = value

    return dict_to_return

start_parse = argparse.ArgumentParser(description="Compares two .env style config files and reports what is missing, extra, or different between them.")
start_parse.add_argument('file_a', help='Takes in the first .env style config file to compare')
start_parse.add_argument('file_b', help='Takes in the second .env style config gile to compare')
start_parse.add_argument('--ignore-values', action='store_true', help='Ignores the Key:Value diff output')
start_parse.add_argument('--json', help='Writes the report as JSON')
parser = start_parse.parse_args()

fileA = Path(parser.file_a).resolve()
fileB = Path(parser.file_b).resolve()

fileA_dict = None
fileB_dict = None

if not fileA.exists() and not fileB.exists():
    print(f"ERROR: Both files do not exist... {fileA.name}, {fileB.name}", file=sys.stderr)
    sys.exit(1)

if not fileA.is_file() and not fileB.is_file():
    print(f"ERROR: Both paths are not files... {fileA}, {fileB}", file=sys.stderr)
    sys.exit(1)

if not fileA.exists():
    print(f"ERROR: The FIRST file does not exist... {fileA.name}", file=sys.stderr)
    sys.exit(1)

if not fileA.is_file():
    print(f"ERROR: The FIRST path is not a file... {fileA}", file=sys.stderr)
    sys.exit(1)

if not fileB.exists():
    print(f"ERROR: The SECOND file does not exist... {fileB.name}", file=sys.stderr)
    sys.exit(1)

if not fileB.is_file():
    print(f"ERROR: The Second path is not a file... {fileB}", file=sys.stderr)
    sys.exit(1)

with open(fileA, 'r', encoding='utf-8') as fileA_obj:
    fileA_dict = file_obj_to_dict(fileA_obj)

with open(fileB, 'r', encoding='utf-8') as fileB_obj:
    fileB_dict = file_obj_to_dict(fileB_obj)

#Empty CASE
if not fileA_dict and not fileB_dict:
    print(f'ERROR: Both files are empty!!!', file=sys.stderr)
    sys.exit(1)
elif not fileA_dict and fileB_dict:
    print(f'ERROR: {fileA.name} is empty but {fileB.name} is not!!!', file=sys.stderr)
    sys.exit(1)
elif fileA_dict and not fileB_dict:
    print(f'ERROR: {fileB.name} is empty but {fileA.name} is not!!!', file=sys.stderr)
    sys.exit(1)

keys_ListA = sorted(fileA_dict.keys())
keys_ListB = sorted(fileB_dict.keys())

#First Category:
diff_keys_A = set(keys_ListA) - set(keys_ListB)
#Second Category:
diff_keys_B = set(keys_ListB) - set(keys_ListA)
#Third Category:
different_values = [(key, value) for key, value in fileB_dict.items() if key in fileA_dict and fileA_dict[key] != value]
#Fourth Category:
same_keys = set(keys_ListA) & set(keys_ListB)
matching_keys = sorted(k for k in same_keys if fileA_dict[k] == fileB_dict[k])
count_of_matching = len(matching_keys)

#Loop/Print the categories  
has_differences = bool(diff_keys_A or diff_keys_B)

if not parser.ignore_values and different_values:
    has_differences = True

print(f'Keys in {fileA.name} but not in {fileB.name}...')
for key in sorted(diff_keys_A):
    print(f'KEY: {key}')

print(f'---'*20)

print(f'Keys in {fileB.name} but not in {fileA.name}...')
for key in sorted(diff_keys_B):
    print(f'KEY: {key}')

print(f'---'*20)

if not parser.ignore_values:
    print(f'Keys in both {fileA.name} and {fileB.name} but with different values...')
    for key, value in sorted(different_values):
        print(f'{key}={mask(key, value)}')
    print(f'---'*20)

print(f'Count of keys in both {fileA.name} and {fileB.name} that match... \nCOUNT: {count_of_matching}')

if parser.json:
    json_data = {
        "file_a": str(fileA),
        "file_b": str(fileB),
        "only_in_a": sorted(diff_keys_A),
        "only_in_b": sorted(diff_keys_B),
        "different_values": [{"key": k, "value_b": mask(k, v)} for k, v in sorted(different_values)],
        "matching_count": count_of_matching,
    }

    with open(parser.json, 'w', encoding='utf-8') as json_file_obj:
        json.dump(json_data, json_file_obj, indent=2)

sys.exit(1 if has_differences else 0)
