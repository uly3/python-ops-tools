# jwt_peek.py

Decodes a JSON Web Token (JWT) stored in a JSON file, prints its header and payload, and reports whether it has expired. Built for inspecting the access tokens an API login returns — whose identity they carry, who issued them, and how long they have left.

**It decodes. It does not verify.** Nothing this tool prints means a token is genuine.

Standard library only — runs anywhere Python 3 does.

## Usage

```bash
python3 jwt_peek.py <file> [--key KEY]
```

| Argument | Default | Description |
|---|---|---|
| `file` | *(required)* | JSON file holding one or more tokens |
| `--key KEY` | `Access_Token` | Which token in the file to inspect |

The default matches the `{"Access_Token": ..., "Refresh_Token": ...}` layout that a login script typically exports.

## Examples

A token that's still valid:

```bash
$ python3 jwt_peek.py tokens.json
JSON file loaded successfully...
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "sub": "uly@example.com",
  "name": "Uly Test",
  "iss": "https://auth.example.com",
  "iat": 1795132800,
  "exp": 1893456000
}
Signature: NOT verified - decoded only
Current Time:   2026-11-23 04:56:49.861707+00:00
Token EXP Time: 2030-01-01 00:00:00+00:00
Time Left on Token: 1134 days, 19:03:10.138293
```

An expired one:

```bash
$ python3 jwt_peek.py tokens.json --key Expired_Token
...
Signature: NOT verified - decoded only
Current Time:   2026-11-23 04:56:49.889798+00:00
Token EXP Time: 2026-06-01 00:00:00+00:00
Token EXPIRED 175 days, 4:56:49.889798 ago
$ echo $?
1
```

Values that aren't usable JWTs:

```bash
$ python3 jwt_peek.py tokens.json --key Refresh_Token
ERROR: Refresh_Token is not a JWT (expected 3 parts, found 1)

$ python3 jwt_peek.py tokens.json --key Corrupt_Token
ERROR: Corrupt_Token could not be decoded: Expecting ',' delimiter: line 1 column 37 (char 36)
```

## What a JWT is

```
eyJhbGciOiJSUzI1NiJ9 . eyJzdWIiOiJ1bHkiLCJleHAiOjE4OTM0NTYwMDB9 . ZmFrZS1zaWduYXR1cmU
└────── header ─────┘   └──────────────── payload ──────────────┘   └── signature ──┘
  {"alg":"RS256"}          {"sub":"uly","exp":1893456000}             binary, not decoded
```

Three base64url-encoded parts joined by dots. The header names the signing algorithm, the payload carries the claims, and the signature proves who issued it. Every JWT begins with `eyJ`, which is simply `{"` encoded.

Common claims:

| Claim | Meaning |
|---|---|
| `sub` | Subject — who the token represents |
| `iss` | Issuer — who created it |
| `iat` | Issued at, in Unix time |
| `exp` | Expires at, in Unix time |

## Decoding is not verifying

The payload is **encoded, not encrypted.** Anyone holding a token can read every claim, which is why secrets never belong inside a JWT.

More importantly, anyone holding a token can **use** it until it expires. A JWT is a bearer credential: possession is authorization.

Verifying a token means checking its signature against the issuer's public key. This tool never does that — every token in the test fixture carries a fake signature and still decodes cleanly. So the tool never calls a token "valid"; after the claims it states plainly that the signature was not verified. Use a library such as PyJWT when a decision depends on trusting the token.

## Errors never print the token

When a value can't be parsed, the error names the key and what was wrong — never the token itself. Error output ends up in terminal scrollback, CI logs, and cron mail, and a refresh token echoed in an error message is a working credential written into every one of them.

## Base64url padding

Base64 encodes in four-character blocks, padding the last one with `=`. JWTs strip that padding to keep tokens compact, but Python's decoder refuses input without it, so the padding is restored before decoding.

Whether a segment needs padding depends on its length, so leaving this step out fails only on some segments — commonly the header decodes and the payload doesn't, with `Incorrect padding`.

Bad base64, bytes that aren't text, and text that isn't JSON all raise subclasses of `ValueError`, so the decode step handles all three in one place.

## Expiry

`exp` is Unix time — seconds since 1970-01-01 UTC, the same representation as a file's modification time. It's converted to a timezone-aware UTC datetime and compared with the current UTC time. A token is expired once the current time reaches `exp`.

Expired tokens report how long ago they expired. Python renders a negative duration confusingly — `-176 days, 19:13:58` means 175 days and 4 hours ago — so the subtraction is reversed for that case.

**A token with no `exp` is treated as a finding** and exits non-zero. A credential that never expires stays usable indefinitely if it leaks, which is worth surfacing rather than passing silently.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Token decoded and not yet expired |
| `1` | Expired, no expiry claim, not a JWT, could not be decoded, key missing, file missing or not a file, or invalid JSON |
| `2` | Invalid arguments |

Fetch a fresh token only when the current one has expired:

```bash
python3 jwt_peek.py AF.json > /dev/null || <login command>
```

Because a token without `exp` also exits `1`, this pattern refreshes on every run for such tokens.

## Test fixture

`tokens.json` holds five fake tokens for `example.com`, signed by nobody, each exercising one branch:

| Key | Exercises |
|---|---|
| `Access_Token` | Valid until 2030 |
| `Refresh_Token` | Opaque string — not a JWT |
| `Expired_Token` | Expired June 2026 |
| `No_Expiry_Token` | No `exp` claim |
| `Corrupt_Token` | Payload decodes but isn't valid JSON |

## Notes

Files holding live tokens, such as `AF.json`, are gitignored in this repository. Real tokens never belong in version control — public or private.

All times are UTC.
