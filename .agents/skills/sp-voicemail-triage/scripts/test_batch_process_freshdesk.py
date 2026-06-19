#!/usr/bin/env python3
"""Focused tests for voicemail context enrichment helpers."""

from __future__ import annotations

import unittest

from batch_process_freshdesk import (
    SP_REVIEW_TAG,
    infer_sp_context,
    resolve_cf_sp_value,
    voicemail_summary,
)


class VoicemailContextTests(unittest.TestCase):
    def test_infers_company_from_spoken_intro(self) -> None:
        meta = {"caller": "TATE,JERRY", "company": "TATE,JERRY"}
        spoken = (
            "Yeah, this is Jerry Tate with Accurate Maintenance, my third "
            "voicemail this week trying to get help on work order 6576341842."
        )

        context = infer_sp_context(meta, spoken)

        self.assertEqual(context.name, "Accurate Maintenance")
        self.assertEqual(context.source, "voicemail transcript")
        self.assertFalse(context.review_required)

    def test_does_not_treat_personal_caller_id_as_company(self) -> None:
        meta = {"caller": "TATE,JERRY", "company": "TATE,JERRY"}

        context = infer_sp_context(meta, "Please call me back.")

        self.assertEqual(context.name, "Unknown")
        self.assertTrue(context.review_required)

    def test_cf_sp_uses_inferred_company(self) -> None:
        ticket = {"custom_fields": {"cf_sp": "Unknown"}}
        context = infer_sp_context(
            {"caller": "WIRELESS CALLER", "company": "Not stated"},
            "This is Alex with Blue Sky Plumbing calling about an invoice.",
        )

        self.assertEqual(resolve_cf_sp_value(ticket, context), "Blue Sky Plumbing")

    def test_cf_sp_preserves_existing_when_context_unknown(self) -> None:
        ticket = {"custom_fields": {"cf_sp": "12345 - Existing SP"}}
        context = infer_sp_context(
            {"caller": "WIRELESS CALLER", "company": "Not stated"},
            "Please call me back.",
        )

        self.assertEqual(resolve_cf_sp_value(ticket, context), "12345 - Existing SP")

    def test_summary_includes_route_and_reference(self) -> None:
        meta = {"caller": "TATE,JERRY"}
        context = infer_sp_context(
            {"caller": "TATE,JERRY", "company": "TATE,JERRY"},
            "This is Jerry Tate with Accurate Maintenance about work order 6576341842.",
        )

        summary = voicemail_summary(
            meta,
            "Billing / Invoice Support",
            "aphelp@vixxo.com",
            "Recommended",
            "6576341842",
            "This is Jerry Tate with Accurate Maintenance about work order 6576341842.",
            context,
        )

        self.assertIn("Accurate Maintenance", summary)
        self.assertIn("aphelp@vixxo.com", summary)
        self.assertIn("6576341842", summary)

    def test_review_tag_constant_remains_stable(self) -> None:
        self.assertEqual(SP_REVIEW_TAG, "sp-name-review-needed")


if __name__ == "__main__":
    unittest.main()
