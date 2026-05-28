# V2 Full Audit — Coordination Spec

**Date:** 2026-05-27  
**Triggered by:** Boss Osmo  
**Orchestrator:** Kora  

---

## Audit Scope
- **V2 Location:** `/root/psvibe-sale-bot/` (running)  
- **Staging:** `/root/staging/bot_src/`  
- **V1 Reference:** `/root/staging/monolithic_ref/main.py` (12,249 lines)  
- **VPS:** 5.223.81.16 (root)

## VPS Access
```
Host: 5.223.81.16
User: root
Key: /home/node/.openclaw/workspace/.ssh/id_rsa
Password: Available in .secrets_map.json (key: S1_PSVIBE_2024)
```

## 5 Sub-Agent Assignments

| Agent | Task | Output File |
|---|---|---|
| A1 | Code Structure & Imports | `AUDIT_A1_imports.md` |
| A2 | Function Parity (V1 vs V2) | `AUDIT_A2_parity.md` |
| A3 | ConversationHandler States | `AUDIT_A3_states.md` |
| A4 | Dead Code & Duplication | `AUDIT_A4_deadcode.md` |
| A5 | Security & Config Audit | `AUDIT_A5_security.md` |

## Rules
- Each agent writes ONLY to its own output file
- Use SSH key auth (not password)
- SSH command: `ssh -o StrictHostKeyChecking=no -i /home/node/.openclaw/workspace/.ssh/id_rsa root@5.223.81.16`
- Report in English (technical terms)
- Be thorough — cover ALL files, not just samples
- Timeout: 10 min per agent
