"""Freshdesk queue definitions for sp-inbound-vetting batch runs."""

from __future__ import annotations

from dataclasses import dataclass

SPM_GROUP_ID = "159000485013"


@dataclass(frozen=True)
class VettingQueue:
    key: str
    label: str
    freshdesk_view: str
    query: str
    inbox_label: str
    recipient_gate: tuple[str, ...] | None = None


QUEUES: dict[str, VettingQueue] = {
    "ksonboarding": VettingQueue(
        key="ksonboarding",
        label="KS Onboarding",
        freshdesk_view="KSOnboarding",
        query=f"group_id:{SPM_GROUP_ID} AND status:2 AND type:'KSOnboarding'",
        inbox_label="ksonboarding@vixxo.com",
    ),
    "invoice-concerns": VettingQueue(
        key="invoice-concerns",
        label="SPM - Invoice Concerns",
        freshdesk_view="SPM - Invoice Concerns",
        query=f"group_id:{SPM_GROUP_ID} AND status:2 AND type:'Invoice Support'",
        inbox_label="spm-invoice-concerns",
    ),
    "aphelp": VettingQueue(
        key="aphelp",
        label="AP Help",
        freshdesk_view="AP Help (mailbox gate)",
        query=f"group_id:{SPM_GROUP_ID} AND status:2",
        inbox_label="aphelp@vixxo.com",
        recipient_gate=("aphelp@vixxo.com",),
    ),
}


def resolve_queues(queue_arg: str) -> list[VettingQueue]:
    key = (queue_arg or "all").strip().lower()
    if key == "all":
        return list(QUEUES.values())
    if key not in QUEUES:
        known = ", ".join(sorted(list(QUEUES) + ["all"]))
        raise SystemExit(f"Unknown queue {queue_arg!r}. Choose one of: {known}")
    return [QUEUES[key]]
