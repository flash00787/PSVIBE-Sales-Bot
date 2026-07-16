#!/usr/bin/env python3
"""
LLM Key Health Monitor — Check API keys for all OpenClaw agents.

Usage:
    python3 llm_health_monitor.py         # Full status table
    python3 llm_health_monitor.py --json   # JSON output
    python3 llm_health_monitor.py --status # Exit code only (0=all OK, 1=issues)
"""

import json, os, subprocess, sys
from datetime import datetime, timezone

# ── Config ───────────────────────────────────────────────────────────
COMPOSE_FILE = "/opt/openclaw/docker-compose.yml"
RESULTS_FILE = "/root/.openclaw/workspace/memory/llm-health.json"
HOST_ENV_FILE = "/root/.openclaw/.env"

# ── Helpers ──────────────────────────────────────────────────────────

def run_curl_test(cmd_args, timeout=15):
    """Run curl and return (exit_code, status_code, body)."""
    try:
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=timeout)
        out = result.stdout.strip()
        parts = out.rsplit("\n", 1)
        body = parts[0] if len(parts) > 1 else ""
        code = int(parts[-1].strip()) if parts[-1].strip() else 0
        return 0, code, body
    except subprocess.TimeoutExpired:
        return -1, 0, "timeout"
    except Exception as e:
        return -1, 0, str(e)

def test_deepseek(api_key):
    """Test DeepSeek key via chat completions (detects 402)."""
    if not api_key:
        return "⚪ None"
    try:
        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 5
        })
        rc, code, body = run_curl_test([
            "curl", "-s", "-w", "\n%{http_code}",
            "https://api.deepseek.com/v1/chat/completions",
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {api_key}",
            "-d", payload,
        ])
        if code == 200:
            return "🟢 Working"
        elif code == 402:
            return "🔴 402 Insuf Bal"
        elif code == 401:
            return "🔴 Invalid Key"
        else:
            return f"🔴 HTTP {code}"
    except Exception as e:
        return f"🔴 Error: {e}"

def test_gemini(api_key):
    """Test Gemini key via models list."""
    if not api_key:
        return "⚪ None"
    try:
        rc, code, body = run_curl_test([
            "curl", "-s", "-w", "\n%{http_code}",
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
        ])
        if code == 200:
            return "🟢 Working"
        elif code == 400:
            return "🔴 Invalid Key"
        elif code == 403:
            return "🔴 Forbidden"
        elif code == 429:
            return "🔴 Rate Limited"
        else:
            return f"🔴 HTTP {code}"
    except Exception as e:
        return f"🔴 Error: {e}"

def test_openrouter(api_key):
    """Test OpenRouter key."""
    if not api_key:
        return "⚪ None"
    try:
        rc, code, body = run_curl_test([
            "curl", "-s", "-w", "\n%{http_code}",
            "https://openrouter.ai/api/v1/auth/key",
            "-H", f"Authorization: Bearer {api_key}",
        ])
        if code == 200:
            return "🟢 Working"
        elif code == 401:
            return "🔴 Invalid Key"
        else:
            return f"🔴 HTTP {code}"
    except Exception as e:
        return f"🔴 Error: {e}"

def read_docker_compose_keys():
    """Read API keys from docker-compose.yml for all OpenClaw agents."""
    agents = {}
    if not os.path.exists(COMPOSE_FILE):
        return agents

    try:
        import yaml
        with open(COMPOSE_FILE) as f:
            d = yaml.safe_load(f)
        for name, svc in d.get("services", {}).items():
            if "openclaw" in svc.get("image", ""):
                env = {}
                for e in svc.get("environment", []):
                    if "=" in e:
                        k, v = e.split("=", 1)
                        env[k] = v
                agents[svc.get("container_name", name)] = {
                    "DEEPSEEK_API_KEY": env.get("DEEPSEEK_API_KEY", ""),
                    "GEMINI_API_KEY": env.get("GEMINI_API_KEY", ""),
                    "GOOGLE_API_KEY": env.get("GOOGLE_API_KEY", ""),
                    "OPENROUTER_API_KEY": env.get("OPENROUTER_API_KEY", ""),
                }
    except Exception:
        pass
    return agents

