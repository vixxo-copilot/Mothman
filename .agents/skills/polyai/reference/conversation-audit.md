# Conversation audit report template

## Report

```markdown
## PolyAI conversation audit

**ID:** …
**Started:** …
**Duration:** …s | **Turns:** …
**Variant:** …

### Outcome
- Outbound status: …
- Transaction type: …
- SR substatus: …

### Integration
- VALID_SR: yes/no
- API_OK: yes/no
- ETA update: started / successful
- Path: polyai_custom_api | vixxolink_mcp

### SR (if extracted)
- Number: …
- VixxoLink cross-check: …

### Narrative (redacted)
- …
```

## Bulk analysis (prefer for hang-ups / providers)

```bash
python3 .agents/skills/polyai/scripts/export_conversations.py --all-projects
python3 .agents/skills/polyai/scripts/analyze_export.py summary --all-projects
python3 .agents/skills/polyai/scripts/analyze_export.py fixable-buckets
```

See [export-and-analysis.md](export-and-analysis.md).

## Single-call audit

```bash
python3 .agents/skills/polyai/scripts/audit_conversation.py --pick-best --project vixxo-outbound-usp
python3 .agents/skills/polyai/scripts/audit_conversation.py --conversation-id OUT-xxxxxxxx --full-scan
```
