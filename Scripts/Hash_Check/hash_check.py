import argparse, sys, hashlib
from pathlib import Path

def lets_hash(file_name, algorithm, kb_to_read = 65536):
    hash_result = hashlib.new(algorithm)

    with open(file_name, 'rb') as file_obj:
        while True:
            chunk = file_obj.read(kb_to_read)
            if not chunk:
                break
            hash_result.update(chunk)

    return hash_result.hexdigest()

start_parse = argparse.ArgumentParser(description="Computes a file’s cryptographic hash and optionally verifies it against an expected value")
start_parse.add_argument('file', type=str, help='File to compute its HASH')
start_parse.add_argument('--algo', type=str, choices=['md5', 'sha1', 'sha256'], default='sha256', help='The HASH algorithm')
start_parse.add_argument('--expect', type=str, help='hash to compare with')
parser = start_parse.parse_args()

first_hash = Path(parser.file).resolve()

if not first_hash.exists():
    print(f"The file to hash does not exist! --> {first_hash}", file=sys.stderr)
    sys.exit(1)

if not first_hash.is_file():
    print(f"The file to hash is not a file! --> {first_hash}", file=sys.stderr)
    sys.exit(1)

first_hash_hex = str(lets_hash(first_hash, parser.algo)).strip().lower()

if parser.expect:

    second_hash_hex = str(parser.expect).strip().lower()

    print(f"File: {first_hash}\nHash: {first_hash_hex}\n")
    print(f"Hash to Match: {second_hash_hex}\n")

    if second_hash_hex == first_hash_hex:
        print("\nMATCH")
        sys.exit(0)
    else:
        print("\nMISMATCH")
        sys.exit(1)
else:
    print(f"File: {first_hash}\nHash: {first_hash_hex}")
sys.exit(0)
