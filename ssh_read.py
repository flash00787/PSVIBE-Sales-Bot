#!/usr/bin/env python3
"""SSH helper to read file lines from VPS."""
import subprocess, sys

host = "5.223.81.16"
key = "/home/node/.openclaw/workspace/.ssh/id_rsa"
cmd = sys.argv[1] if len(sys.argv) > 1 else ""

ssh_cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no",
    "-i", key,
    f"root@{host}",
    cmd
]
result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
