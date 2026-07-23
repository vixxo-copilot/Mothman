import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
PARENT_SCRIPTS = SKILLS / "sp-voicemail-triage" / "scripts"
INBOUND_SCRIPTS = SKILLS / "sp-inbound-vetting" / "scripts"
FAST_WRAPPER = SKILLS / "sp-voicemail-triage-fast" / "scripts" / "batch_process_freshdesk.py"
QSIAP_RUNNER = INBOUND_SCRIPTS / "live_run_qsiap_voicemails.py"


def load_module(name: str, path: Path, extra_paths: list[Path] | None = None):
    for extra in reversed(extra_paths or []):
        sys.path.insert(0, str(extra))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class FastWrapperArgsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fast = load_module("sp_voicemail_fast_wrapper_test", FAST_WRAPPER)

    def test_qsiap_is_enabled_by_default(self):
        self.assertTrue(self.fast._qsiap_enabled([]))
        self.assertTrue(self.fast._qsiap_enabled(["--dry-run", "--no-email"]))

    def test_no_qsiap_flag_disables_qsiap_path(self):
        self.assertFalse(self.fast._qsiap_enabled(["--no-qsiap"]))

    def test_parent_argv_removes_wrapper_only_flags(self):
        self.assertEqual(
            self.fast._parent_argv(
                ["--dry-run", "--no-email", "--no-qsiap", "--qsiap-only", "--qsiap-re-vet"]
            ),
            ["--dry-run", "--no-email"],
        )

    def test_qsiap_only_and_revet_flags_are_detected(self):
        self.assertTrue(self.fast._qsiap_only(["--qsiap-only"]))
        self.assertTrue(self.fast._qsiap_re_vet(["--qsiap-re-vet"]))


class QsiapRunnerTest(unittest.TestCase):
    def setUp(self):
        self.qsiap = load_module(
            "live_run_qsiap_voicemails_test",
            QSIAP_RUNNER,
            [PARENT_SCRIPTS, INBOUND_SCRIPTS],
        )

    def test_run_qsiap_voicemails_builds_dry_run_summary_without_writes(self):
        self.qsiap.load_credentials = lambda: "api-key"
        self.qsiap.gateway_health_check = lambda: {"ok": True}
        self.qsiap.discover_qsiap_voicemails = lambda _api: [
            {"id": 1001, "tags": []},
            {"id": 1002, "tags": ["sp-vetted"]},
            {"id": 74250, "tags": []},
        ]
        built: list[tuple[int, bool, bool]] = []

        def build_item(ticket, _api, *, transcribe=True, gateway_available=True):
            built.append((int(ticket["id"]), transcribe, gateway_available))
            return {"ticket_id": int(ticket["id"]), "posture": "Known SP — matched"}

        self.qsiap.build_item = build_item
        self.qsiap.apply_qsiap_item = lambda _api, item: (_ for _ in ()).throw(
            AssertionError(f"unexpected live write for {item['ticket_id']}")
        )

        summary = self.qsiap.run_qsiap_voicemails(
            skip={74250},
            re_vet=False,
            dry_run=True,
            transcribe=True,
        )

        self.assertEqual(summary["mode"], "dry-run")
        self.assertEqual(summary["discovered"], 3)
        self.assertEqual(summary["vetted"], 1)
        self.assertEqual(summary["skipped_ids"], [74250])
        self.assertEqual(summary["known_sp"], 1)
        self.assertEqual(built, [(1001, True, True)])
        self.assertEqual(summary["results"], [{"ticket_id": 1001, "posture": "Known SP — matched", "dry_run": True}])

    def test_run_qsiap_voicemails_skips_gateway_lookup_when_probe_fails(self):
        self.qsiap.load_credentials = lambda: "api-key"
        self.qsiap.gateway_health_check = lambda: {"ok": False, "error": "probe failed"}
        self.qsiap.discover_qsiap_voicemails = lambda _api: [{"id": 1001, "tags": []}]
        built: list[bool] = []

        def build_item(ticket, _api, *, transcribe=True, gateway_available=True):
            built.append(gateway_available)
            return {"ticket_id": int(ticket["id"]), "posture": "Unknown / Not in systems"}

        self.qsiap.build_item = build_item

        summary = self.qsiap.run_qsiap_voicemails(dry_run=True)

        self.assertEqual(built, [False])
        self.assertEqual(summary["gateway_health"], {"ok": False, "error": "probe failed"})

    def test_write_summary_persists_qsiap_json(self):
        with TemporaryDirectory() as tmp:
            self.qsiap.OUT_DIR = Path(tmp)
            out = self.qsiap.write_summary({"mode": "dry-run", "discovered": 0})

            self.assertTrue(out.is_file())
            self.assertIn("live-run-qsiap-voicemails-", out.name)
            self.assertIn('"discovered": 0', out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
