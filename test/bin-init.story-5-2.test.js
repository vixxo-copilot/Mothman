const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const initModule = require('../bin/init');

const repoRoot = path.resolve(__dirname, '..');

test('parseCanonicalMcpKeysFromDocs returns expected ordered keys', () => {
  const docsContent = fs.readFileSync(initModule.MCPS_DOC_PATH, 'utf8');
  const keys = initModule.parseCanonicalMcpKeysFromDocs(docsContent);
  assert.ok(keys.length >= 5);
  assert.deepEqual(keys.slice(0, 5), ['linear', 'github', 'microsoft-365', 'salesforce', 'gong']);
  assert.equal(new Set(keys).size, keys.length);
  assert.ok(keys.includes('introspection'));
});

test('prompt schema is deterministic and conditional', () => {
  const canonical = ['linear', 'github'];
  const withoutOverwrite = initModule.promptSchema(canonical, false);
  assert.deepEqual(
    withoutOverwrite.map((question) => question.name),
    ['employeeName', 'employeeEmail', 'employeeRole', 'optionalMcps']
  );

  const withOverwrite = initModule.promptSchema(canonical, true);
  assert.deepEqual(
    withOverwrite.map((question) => question.name),
    ['employeeName', 'employeeEmail', 'employeeRole', 'optionalMcps', 'overwriteEnv']
  );
  assert.equal(withOverwrite[4].initial, false);
});

test('normalizeWizardAnswers enforces deterministic mapping and MCP order', () => {
  const canonical = ['linear', 'github', 'salesforce'];
  const normalized = initModule.normalizeWizardAnswers(
    {
      employeeName: '  Jane   Doe  ',
      employeeEmail: '  JANE.DOE@VIXXO.COM  ',
      employeeRole: ' Senior  Software Engineer ',
      optionalMcps: ['salesforce', 'linear', 'linear']
    },
    canonical
  );

  assert.equal(normalized.employeeName, 'Jane Doe');
  assert.equal(normalized.employeeEmail, 'jane.doe@vixxo.com');
  assert.equal(normalized.employeeRole, 'Senior Software Engineer');
  assert.equal(normalized.department, 'Engineering');
  assert.equal(normalized.manager, 'Engineering Manager (TBD)');
  assert.deepEqual(normalized.optionalMcps, ['linear', 'salesforce']);
});

test('renderers produce newline-terminated, placeholder-free output', () => {
  const profile = {
    employeeName: 'Taylor Avery',
    employeeRole: 'Product Manager',
    employeeEmail: 'taylor.avery@vixxo.com',
    department: 'Product',
    manager: 'Product Manager (TBD)',
    optionalMcps: ['linear', 'github']
  };

  const identity = initModule.renderIdentityMarkdown(profile);
  const persona = initModule.renderWorkPersonaMarkdown(profile);

  assert.ok(identity.endsWith('\n'));
  assert.ok(persona.endsWith('\n'));
  assert.match(identity, /## Optional MCPs/);
  assert.match(identity, /- linear/);
  assert.match(identity, /- github/);
  assert.doesNotMatch(identity, /\{\{employee_/);
  assert.doesNotMatch(persona, /\{\{employee_/);
});

test('renderers escape quoted yaml scalar values', () => {
  const profile = {
    employeeName: 'Alex "Ace" Dev',
    employeeRole: 'Ops \\ Platform',
    employeeEmail: 'alex.ace@vixxo.com',
    department: 'Operations',
    manager: 'Ops "Lead" (TBD)',
    optionalMcps: ['linear']
  };

  const identity = initModule.renderIdentityMarkdown(profile);
  const persona = initModule.renderWorkPersonaMarkdown(profile);

  assert.match(identity, /name: "Alex \\"Ace\\" Dev"/);
  assert.match(identity, /role: "Ops \\\\ Platform"/);
  assert.match(identity, /manager: "Ops \\"Lead\\" \(TBD\)"/);
  assert.match(persona, /name: "Alex \\"Ace\\" Dev"/);
});

test('assertPathInsideRepo rejects traversal escapes', () => {
  assert.throws(() => initModule.assertPathInsideRepo('../outside.md'), /path escapes repository root/);
  assert.doesNotThrow(() => initModule.assertPathInsideRepo('memory/me/identity.md'));
});

test('loadFixtureResponsesIfPresent validates shape and maps injected error tokens', () => {
  fs.mkdirSync(path.join(repoRoot, 'tmp'), { recursive: true });
  const fixtureDir = fs.mkdtempSync(path.join(repoRoot, 'tmp', 'story-5-2-fixture-'));
  const fixturePath = path.join(fixtureDir, 'fixture.json');
  fs.writeFileSync(
    fixturePath,
    JSON.stringify({
      responses: ['Alex Doe', 'alex@vixxo.com', 'Engineering Manager', ['linear'], { type: 'error', message: 'stop' }]
    }),
    'utf8'
  );

  const env = { [initModule.FIXTURE_ENV_VAR]: path.relative(repoRoot, fixturePath) };
  const responses = initModule.loadFixtureResponsesIfPresent(env);
  assert.equal(responses.length, 5);
  assert.equal(responses[0], 'Alex Doe');
  assert.ok(responses[4] instanceof Error);
  assert.equal(responses[4].code, 'WIZARD_CANCELLED');
  assert.equal(responses[4].message, 'stop');
  assert.doesNotThrow(() => initModule.validateFixtureResponses(responses, true));
  assert.throws(
    () => initModule.validateFixtureResponses(responses.slice(0, 3), false),
    /responses\[3\] required/
  );
  assert.doesNotThrow(() =>
    initModule.validateFixtureResponses(
      ['Alex Doe', 'alex@vixxo.com', 'Engineering Manager', Object.assign(new Error('cancel'), { code: 'WIZARD_CANCELLED' })],
      true
    )
  );
  assert.throws(
    () => initModule.validateFixtureResponses(['Alex Doe', 'alex@vixxo.com', 'Engineering Manager', ['linear']], true),
    /responses\[4\] required/
  );

  const invalidPath = path.join(fixtureDir, 'invalid.json');
  fs.writeFileSync(invalidPath, JSON.stringify({ notResponses: [] }), 'utf8');
  assert.throws(
    () => initModule.loadFixtureResponsesIfPresent({ [initModule.FIXTURE_ENV_VAR]: path.relative(repoRoot, invalidPath) }),
    /missing responses array/
  );

  fs.rmSync(fixtureDir, { recursive: true, force: true });
});

