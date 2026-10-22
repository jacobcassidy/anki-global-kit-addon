import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { updateDevAddonName } from '../../../scripts/dev_metadata.js';

async function fixture(t) {
  const addonDirectory = await mkdtemp(join(tmpdir(), 'anki-kit-dev-metadata-'));
  t.after(() => rm(addonDirectory, { recursive: true, force: true }));
  const manifestPath = join(addonDirectory, 'manifest.json');
  const metadataPath = join(addonDirectory, 'meta.json');
  await writeFile(manifestPath, JSON.stringify({ name: 'Anki Global Kit', version: '1.1.1' }));
  return { addonDirectory, manifestPath, metadataPath };
}

test('development label follows version changes while preserving installation metadata and release manifest', async (t) => {
  const { addonDirectory, manifestPath, metadataPath } = await fixture(t);
  const saved = { disabled: true, mod: 123, config: { shortcut: 'Meta+K', note_type_selections: { custom: true } } };
  await writeFile(metadataPath, JSON.stringify({ name: 'Anki Global Kit', ...saved }));
  for (const version of ['1.1.1', '2.0.0']) {
    const manifest = JSON.stringify({ name: 'Anki Global Kit', version });
    await writeFile(manifestPath, manifest);
    await updateDevAddonName({ addonDirectory });
    assert.deepEqual(JSON.parse(await readFile(metadataPath, 'utf8')), {
      name: `Anki Global Kit (dev v${version})`,
      ...saved,
    });
    assert.equal(await readFile(manifestPath, 'utf8'), manifest);
  }
  // Repeated builds should not rewrite metadata that is already current.
  const current = JSON.stringify(JSON.parse(await readFile(metadataPath, 'utf8')));
  await writeFile(metadataPath, current);
  await updateDevAddonName({ addonDirectory });
  assert.equal(await readFile(metadataPath, 'utf8'), current);
});

test('clean builds leave local metadata absent; linking explicitly creates it', async (t) => {
  const { addonDirectory, metadataPath } = await fixture(t);
  await updateDevAddonName({ addonDirectory });
  await assert.rejects(readFile(metadataPath), { code: 'ENOENT' });
  await updateDevAddonName({ addonDirectory, create: true });
  assert.deepEqual(JSON.parse(await readFile(metadataPath, 'utf8')), { name: 'Anki Global Kit (dev v1.1.1)' });
});

test('invalid local metadata is preserved instead of replacing saved settings', async (t) => {
  const { addonDirectory, metadataPath } = await fixture(t);
  for (const contents of ['{invalid', 'null', '[]']) {
    await writeFile(metadataPath, contents);
    await assert.rejects(updateDevAddonName({ addonDirectory, create: true }));
    assert.equal(await readFile(metadataPath, 'utf8'), contents);
  }
});
