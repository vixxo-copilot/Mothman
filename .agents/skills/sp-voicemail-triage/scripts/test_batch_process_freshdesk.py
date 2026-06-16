#!/usr/bin/env python3
"""Focused tests for Freshdesk voicemail batch processing."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import batch_process_freshdesk as batch


def sample_ticket() -> dict:
    return {
        "id": 12345,
        "subject": "FW: New voicemail from TEST,CALLER via VENDOR RELATIONS",
        "description": "",
        "description_text": (
            "New voicemail from\n"
            "TEST,CALLER (+15555550123)\n"
            "Received on: Tuesday, June 16, 2026 11:23:08 AM Duration: 00:34"
        ),
        "attachments": [
            {
                "name": "voicemail_15555550123.wav",
                "content_type": "application/octet-stream",
                "attachment_url": "https://example.test/voicemail.wav",
            }
        ],
    }


class BatchProcessFreshdeskTests(unittest.TestCase):
    def test_build_transcript_includes_audio_transcription(self) -> None:
        ticket = sample_ticket()
        meta = batch.extract_metadata(ticket)
        with patch.object(
            batch,
            "transcribe_ticket_audio",
            return_value=batch.TranscriptResult(
                text="Please return my call about invoice 456.",
                source="audio transcription",
                status="transcribed",
                attachment_name="voicemail_15555550123.wav",
            ),
        ):
            result = batch.build_transcript(meta, ticket, api_key="freshdesk-key")

        self.assertEqual(result.status, "transcribed")
        self.assertIn("[Transcript source: audio transcription]", result.text)
        self.assertIn("Please return my call about invoice 456.", result.text)
        category, route, _ = batch.classify(result.text, meta)
        self.assertEqual(category, "Billing / Invoice Support")
        self.assertEqual(route, "aphelp@vixxo.com")

    def test_process_ticket_leaves_open_when_required_transcription_fails(self) -> None:
        calls: list[tuple[str, str, dict | None]] = []

        def fake_http_json(method: str, path: str, api_key: str, body: dict | None = None) -> dict | None:
            calls.append((method, path, body))
            if method == "GET":
                return sample_ticket()
            return {}

        with (
            patch.object(batch, "http_json", side_effect=fake_http_json),
            patch.object(
                batch,
                "build_transcript",
                return_value=batch.TranscriptResult(
                    text="",
                    source="audio transcription",
                    status="failed",
                    error="no transcription provider configured",
                    attachment_name="voicemail_15555550123.wav",
                ),
            ),
            patch.dict("os.environ", {"SP_VOICEMAIL_REQUIRE_TRANSCRIPTION": "1"}, clear=False),
        ):
            result = batch.process_ticket("freshdesk-key", sample_ticket())

        self.assertEqual(result.category, "Not triaged")
        self.assertEqual(result.forward, "skipped:transcription_failed")
        self.assertEqual(result.resolve, "open")
        self.assertIn("transcription:no transcription provider configured", result.error)
        self.assertIn(("POST", "/api/v2/tickets/12345/notes", calls[1][2]), calls)
        self.assertFalse(any(call[1].endswith("/forward") for call in calls))
        self.assertFalse(any(call[0] == "PUT" for call in calls))


if __name__ == "__main__":
    unittest.main()
