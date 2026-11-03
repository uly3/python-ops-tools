# hash_check.py

Computes a file's cryptographic hash and optionally verifies it against an expected value. The standard way to confirm a download — an ISO, an installer, a release archive — arrived intact and unmodified.

Standard library only. Runs identically on macOS, Linux, and Windows.

## Usage

```bash
python3 hash_check.py <file> [--algo ALGORITHM] [--expect HASH]
```

| Argument | Default | Description |
|---|---|---|
| `file` | *(required)* | File to hash |
| `--algo` | `sha256` | One of `md5`, `sha1`, `sha256` |
| `--expect` | none | Hash to compare against |

## Examples

Compute a hash:

```bash
$ python3 hash_check.py ubuntu-26.04.1-live-server-amd64.iso
File: /Users/uly/Downloads/ubuntu-26.04.1-live-server-amd64.iso
Hash: cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927
```

Verify against a published value:

```bash
$ python3 hash_check.py ubuntu-26.04.1-live-server-amd64.iso --expect cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927
File: /Users/uly/Downloads/ubuntu-26.04.1-live-server-amd64.iso
Hash: cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927

Hash to Match: cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927

MATCH
```

A mismatch reports both values and exits non-zero:

```bash
$ python3 hash_check.py test.txt --expect 0000000000000000000000000000000000000000000000000000000000000000
...
MISMATCH
$ echo $?
1
```

## Verifying a download properly

Comparing against your own second tool only proves the hashing is correct. To verify a download, compare against the value the **publisher** distributes — for Ubuntu, the `SHA256SUMS` file alongside the ISO on releases.ubuntu.com.

A hash is only as trustworthy as its source. If a download mirror were compromised, the hash published on that same mirror could be replaced to match the tampered file. Publishers address this by signing the checksum file — Ubuntu ships `SHA256SUMS.gpg` — so the hashes themselves can be verified as coming from the publisher.

## How it reads files

Files are opened in **binary mode** and fed to the hash in 64 KB chunks.

Binary mode matters for correctness. In text mode on Windows, Python translates `\r\n` line endings to `\n` as it reads, which changes the bytes — and therefore the hash. Reading raw bytes produces the same result every other tool computes.

Chunking matters for size. A multi-gigabyte ISO is never loaded into memory; only one chunk is held at a time, so memory use is constant regardless of file size.

The same bytes produce the same hash on every platform and CPU architecture. That's what makes a published hash useful: it was computed on the publisher's hardware and still matches on yours. Two files that *look* identical but hash differently genuinely differ — usually in line endings or text encoding.

## Comparison

`--expect` is compared case-insensitively, with surrounding whitespace ignored. Tools disagree on letter case for the same value — macOS `shasum` prints lowercase, PowerShell `Get-FileHash` prints uppercase — and a pasted hash often carries a trailing space or newline. None of those should register as a mismatch.

## Choosing an algorithm

| Algorithm | Use |
|---|---|
| `sha256` | Default. Suitable for detecting both corruption and tampering. |
| `sha1` | Corruption only. Practical collision attacks exist. |
| `md5` | Corruption only. Collisions are trivial to manufacture. |

MD5 and SHA-1 remain available because older projects still publish them, and for catching an accidentally truncated or corrupted download they work fine. They can't be relied on to detect a deliberately altered file.

## Empty files

An empty file is hashed normally rather than treated as an error. Zero bytes has a perfectly well-defined hash (SHA-256: `e3b0c442…b855`), and a download that came through empty will simply fail to match the expected value — so `--expect` already catches it without a special case.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Hash computed, or `--expect` matched |
| `1` | File missing or not a regular file, or `--expect` did not match |
| `2` | Invalid arguments, such as an unsupported algorithm |

Usable as a gate before installing anything:

```bash
python3 hash_check.py installer.iso --expect "$PUBLISHED_HASH" && ./install.sh
```
