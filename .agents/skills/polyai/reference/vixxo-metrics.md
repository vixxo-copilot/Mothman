# Vixxo voice call metrics (PolyAI)

Metrics appear in Conversations API `metrics` — not separate MCP tool events.

## Core outbound

| Metric | Meaning |
| --- | --- |
| `VALID_SR` | SR validated at call start |
| `API_OK` | Backend API write succeeded |
| `OUT_OF_SCOPE_SR` | SR outside outbound USP scope |
| `TRANSACTION_TYPE` | Call purpose (e.g. New ETA Required) |
| `SR_SUBSTATUS` | SR substatus at time of call |
| `UPDATE_ETA_SUCCESSFUL` | ETA posted to Vixxo |
| `UPDATE_ETA_START` | ETA collection flow started |
| `UPDATE_ETA_ETA_COLLECTED` | Caller gave an ETA |
| `UPDATE_ETA_DETAILS_CONFIRMED` | Caller confirmed details |
| `TECHNICIAN_STATUS` | e.g. REQUIRES_ETA |

## Call path

| Metric | Meaning |
| --- | --- |
| `CALL_CONNECTED` | Call connected (PolyAI platform signal) |
| `HUMAN_ENCOUNTERED` | Reached a person |
| `CALL_ANSWERED_BY` | HUMAN / VOICEMAIL / IVR tags |
| `IVR_ENCOUNTERED` | Hit a phone tree |
| `IVR_DURATION_EXCEEDED` | Stuck in phone tree too long |
| `VOICEMAIL_ENCOUNTERED` | Voicemail detected |
| `USER_HANGUP` | Callee hung up |

## Outbound telephony

| Metric | Meaning |
| --- | --- |
| `OUTBOUND_CALL_STATUS` | Success / Unavailable / Busy |
| `OUTBOUND_CALL_SIP_CODE` | SIP result (480, 486, 200, …) |
| `AGENT_FALLBACK` | Platform fallback before conversation |

## Studio / analytics

| Metric | Meaning |
| --- | --- |
| `VARIANT_ID` | A/B or environment variant ID |
| `TOTAL_AGENT_TURNS` | Agent turn count (metric mirror) |
