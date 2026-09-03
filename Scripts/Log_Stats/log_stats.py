import argparse, sys, re, json
from pathlib import Path

def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.2f} {unit}'
        size /= 1024
    return f'{size:.2f} TB'

#compound key — negative count sorts descending, 
#name sorts ascending, so ties always break the same way on every run
#Lambda Function Version: lambda item: (-item[1], item[0])
def by_count_then_name(item):
    return (-item[1], item[0])

log_line_regex = re.compile(
    r'^(\d+\.\d+\.\d+\.\d+)'      # 1 IP
    r'\s+\S+\s+\S+\s+'            #   the two "-" fields
    r'\[([^\]]+)\]\s+'            # 2 timestamp (inside brackets)
    r'"([A-Z]+)\s+'               # 3 method
    r'(\S+)\s+'                   # 4 path
    r'HTTP/\d\.\d"\s+'            #   protocol
    r'(\d{3})\s+'                 # 5 status
    r'(\d+)'                      # 6 bytes
)

start_parse = argparse.ArgumentParser(description='Parses a web-server-style access log and reports traffic statistics.')
start_parse.add_argument('logfile', help='Access log file to parse')
start_parse.add_argument('--top', type=int, default=5, help='How many top IPs/paths to show')
start_parse.add_argument('--status', type=int, help='Only count requests with this status code')
start_parse.add_argument('--json', help='Write the report to this JSON file')
parser = start_parse.parse_args()

log_file = Path(parser.logfile).resolve()

if not log_file.exists():
    print(f'ERROR: The file {log_file} does not exist!', file=sys.stderr)
    sys.exit(1)

if not log_file.is_file():
    print(f'This is not a file! {log_file}', file=sys.stderr)
    sys.exit(1)


lines_that_dont_parse = 0
total_parsed = 0
requests_per_status_code = {}
requests_per_ip_counts = {}
requests_per_path_counts = {}
total_bytes = 0

with open(log_file, 'r', encoding='utf-8') as log_obj:
    for line in log_obj:
        match = log_line_regex.search(line)

        #Check for bad lines
        if match is None:
            lines_that_dont_parse += 1
            continue

        ip = match.group(1)         
        path = match.group(4)
        status_code = int(match.group(5))
        response_size = int(match.group(6))

        #Filter EVERY request per action
        if parser.status is not None and status_code != parser.status:
            continue

        total_parsed += 1
        requests_per_status_code[status_code] = requests_per_status_code.get(status_code, 0) + 1
        requests_per_ip_counts[ip] = requests_per_ip_counts.get(ip, 0) + 1
        requests_per_path_counts[path] = requests_per_path_counts.get(path, 0) + 1
        total_bytes += response_size

if total_parsed == 0:
    if parser.status is not None:
        print(f'No requests matched status code {parser.status}', file=sys.stderr)
    else:
        print('No parseable log lines found', file=sys.stderr)
    sys.exit(1)
        
if parser.status is not None:
    print(f'Filtered to status {parser.status}')

print(f'\nRequests: {total_parsed}')

print('\nRequests per status code...')
for code, count in sorted(requests_per_status_code.items()):
    print(f'  {code}: {count}')

print(f'\nTop {parser.top} IPs...')
for ip, count in sorted(requests_per_ip_counts.items(), key=by_count_then_name)[:parser.top]:
    print(f'  {ip}: {count}')

print(f'\nTop {parser.top} paths...')
for path, count in sorted(requests_per_path_counts.items(), key=by_count_then_name)[:parser.top]:
    print(f'  {path}: {count}')

print(f'\nTotal bytes transferred: {human_size(total_bytes)}')
print(f'Unparseable lines (whole file): {lines_that_dont_parse}')

if parser.json:
    json_data = {
        "status_codes": {str(k): v for k, v in sorted(requests_per_status_code.items())},
        "top_ips": dict(sorted(requests_per_ip_counts.items(), key=by_count_then_name)[:parser.top]),
        "top_paths": dict(sorted(requests_per_path_counts.items(), key=by_count_then_name)[:parser.top]),
        "total_requests": total_parsed,
        "total_bytes": total_bytes,
        "total_bytes_human": human_size(total_bytes),
        "unparseable_lines": lines_that_dont_parse,
    }
    with open(parser.json, 'w', encoding='utf-8') as json_file_obj:
        json.dump(json_data, json_file_obj, indent=2)

sys.exit(0)
