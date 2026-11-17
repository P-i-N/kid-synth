# kid-synth

A calm sound-and-picture toy for a toddler at an Akai MPK mini. One HTML file,
no install, no network.

- **Keys** play a soft electric piano. Each press lights its key and sends up one slow bloom of colour.
- **Pads** play eight animals: cow, sheep, cat, dog on the bottom row, duck, rooster, horse, frog on the top row. Both pad banks play the same animals.
- **Knobs** are eight small melodic toys (music box, marimba, water drop, bell and so on). They play while turned and are silent when still.
- **Joystick** left and right plays a harp, like a ninth knob that springs back. Up and down plays knob 1.

Hard hits are barely louder than soft ones, and the output has a fixed ceiling.
Nothing on screen moves unless the child does something.

## Run it

Open <https://p-i-n.github.io/kid-synth/>, click the play button once, and allow
MIDI when the browser asks.

Or run it from this folder:

```bash
python3 play.py
```

That serves the folder to this machine only and opens <http://localhost:8377>
in the browser; Ctrl+C stops it. Click the play button once and allow MIDI when
the browser asks (Firefox asks once per address). The small slider in the
top-right corner is the volume; the button next to it is full screen.

Opening `index.html` itself (double-clicking it) shows the toy and it plays with
the mouse, but it cannot reach the keyboard: browsers give no MIDI to a page
opened as a file. Firefox does not offer Web MIDI there at all.

Without a keyboard, the on-screen keys, pads and knobs work with the mouse or a
finger. Drag a knob up or down to turn it.

If the keyboard is unplugged and plugged back in, it should play again within a
few seconds. If it does not, reload the page and click play.

A held key fades out by itself after a few seconds, like a piano string, so a
key that is leaned on (or a key-up that gets lost) never drones.

## Keyboard setup it expects

An MPK mini mk2 in either of two layouts:

- **Factory layout:** pads send notes 23–38 on the keys' channel, knobs send
  controllers 1–8, joystick left/right sends pitch bend.
- **Toddler program** (below): the same, but with the pads on channel 10.

The app tells them apart by itself: the first pad hit on channel 10 settles it
until the page is reloaded.

## Toddler program for the keyboard

A toddler presses every button. `tools/mpk-program.py` writes one program into
all four of the keyboard's stored programs, so most buttons stop mattering
(Linux, needs `alsa-utils`; works while the browser has the keyboard open):

```bash
python3 tools/mpk-program.py write
```

It first saves the keyboard's own four programs to `keyboard-backup/` (kept out
of git, never overwritten), then writes and reads back each one. To undo:

```bash
python3 tools/mpk-program.py restore
```

`python3 tools/mpk-program.py show` prints what the keyboard holds.

What each button then does to the toy, and what it does without the program:

| button | with the toddler program | with the factory layout |
|--------|--------------------------|-------------------------|
| OCT − / OCT + | Nothing: the same key plays and lights the same note in any octave. | The same, except that shifted down, the lowest keys play animals (they send the pads' notes). |
| BANK A/B | Nothing: both banks play the same animals. | The same. |
| FULL LEVEL | Nothing: hit strength barely changes loudness anyway. | The same. |
| PROG CHANGE | Nothing: pads still play animals. | The same. |
| CC | Nothing: pads still play animals. | Bank A pads play knob sounds instead. |
| PROG SELECT + pad | Nothing: all four programs are the same. It also resets the octave and switches the arpeggiator off. | Loads another program; two of the factory ones start a latched arpeggio. |
| ARP ON/OFF, NOTE REPEAT | Repeats a held key or pad once every two seconds. | Repeats several times a second. |
| TAP TEMPO | Its light blinks once every two seconds; four taps can speed the above up again. | Blinks about twice a second. |

No program can switch a button or its light off: the keyboard has no setting
for that.

## Change an animal

1. Put the new clip in `sounds/` under the same name (`0-cow.ogg` … `7-frog.ogg`),
   or edit the source list in `tools/prep-sounds.py` and run it (needs ffmpeg).
2. Run `python3 tools/embed-sounds.py` to write the clips into `index.html`.
3. Update `CREDITS.md`. Clips must be CC0 or public domain.

To change which animal a pad shows, edit `ANIMALS` at the top of `index.html`.

## Tests

```bash
node --test test/
```

```bash
python3 -m unittest discover -s test
```

## Credits

Animal recordings: see [CREDITS.md](CREDITS.md). Everything else is public
domain ([LICENSE](LICENSE)).
