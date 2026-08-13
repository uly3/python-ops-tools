import re, argparse, sys
from pathlib import Path

create_parser = argparse.ArgumentParser(description="Validates a config/env file before it gets deployed")
create_parser.add_argument('envfile', help='Acceps a config/env file')
create_parser.add_argument('--required', nargs='*', help='Reports any missing required keys')
create_parser.add_argument('--verbose', action='store_true', help='Prints any valid key it finds')
parser = create_parser.parse_args()

path_to_config_env_file = Path(parser.envfile)

variable_regex = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$')

variable_value_dict = {}
code_line_number = 0
number_of_malform_variables = 0
missing_required_keys = 0

#Check if the file actually exists on the computer
if not path_to_config_env_file.exists():
    print(f"ERROR: The file {path_to_config_env_file} does not exist.", file=sys.stderr)
    sys.exit(1)

#Check if the file is empty
if path_to_config_env_file.stat().st_size == 0:
    print(f'ERROR: The file {path_to_config_env_file} is empty.', file=sys.stderr)
    sys.exit(1)

with open(path_to_config_env_file, 'r', encoding='utf-8') as env_config_obj:
    for line in env_config_obj:
        code_line_number += 1
        #Take '/n' white space per line
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue

        match = variable_regex.search(stripped)

        if match is None:
            print(f'Line Number {code_line_number}: There is malformed code here. Line: ', end='')
            print(stripped)
            number_of_malform_variables += 1
            continue

        variable = match.group(1)
        value = match.group(2)

        SENSITIVE = ('KEY', 'PASSWORD', 'SECRET', 'TOKEN')

        if parser.verbose:
            if any(word in variable.upper() for word in SENSITIVE):
                print(f'{variable}=***')        
            else:
                print(f'{variable}={value}')

        variable_value_dict[variable] = value

    if not variable_value_dict:
        print('ERROR: No valid entries found in file', file=sys.stderr)
        sys.exit(1)

if parser.required:
    if len(parser.required) >= 1:
        for key in parser.required:
            if key not in variable_value_dict:
                print(f'REQUIRED KEY IS MISSING: {key}')
                missing_required_keys += 1
            else:
                continue

if number_of_malform_variables == 0 and missing_required_keys == 0:
    print(f'\nSUCCESS!!! CONFIG FILE IS VALID & NOT MISSING REQUIRED KEYS!!!')
    sys.exit(0)
else:
    print(f'\nERROR!!! CONFIG FILE IS NOT VALID & MISSING REQUIRED KEYS!!!', file=sys.stderr)
    sys.exit(1)
