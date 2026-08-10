disk_check.py

Monitoring-style check for filesystem capacity. Runs df -h, parses the output, and reports any filesystem at or above a usage threshold.

Designed to be used as an automated check: the exit code is the finding, so it can gate other commands or drive alerting.

Usage
bash
python3 disk_check.py [--threshold N] [--verbose]
Flag	Default	Description
--threshold N	80	Usage percentage at which a filesystem is reported
--verbose	off	Print every filesystem with its usage, not just breaches
Examples

Check with the default 80% threshold:

bash
$ python3 disk_check.py
The filesystem - devfs is at or above the threshold 80
The filesystem - /dev/disk3s5 is at or above the threshold 80
The filesystem - map auto_home is at or above the threshold 80

Show all filesystems with their usage:

bash
$ python3 disk_check.py --threshold 50 --verbose
Filesystem: /dev/disk3s1s1 ---> Capacity: 17
Filesystem: devfs ---> Capacity: 100
Filesystem: /dev/disk3s5 ---> Capacity: 87

Use the exit code to trigger follow-up action:

bash
python3 disk_check.py --threshold 90 || ./page_oncall.sh
Exit codes
Code	Meaning
0	All filesystems below threshold
1	One or more filesystems at or above threshold, or df not found
other	Propagated from df if the command itself failed
Notes

Parses df -h output, handling filesystem names that contain spaces (e.g. map auto_home). Written for macOS/BSD df; column layout differs on some Linux distributions.

Requirements

Python 3.8+