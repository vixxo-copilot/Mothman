---
name: polyai-conversation-audit
description: >-
  Alias for the polyai skill. Use for outbound conversation audit, hang-up
  analysis, CSV export, and disconnect breakdowns. Loads polyai skill.
---

# PolyAI Conversation Audit (alias)

**Use the `polyai` skill.** This name exists for backward compatibility.

## Workflow

1. Load `.agents/skills/polyai/SKILL.md`
2. If no fresh CSV → `export_conversations.py`
3. Bulk hang-up / provider / time questions → `analyze_export.py`
4. Single call → `audit_conversation.py`

```bash
python3 .agents/skills/polyai/scripts/polyai_client.py projects
python3 .agents/skills/polyai/scripts/export_conversations.py --all-projects
python3 .agents/skills/polyai/scripts/analyze_export.py fixable-buckets
python3 .agents/skills/polyai/scripts/audit_conversation.py --pick-best
```

See `polyai/reference/export-and-analysis.md` and
`polyai/reference/conversation-audit.md`.
