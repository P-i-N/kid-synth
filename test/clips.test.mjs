import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const block = html.match(/\/\*SOUNDS-BEGIN\*\/([\s\S]*?)\/\*SOUNDS-END\*\//)[1];
const clips = new Function(block + '; return CLIPS')();
const creditsUrl = new URL('../CREDITS.md', import.meta.url);
const credits = existsSync(creditsUrl) ? readFileSync(creditsUrl, 'utf8') : '';

test('eight embedded clips', () => {
  assert.equal(clips.length, 8);
  for (const c of clips) assert.match(c, /^data:audio\/ogg;base64,[A-Za-z0-9+/=]+$/);
});

test('each clip is an Ogg file under 80 kB', () => {
  for (const c of clips) {
    const buf = Buffer.from(c.split(',')[1], 'base64');
    assert.equal(buf.subarray(0, 4).toString('latin1'), 'OggS');
    assert.ok(buf.length < 80_000);
  }
});

test('every animal has a credit with a licence and a link', () => {
  for (const name of ['cow', 'sheep', 'cat', 'dog', 'duck', 'rooster', 'horse', 'frog']) {
    const row = credits.split('\n').find(l => l.toLowerCase().includes(`| ${name} |`));
    assert.ok(row, name);
    assert.match(row, /CC0|Public domain/);
    assert.match(row, /https:\/\//);
  }
});
