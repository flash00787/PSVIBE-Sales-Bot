#!/usr/bin/env python3
"""Execute commands or file edits on remote server via paramiko."""
import paramiko, sys, os, json

HOST = "5.223.81.16"
KEY_PATH = os.path.expanduser("/home/node/.openclaw/workspace/.ssh/id_rsa")
USER = "root"

def run_cmd(cmd, timeout=20):
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, pkey=key, timeout=10)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_code = stdout.channel.recv_exit_status()
    client.close()
    return {"stdout": out, "stderr": err, "exit_code": exit_code}

def remote_edit(filepath, edits):
    """Apply edits to a remote file."""
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, pkey=key, timeout=10)
    sftp = client.open_sftp()
    with sftp.file(filepath, 'r') as f:
        content = f.read().decode('utf-8', errors='replace')
    for old_text, new_text in edits:
        if old_text not in content:
            sftp.close()
            client.close()
            return {"stdout": "", "stderr": f"Edit FAILED: oldText not found in {filepath}", "exit_code": 1}
        content = content.replace(old_text, new_text, 1)
    with sftp.file(filepath, 'w') as f:
        f.write(content)
    sftp.close()
    client.close()
    return {"stdout": f"OK: {len(edits)} edit(s) applied to {filepath}", "stderr": "", "exit_code": 0}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: remote_exec.py '<command>'")
        sys.exit(1)
    cmd = sys.argv[1]
    result = run_cmd(cmd)
    print(result["stdout"])
    if result["stderr"]:
        print("STDERR:", result["stderr"][:500], file=sys.stderr)
    sys.exit(result["exit_code"])
