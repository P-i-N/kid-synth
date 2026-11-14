import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const src = html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const { route, velGain, knobNote, ANIMALS, isBlack, keyX, stickValue, octaveShift } =
  new Function(src + '; return {route, velGain, knobNote, ANIMALS, isBlack, keyX, stickValue, octaveShift}')();

test('key down and up', () => {
  assert.deepEqual(route([0x90, 60, 100]), { type: 'key', note: 60, on: true, vel: 100 });
  assert.deepEqual(route([0x80, 60, 0]), { type: 'key', note: 60, on: false, vel: 0 });
});

test('note-on with velocity 0 is a key up', () => {
  assert.deepEqual(route([0x90, 60, 0]), { type: 'key', note: 60, on: false, vel: 0 });
});

test('pad notes on both banks and any channel', () => {
  assert.deepEqual(route([0x90, 23, 90]), { type: 'pad', index: 0 });
  assert.deepEqual(route([0x90, 30, 90]), { type: 'pad', index: 7 });
  assert.deepEqual(route([0x99, 31, 90]), { type: 'pad', index: 0 });
  assert.deepEqual(route([0x90, 38, 90]), { type: 'pad', index: 7 });
});

test('notes just outside the pad range are keys', () => {
  assert.equal(route([0x90, 22, 90]).type, 'key');
  assert.equal(route([0x90, 39, 90]).type, 'key');
});

test('pad release makes nothing', () => {
  assert.equal(route([0x80, 23, 0]), null);
  assert.equal(route([0x90, 23, 0]), null);
});

test('program change plays an animal', () => {
  assert.deepEqual(route([0xC0, 9]), { type: 'pad', index: 1 });
});

test('knobs', () => {
  assert.deepEqual(route([0xB0, 1, 0]), { type: 'knob', index: 0, value: 0 });
  assert.deepEqual(route([0xB0, 8, 127]), { type: 'knob', index: 7, value: 127 });
  assert.equal(route([0xB0, 64, 127]), null);
});

test('bank B pads in controller mode play animals on press only', () => {
  assert.deepEqual(route([0xB0, 9, 127]), { type: 'pad', index: 0 });
  assert.deepEqual(route([0xB0, 16, 1]), { type: 'pad', index: 7 });
  assert.equal(route([0xB0, 9, 0]), null);
});

test('pitch bend', () => {
  assert.equal(route([0xE0, 0, 64]).value, 0);
  assert.equal(route([0xE0, 0, 0]).value, -1);
  assert.ok(Math.abs(route([0xE0, 127, 127]).value - 1) < 0.001);
});

test('junk is ignored', () => {
  for (const b of [[], [0xF8], [0x90], [0x90, 60], [0xF0, 1, 2, 0xF7], [0xB0, 1], [0xC0], [0xE0, 0]]) {
    assert.equal(route(b), null);
  }
});

test('loudness stays in a narrow band', () => {
  assert.equal(velGain(1), 0.55);
  assert.equal(velGain(127), 0.8);
  assert.equal(velGain(999), 0.8);
  assert.equal(velGain(-5), 0.55);
  assert.ok(velGain(64) > 0.55 && velGain(64) < 0.8);
});

test('knobs play a five-note scale', () => {
  const pc = new Set([0, 2, 4, 7, 9]);
  for (let k = 0; k < 8; k++) for (let v = 0; v <= 127; v++) assert.ok(pc.has(knobNote(k, v) % 12));
  assert.ok(knobNote(0, 127) > knobNote(0, 0));
  assert.equal(knobNote(0, 60), knobNote(0, 61)); // ±1 jitter stays on the same note
});

test('bottom-row knobs sit an octave below the top row', () => {
  assert.equal(knobNote(0, 0), 60);
  assert.equal(knobNote(4, 0), 48);
});

test('eight animals in pad order', () => {
  assert.deepEqual(ANIMALS.map(a => a.name),
    ['cow', 'sheep', 'cat', 'dog', 'duck', 'rooster', 'horse', 'frog']);
  for (const a of ANIMALS) assert.ok(a.emoji);
});

test('black keys of the 25-key keyboard', () => {
  const black = [];
  for (let n = 48; n <= 72; n++) if (isBlack(n)) black.push(n);
  assert.deepEqual(black, [49, 51, 54, 56, 58, 61, 63, 66, 68, 70]);
});

test('a key sits at its place across the keyboard', () => {
  assert.equal(keyX(48), 0.5 / 15);          // first white key
  assert.equal(keyX(49), 1 / 15);            // black key on the edge of two whites
  assert.equal(keyX(72), 14.5 / 15);         // last white key
  for (let n = 49; n <= 72; n++) assert.ok(keyX(n) > keyX(n - 1));
});

test('notes beyond the keyboard sit at its nearest edge', () => {
  assert.equal(keyX(0), keyX(48));
  assert.equal(keyX(47), keyX(48));
  assert.equal(keyX(73), keyX(72));
  assert.equal(keyX(127), keyX(72));
});

test('the joystick sideways reads like a knob resting at its middle', () => {
  assert.equal(stickValue(-1), 0);
  assert.equal(stickValue(0), 64);
  assert.equal(stickValue(1), 127);
  assert.equal(stickValue(-7), 0);
  assert.equal(stickValue(7), 127);
  for (let i = -20; i < 20; i++) assert.ok(stickValue((i + 1) / 20) >= stickValue(i / 20));
});

test('notes inside the keyboard mean the octave buttons are untouched', () => {
  for (const n of [48, 60, 72]) assert.equal(octaveShift(0, n), 0);
});

test('a note beyond the keyboard reveals how far the octave buttons moved it', () => {
  assert.equal(octaveShift(0, 73), 1);
  assert.equal(octaveShift(0, 84), 1);
  assert.equal(octaveShift(0, 85), 2);
  assert.equal(octaveShift(0, 47), -1);
  assert.equal(octaveShift(0, 36), -1);
  assert.equal(octaveShift(0, 35), -2);
  assert.equal(octaveShift(-2, 100), 3);
});

test('the octave guess stays until a note contradicts it', () => {
  assert.equal(octaveShift(1, 60), 1);    // 60–84 all fit one octave up
  assert.equal(octaveShift(1, 84), 1);
  assert.equal(octaveShift(1, 59), 0);
  assert.equal(octaveShift(-1, 36), -1);
  assert.equal(octaveShift(-1, 61), 0);
});

test('with the octave taken out, every note lands on the 25 keys', () => {
  for (let shift = -4; shift <= 4; shift++) {
    for (let key = 48; key <= 72; key++) {
      const note = key + 12 * shift;
      if (note < 0 || note > 127) continue;
      const guess = octaveShift(shift, note);
      assert.equal(note - 12 * guess, key);
    }
  }
  for (let note = 0; note <= 127; note++) {
    const key = note - 12 * octaveShift(0, note);
    assert.ok(key >= 48 && key <= 72, `note ${note} → ${key}`);
  }
});
