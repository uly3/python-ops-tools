import argparse, sys, socket

start_parse = argparse.ArgumentParser(description="Checks whether TCP ports are open on one or more hosts")
start_parse.add_argument('targets', nargs='+', help='One or more host:port pairs to check')
start_parse.add_argument('--timeout', type=float, default=2, help='Seconds to wait for each connection')
parser = start_parse.parse_args()

check = 0
error = 0

for element in parser.targets:

    host, sep, port = element.rpartition(':')

    if not sep or not host:
        print(f"INVALID     {element} (expected host:port)")
        error += 1
        continue

    try:
        port = int(port)
    except ValueError:
        print(f"INVALID     {element} (port is not a number)")
        error += 1
        continue

    if not 1 <= port <= 65535:
        print(f"INVALID     {element} (port must be 1-65535)")
        error += 1
        continue

    try:
        with socket.create_connection((host, port), timeout=parser.timeout):
            # if we got here, the port is open — `with` closes it immediately
            pass

        print(f"OPEN        {host}:{port}")
        check += 1

    except ConnectionRefusedError:
        print(f"REFUSED     {host}:{port}")
        error += 1
    except socket.timeout:
        print(f"TIMEOUT     {host}:{port}")
        error += 1
    except socket.gaierror:
        print(f"HOSTNAME_UNRESOLVED     {host}:{port}")
        error += 1
    except OSError as e:
        print(f"An error occurred... {e} - {host}:{port}")
        error += 1

print(f"{check}/{len(parser.targets)} OPEN")

sys.exit(1 if error > 0 else 0)
