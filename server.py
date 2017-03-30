import subprocess

import sys


def main():
    subprocess.call("python Notifications.py", shell=True)
    subprocess.call("python DailyDigest.py", shell=True)

if __name__ == '__main__':
    sys.exit(main())
