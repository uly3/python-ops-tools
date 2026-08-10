import sys, argparse, subprocess, re

start_tool = argparse.ArgumentParser(description='Outputs the disk usage of a path')
start_tool.add_argument('--threshold', type=int, default=80, help='Takes in a number to display how much to check')
start_tool.add_argument('--verbose', action='store_true', help='Turns on logging')
parser = start_tool.parse_args()

command_to_excute = ['df', '-h']

filesystem_regex = re.compile(r'^\S+(?:\s\S+)*?(?=\s{2,})')
pull_capacity_regex = re.compile(r'[0-9]+%')

try:
    result = subprocess.run(command_to_excute, capture_output=True, text=True, check=True, timeout=10)
    output = result.stdout.split('\n')
    breached = False

    #Prevents last element from just being an empty string
    for line in output[1:len(output)-1]:
        fs_match = filesystem_regex.search(line)
        cap_match = pull_capacity_regex.search(line)

        if fs_match is None or cap_match is None:
            continue
        filesystem = fs_match.group()
        capacity = int(cap_match.group().strip('%'))

        if capacity >= parser.threshold:
            print(f'The filesystem - {filesystem} is at or above the threshold {parser.threshold}')
            breached = True
        if parser.verbose:
            print(f'Filesystem: {filesystem} ---> Capacity: {capacity}')

    sys.exit(1 if breached else 0)
            
except subprocess.CalledProcessError as e:
    print(f'ERROR: {e.stderr}', file=sys.stderr)
    sys.exit(e.returncode)
except FileNotFoundError:
    print('Command not found', file=sys.stderr)
    sys.exit(1)
