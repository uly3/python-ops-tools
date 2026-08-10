sys_report.py

Runs an arbitrary system command, captures its output, and produces a structured report — execution time, return code, output size, and a preview of the results. Optionally writes the report as JSON for downstream processing.

Useful as a wrapper for auditing what a command actually did, or as a building block for scripted health checks.

Usage
bash
python3 sys_report.py <command> [--args ARG ...] [--timeout N] [--json FILENAME]
Argument	Default	Description
command	(required)	The command to execute
--args ARG ...	none	Arguments to pass to the command
--timeout N	30	Seconds before the command is killed
--json FILENAME	none	Also write the report as JSON to this file
Examples

Run a command and report on it:

bash
$ python3 sys_report.py df
Command Used: df
Return Code: 0
Duration: 0.0
Line Count: 11
Output:
 Filesystem     512-blocks      Used Available Capacity  Mounted on
/dev/disk3s1s1  965595304  24551664 127501024    17%   /
devfs                 693       693         0   100%   /dev
Timestamp:  2026/08/02 11:26:16 PM

Pass arguments to the command:

bash
$ python3 sys_report.py ls --args="-la"

Note: use --args="-la" (with the equals sign) when an argument begins with a dash. Without it, argparse interprets -la as a flag belonging to sys_report.py rather than a value.

Write a machine-readable report:

bash
$ python3 sys_report.py df --json report.json
json
{
  "Command_Used": "df",
  "Return_Code": 0,
  "Duration": 0.0,
  "Line_Count": 11,
  "Output": [
    "Filesystem     512-blocks      Used Available Capacity  Mounted on",
    "/dev/disk3s1s1  965595304  24551664 127501024    17%   /"
  ]
}

Guard against a hanging command:

bash
$ python3 sys_report.py some_slow_command --timeout 5
ERROR: command timed out after 5 seconds
Report fields
Field	Description
Command_Used	The full command line as executed
Return_Code	Exit status of the command
Duration	Wall-clock execution time in seconds
Line_Count	Total lines of stdout produced
Output	First 5 lines of stdout
Exit codes
Code	Meaning
0	Command succeeded (including when it produced no output)
1	Command timed out, or the executable was not found
other	Propagated from the command itself when it exits non-zero

Propagating the command's own return code keeps the wrapper honest to whatever calls it — a shell && chain or CI step sees the real failure status rather than a flattened 1.

Notes

Commands are executed with arguments passed as a list rather than through a shell, so shell metacharacters in arguments are not interpreted. Output is captured as text and truncated to the first 5 lines in the report; the full line count is still reported.

Always runs with a timeout — important for anything invoked by cron or a systemd timer, where a hung process would otherwise accumulate on every interval.