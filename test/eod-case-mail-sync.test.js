/**
 * Smoke tests for EOD SF Case Email Sync runner helpers.
 * Runs the Python module's summarize_* functions via a tiny inline harness.
 */
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");

const SCRIPT = path.join(
  __dirname,
  "..",
  ".agents",
  "skills",
  "sf-case-email-sync",
  "scripts",
  "eod_case_mail_sync.py",
);

describe("eod_case_mail_sync.py", () => {
  it("parses --help and exits 0", () => {
    const r = spawnSync("python3", [SCRIPT, "--help"], { encoding: "utf8" });
    assert.equal(r.status, 0, r.stderr);
    assert.match(r.stdout, /dry-run/);
    assert.match(r.stdout, /high\/medium/);
  });

  it("summarize_plan counts high/medium and skips manual_review", () => {
    const harness = `
import json, sys
sys.path.insert(0, ${JSON.stringify(path.dirname(SCRIPT))})
from eod_case_mail_sync import summarize_plan
plan = {
  "cases_scanned": 2,
  "cases": [
    {
      "case_number": "6911",
      "subject": "CarMax",
      "status": "Working",
      "matched_messages": [
        {"confidence": "high"},
        {"confidence": "medium"},
      ],
      "manual_review": [{"confidence": "low"}],
    },
    {
      "case_number": "5784",
      "subject": "Economy Lock",
      "status": "New",
      "matched_messages": [],
      "manual_review": [],
    },
  ],
  "summary": {"matched_messages": 2},
}
print(json.dumps(summarize_plan(plan)))
`;
    const r = spawnSync("python3", ["-c", harness], { encoding: "utf8" });
    assert.equal(r.status, 0, r.stderr);
    const stats = JSON.parse(r.stdout);
    assert.equal(stats.matched_high_medium, 2);
    assert.equal(stats.matched_high, 1);
    assert.equal(stats.matched_medium, 1);
    assert.equal(stats.manual_review_skipped, 1);
    assert.equal(stats.cases_with_hits, 1);
  });
});