def read_host_keys():
    """Read main Kora's API keys from host env."""
    keys = {
        "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),
    }
    # Also try .env file
    if os.path.exists(HOST_ENV_FILE):
        with open(HOST_ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k in keys and not keys[k]:
                        keys[k] = v
    return keys

def truncate_key(key):
    """Truncate key for display."""
    if not key:
        return "N/A"
    if len(key) > 12:
        return f"{key[:4]}...{key[-4:]}"
    return key

def main():
    # Read keys
    docker_agents = read_docker_compose_keys()
    host_keys = read_host_keys()

    # Build test list
    tests = []

    # Main Kora (host)
    tests.append(("Main Kora", host_keys))

    # Docker agents
    agent_display = {"oc-coco": "oc-coco", "oc-nova": "oc-nova", "oc-gayzoelay": "oc-gayzoelay"}
    for name, keys in sorted(docker_agents.items()):
        display = agent_display.get(name, name)
        tests.append((display, keys))

    # Run tests
    results = []
    for name, keys in tests:
        # Skip disabled agents
        if name == "oc-gayzoelay" or "gayzoelay" in name.lower():
            results.append({
                "agent": name,
                "DeepSeek": "⚪ Disabled",
                "Gemini": "⚪ Disabled",
                "OpenRouter": "⚪ Disabled",
                "status": "⚪",
            })
            continue

        deepseek = test_deepseek(keys.get("DEEPSEEK_API_KEY", ""))
        gemini = test_gemini(keys.get("GEMINI_API_KEY", ""))
        openrouter = test_openrouter(keys.get("OPENROUTER_API_KEY", ""))

        # Determine overall status
        status_parts = []
        if "🟢" in deepseek:
            status_parts.append("DS")
        if "🟢" in gemini:
            status_parts.append("GM")
        if "🟢" in openrouter:
            status_parts.append("OR")

        if len(status_parts) >= 2:
            status = "🟢"
        elif len(status_parts) == 1:
            status = "🟡"
        else:
            status = "🔴"

        results.append({
            "agent": name,
            "DeepSeek": deepseek,
            "Gemini": gemini,
            "OpenRouter": openrouter,
            "status": status,
        })

    # Print table (skip if --json)
    if "--json" not in sys.argv:
        print(f"\n{'Agent':<15s} {'DeepSeek':<20s} {'Gemini/GDrive':<20s} {'OpenRouter':<20s} {'Status':<8s}")
        print(f"{\\u2500'*15} {\─'*20} {\─'*20} {\─'*20} {\─'*8}")
    has_issues = False
    for r in results:
        ds = r["DeepSeek"]
        gm = r["Gemini"]
        or_ = r["OpenRouter"]
        if "--json" not in sys.argv:
            print(f"{r['agent']:<15s} {ds:<20s} {gm:<20s} {or_:<20s} {r['status']:<8s}")
        if r["status"] == "🔴" and "Disabled" not in ds:
            has_issues = True
    if "--json" not in sys.argv:
        print()

    # Save results
    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "results": results,
        "has_issues": has_issues,
    }
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    # Summary
    if "--json" in sys.argv:
        print(json.dumps(output, indent=2))
        return

    working = sum(1 for r in results if r["status"] == "🟢")
    partial = sum(1 for r in results if r["status"] == "🟡")
    failing = sum(1 for r in results if r["status"] == "🔴" and "⚪" not in r["DeepSeek"])

    if has_issues:
        print(f"⚠️  {failing} agent(s) have issues — check keys above")
        if "--status" in sys.argv:
            sys.exit(1)
    else:
        print(f"✅ All agents healthy!")
        if "--status" in sys.argv:
            sys.exit(0)


if __name__ == "__main__":
    main()
