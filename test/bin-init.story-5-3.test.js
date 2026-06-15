const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const initModule = require('../bin/init');

const repoRoot = path.resolve(__dirname, '..');

test('loadActiveMcpServerKeys returns active keys in JSON order', () => {
  const keys = initModule.loadActiveMcpServerKeys();
  assert.deepEqual(keys.slice(0, 5), ['linear', 'github', 'microsoft-365', 'salesforce', 'gong']);
});

test('runSkillsInstall invokes npx skills add once on success', () => {
  let callCount = 0;
  const calls = [];
  const result = initModule.runSkillsInstall(
    {},
    {
      spawnSyncImpl(command, args, options) {
        callCount += 1;
        calls.push({ command, args, stdio: options.stdio });
        return { status: 0, signal: null, error: null };
      }
    }
  );

  assert.equal(callCount, 1);
  assert.equal(result.status, 'PASS');
  assert.equal(calls[0].command, 'npx');
  assert.deepEqual(calls[0].args, ['skills', 'add', 'vixxo-copilot/agent-skills']);
  assert.equal(calls[0].stdio, 'inherit');
});

test('runSkillsInstall returns deterministic failure for ENOENT', () => {
  const result = initModule.runSkillsInstall(
    {},
    {
      spawnSyncImpl() {
        return { error: { code: 'ENOENT' }, signal: null, status: null };
      }
    }
  );

  assert.equal(result.status, 'FAIL');
  assert.match(result.reason, /ENOENT/);
  assert.match(result.remediation, /npx skills add vixxo-copilot\/agent-skills/);
});

test('runSkillsInstall returns deterministic failure for signal and non-zero exit', () => {
  const signalResult = initModule.runSkillsInstall(
    {},
    {
      spawnSyncImpl() {
        return { error: null, signal: 'SIGTERM', status: null };
      }
    }
  );
  assert.equal(signalResult.status, 'FAIL');
  assert.match(signalResult.reason, /SIGTERM/);

  const statusResult = initModule.runSkillsInstall(
    {},
    {
      spawnSyncImpl() {
        return { error: null, signal: null, status: 3 };
      }
    }
  );
  assert.equal(statusResult.status, 'FAIL');
  assert.match(statusResult.reason, /status 3/);
});

test('validateStory53FixturePayload rejects malformed payloads', () => {
  assert.throws(
    () => initModule.validateStory53FixturePayload({ mcpResults: {} }),
    /skillsInstall/
  );
  assert.throws(
    () =>
      initModule.validateStory53FixturePayload({
        skillsInstall: { status: 'PASS' },
        mcpResults: { linear: { status: 'MAYBE' } }
      }),
    /status/
  );
});

test('loadStory53FixtureIfPresent loads and validates payload', () => {
  fs.mkdirSync(path.join(repoRoot, 'tmp'), { recursive: true });
  const fixtureDir = fs.mkdtempSync(path.join(repoRoot, 'tmp', 'story-5-3-fixture-'));
  const fixturePath = path.join(fixtureDir, 'fixture.json');
  fs.writeFileSync(
    fixturePath,
    JSON.stringify({
      skillsInstall: { status: 'PASS' },
      mcpResults: {
        linear: { status: 'PASS' },
        github: { status: 'FAIL', reason: 'missing token' }
      }
    }),
    'utf8'
  );

  const payload = initModule.loadStory53FixtureIfPresent({
    [initModule.STORY_5_3_FIXTURE_ENV_VAR]: path.relative(repoRoot, fixturePath)
  });
  assert.equal(payload.skillsInstall.status, 'PASS');
  assert.equal(payload.mcpResults.github.status, 'FAIL');

  fs.rmSync(fixtureDir, { recursive: true, force: true });
});

test('summarizePostWizard returns non-zero when any check fails', () => {
  const summary = initModule.summarizePostWizard(
    { status: 'PASS', reason: 'ok', remediation: '' },
    [
      { server_key: 'linear', status: 'PASS', reason: 'ok', remediation: 'n/a' },
      { server_key: 'github', status: 'FAIL', reason: 'bad token', remediation: 'export GITHUB_PERSONAL_ACCESS_TOKEN' }
    ]
  );

  assert.equal(summary.exitCode, 1);
  assert.equal(summary.passCount, 1);
  assert.equal(summary.failCount, 1);
  assert.deepEqual(summary.failingKeys, ['github']);
});

test('verifyActiveMcps can use deterministic fixture outcomes', () => {
  const results = initModule.verifyActiveMcps(
    {},
    {
      activeKeys: ['linear', 'github'],
      fixture: {
        skillsInstall: { status: 'PASS' },
        mcpResults: {
          linear: { status: 'PASS', reason: 'fixture pass' },
          github: { status: 'FAIL', reason: 'fixture fail' }
        }
      }
    }
  );

  assert.equal(results.length, 2);
  assert.equal(results[0].server_key, 'linear');
  assert.equal(results[0].status, 'PASS');
  assert.equal(results[1].server_key, 'github');
  assert.equal(results[1].status, 'FAIL');
});

test('verifyActiveMcps fails known keys with malformed server config', () => {
  const results = initModule.verifyActiveMcps(
    {
      GITHUB_PERSONAL_ACCESS_TOKEN: 'token',
      GONG_ACCESS_KEY: 'key',
      GONG_ACCESS_KEY_SECRET: 'secret'
    },
    {
      activeKeys: ['microsoft-365', 'github', 'salesforce', 'gong'],
      mcpServers: {
        'microsoft-365': null,
        github: null,
        salesforce: null,
        gong: null
      },
      spawnSyncImpl() {
        return { error: null, signal: null, status: 0 };
      }
    }
  );

  assert.equal(results.length, 4);
  for (const result of results) {
    assert.equal(result.status, 'FAIL');
    assert.match(result.reason, /config missing object entry/);
  }
});

test('normalizeProbeStatus treats unknown states as FAIL', () => {
  assert.equal(initModule.normalizeProbeStatus('PASS'), 'PASS');
  assert.equal(initModule.normalizeProbeStatus('FAIL'), 'FAIL');
  assert.equal(initModule.normalizeProbeStatus('UNKNOWN'), 'FAIL');
});

