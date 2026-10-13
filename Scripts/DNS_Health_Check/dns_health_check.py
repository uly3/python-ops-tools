import argparse, sys, re, subprocess, ipaddress

RCODE_STATUS_REGEX = re.compile(r"status:\s+(\w+)")
IP_REGEX = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

start_parse = argparse.ArgumentParser(description='Checks the DNS Health of the DNS Server')

start_parse.add_argument('--dns-server', default='10.0.1.100', help='IP of your DNS/Pi-Hole Server')
start_parse.add_argument('--unbound-port', type=int, default=5335, help='Unbound Port Number')
start_parse.add_argument('--timeout', type=int, default=10, help='Timeout in seconds')

parser = start_parse.parse_args()

def helper_dig(site, server, port=None):
    """Returns (rcode, ip, timed_out). rcode is None if unreadable."""

    cmd = ['dig', site, f'@{server}', f'+time={parser.timeout}', '+tries=1']
    if port:
        cmd += ['-p', str(port)] 

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=parser.timeout + 3)
    except subprocess.TimeoutExpired:
        return (None, None, True)           

    if result.returncode == 9:
        return (None, None, True)

    if len(result.stdout) == 0:
        return (None, None, True)

    rcode_match = RCODE_STATUS_REGEX.search(result.stdout)
    rcode = rcode_match.group(1) if rcode_match else None

    ip = None
    in_answer = False
    for line in result.stdout.splitlines():
        if line.startswith(';; ANSWER SECTION:'):
            in_answer = True
            continue
        if in_answer:
            if not line.strip():
                break
            found = IP_REGEX.search(line)
            if found:
                ip = found.group(0)

    return (rcode, ip, False)

def is_real_ip(value):
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return value != '0.0.0.0'

failures = 0

def report(name, passed, detail):
    global failures
    print(f"{'PASS' if passed else 'FAIL'}  {name:<34} {detail}")
    if not passed:
        failures += 1

# Check 1 — real domain via Pi-hole → expect a real IP
rcode, ip, timed_out = helper_dig('google.com', parser.dns_server)
if timed_out:
    report('google.com via Pi-hole', False, 'UNREACHABLE (no response)')
else:
    report('google.com via Pi-hole', is_real_ip(ip), f'status={rcode} ip={ip}')

# Check 2 — ad domain via Pi-hole → expect 0.0.0.0
rcode, ip, timed_out = helper_dig('doubleclick.net', parser.dns_server)
if timed_out:
    report('doubleclick.net blocked', False, 'UNREACHABLE (no response)')
else:
    report('doubleclick.net blocked', ip == '0.0.0.0', f'status={rcode} ip={ip}')

# Check 3 — real domain via Unbound → expect a real IP
rcode, ip, timed_out = helper_dig('google.com', '127.0.0.1', parser.unbound_port)
if timed_out:
    report('google.com via Unbound', False, 'UNREACHABLE (no response)')
else:
    report('google.com via Unbound', is_real_ip(ip), f'status={rcode} ip={ip}')

# Check 4 — DNSSEC enforcement → SERVFAIL is the PASS
rcode, ip, timed_out = helper_dig('fail01.dnssec.works', '127.0.0.1', parser.unbound_port)
if timed_out:
    report('DNSSEC enforcement', False, 'UNREACHABLE (no response)')
else:
    report('DNSSEC enforcement', rcode == 'SERVFAIL', f'status={rcode} ip={ip}')

print(f"\n{4 - failures}/4 checks passed")
sys.exit(1 if failures else 0)
