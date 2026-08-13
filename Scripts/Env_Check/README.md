env_check.py

Validates a .env / config file before deployment. Checks that every line is well-formed KEY=VALUE, reports malformed lines with their line numbers, and optionally verifies that required keys are present.

Designed to run as a pre-deploy or CI gate: the exit code is the finding, so a malformed config fails the pipeline instead of silently breaking a service at runtime.

Usage
bash
python3 env_check.py <envfile> [--required KEY ...] [--verbose]
Argument	Default	Description
envfile	(required)	Path to the config file to validate
--required KEY ...	none	Keys that must be present; each missing one is reported
--verbose	off	Print every valid key found, masking sensitive values
Examples

Validate a file:

bash
$ python3 env_check.py app.env
Line 4: malformed — DB PASSWORD=hunter2
Line 9: malformed — MALFORMED_LINE_NO_EQUALS
ERROR: config file is not valid

Check that required keys exist:

bash
$ python3 env_check.py app.env --required DB_HOST DB_PORT SECRET
REQUIRED KEY MISSING: SECRET
ERROR: config file is not valid

Inspect parsed values, with secrets masked:

bash
$ python3 env_check.py app.env --verbose
DB_HOST=10.0.0.5
DB_PORT=5432
API_KEY=***
TIMEOUT=30

A clean file:

bash
$ python3 env_check.py good.env
SUCCESS: config file is valid
$ echo $?
0
Validation rules

A line is valid if it matches KEY=VALUE in full, where KEY starts with a letter or underscore and contains only letters, digits, and underscores.

Line	Result
DB_HOST=10.0.0.5	valid
# comment	skipped — not an error
(blank)	skipped — not an error
DB PASSWORD=hunter2	malformed — space in key
MALFORMED_LINE_NO_EQUALS	malformed — no =

The pattern is anchored at both ends, so a line only passes if the entire line is a valid assignment — not merely if it contains something assignment-shaped.

Secret masking

Under --verbose, a value is replaced with a random set of asterisks when its key contains any of KEY, PASSWORD, SECRET, or TOKEN (case-insensitive).

The mask is a random series of asterisks on purpose. Masking with one character per character (API_KEY=*********) reveals the secret's length, which narrows the search space for anyone reading the output.

This matters because validator output typically lands in CI logs or a central log aggregator. A validator that prints credentials in plaintext has leaked them to everywhere those logs are shipped.

Exit codes
Code	Meaning
0	All lines valid and all required keys present
1	Malformed lines, missing required keys, no valid entries, or file not found

Gate a deploy on a valid config:

bash
python3 env_check.py app.env --required DB_HOST API_KEY && ./deploy.sh
Notes

Reads the file line by line, so it handles large config files without loading them into memory.

A file containing only comments and blank lines is reported as an error rather than a success — a config with zero settings is more likely a wrong path or an unfinished file than a valid one.

Whitespace around = (LOG_LEVEL = debug) is rejected. Shells and Docker's --env-file parser both treat that as invalid, so accepting it here would let a broken config through.

The sample .env files in this directory are test fixtures containing fake values only. Real .env files hold live credentials and should never be committed — add them to .gitignore.