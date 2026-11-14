import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

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

// A pad must answer at once: hit, hear. Needs ffmpeg to decode; skipped without it.
const hasFfmpeg = spawnSync('ffmpeg', ['-version']).status === 0;
test('every clip is audible within 80 ms of its start', { skip: !hasFfmpeg && 'ffmpeg not installed' }, () => {
  const names = ['cow', 'sheep', 'cat', 'dog', 'duck', 'rooster', 'horse', 'frog'];
  clips.forEach((c, i) => {
    const ogg = Buffer.from(c.split(',')[1], 'base64');
    const r = spawnSync('ffmpeg', ['-v', 'error', '-i', 'pipe:0', '-ac', '1', '-ar', '44100', '-f', 's16le', '-'],
      { input: ogg, maxBuffer: 1 << 26 });
    const pcm = new Int16Array(r.stdout.buffer, r.stdout.byteOffset, r.stdout.length >> 1);
    let peak = 0;
    for (const s of pcm) peak = Math.max(peak, Math.abs(s));
    const first = pcm.findIndex(s => Math.abs(s) >= peak * 0.25);
    assert.ok(first / 44.1 <= 80, `${names[i]}: ${Math.round(first / 44.1)} ms of lead-in`);
  });
});
