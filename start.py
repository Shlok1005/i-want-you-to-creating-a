"""
Cross-platform launcher for Fitness Gurukul.
Tries common Windows/macOS/Linux Python commands.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


CANDIDATES = [
    # Windows Python launcher first
    ["py", "-3"],
    ["py"],
    ["python"],
    ["python3"],
]


def find_python():
    for cmd in CANDIDATES:
        exe = shutil.which(cmd[0])
        if not exe:
            continue
        try:
            probe = subprocess.run(
                cmd + ["-c", "import sys; print(sys.version_info[0])"],
                check=False,
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0 and probe.stdout.strip().startswith("3"):
                return cmd
        except OSError:
            continue
    return None


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    server = os.path.join(root, "server.py")
    if not os.path.exists(server):
        print("Could not find server.py next to start.py")
        return 1

    # If this file is already running under Python 3, just exec server.py.
    if sys.version_info.major >= 3:
        os.chdir(root)
        sys.argv = [server] + sys.argv[1:]
        with open(server, encoding="utf-8") as fh:
            code = compile(fh.read(), server, "exec")
        globals_dict = {
            "__name__": "__main__",
            "__file__": server,
            "__package__": None,
        }
        exec(code, globals_dict)
        return 0

    cmd = find_python()
    if not cmd:
        print("Python 3 was not found.")
        print("")
        print("On Windows:")
        print("  1. Install Python from https://www.python.org/downloads/")
        print("  2. During setup, check \"Add python.exe to PATH\"")
        print("  3. Open a new PowerShell window, then run:")
        print("       py server.py")
        print("     or:")
        print("       python server.py")
        print("")
        print("If Windows opens the Microsoft Store instead, turn OFF the")
        print("App execution aliases for python.exe / python3.exe:")
        print("  Settings > Apps > Advanced app settings > App execution aliases")
        return 1

    return subprocess.call(cmd + [server] + sys.argv[1:], cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
