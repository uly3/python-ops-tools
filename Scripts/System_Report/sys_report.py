from pathlib import Path
import argparse, json, time, datetime, subprocess, sys

args = argparse.ArgumentParser(description='Shell out to a command, capture its output, parse it, report on it.')
args.add_argument('command', help='Takes in a command')
args.add_argument('--args', nargs='*', help='Takes in the commands arguments')
args.add_argument('--timeout', type=int, default=30, help='Time before application timesout')
args.add_argument('--json', help='Output the information as a JSON file')
parser = args.parse_args()

list_commands = [parser.command]

if parser.args:
    list_commands.extend(parser.args)

try:
    start_time = time.time()
    result = subprocess.run(list_commands, capture_output=True, text=True, check=True, timeout=parser.timeout)
    end_time = time.time()
    if len(result.stdout) == 0:
        print('The command produced no output...')
        sys.exit(0)

    command_used = ' '.join(list_commands)
    return_code = result.returncode
    duration = round(end_time - start_time, 2)
    lines = result.stdout.rstrip('\n').split('\n')
    line_count = len(lines)
    line_output = lines[:5]
    
    print(f'Command Used: {command_used}\nReturn Code: {return_code}\nDuration: {duration}\nLine Count: {line_count}\nOutput:\n', '\n'.join(line_output))
  
    if parser.json:
        json_data = {
            "Command_Used": command_used,
            "Return_Code": return_code,
            "Duration": duration,
            "Line_Count": line_count,
            "Output": line_output
        }

        with open(parser.json, 'w') as file_obj:
            json.dump(json_data, file_obj, indent=2)

    print('Timestamp: ', datetime.datetime.now().strftime('%Y/%m/%d %I:%M:%S %p'))
    sys.exit(0)
except subprocess.TimeoutExpired as e:
    print(f'ERROR: command timed out after {parser.timeout} seconds', file=sys.stderr)
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f'ERROR: {e.stderr}', file=sys.stderr)
    sys.exit(e.returncode)
except FileNotFoundError:
    print('Command not found', file=sys.stderr)
    sys.exit(1)
