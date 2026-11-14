# kid-synth

A calm sound-and-picture toy for a toddler at an Akai MPK mini. One HTML file,
no install, no network.

- **Keys** play a soft electric piano. Each press lights its key and sends up one slow bloom of colour.
- **Pads** play eight animals: cow, sheep, cat, dog on the bottom row, duck, rooster, horse, frog on the top row. Both pad banks play the same animals.
- **Knobs** are eight small melodic toys (music box, marimba, water drop, bell and so on). They play while turned and are silent when still.
- **Joystick** left and right bends held notes a little.

Hard hits are barely louder than soft ones, and the output has a fixed ceiling.
Nothing on screen moves unless the child does something.

## Run it

Browsers only give MIDI access to a served page, not to a file opened from disk:

```bash
python3 -m http.server 8377
```

Then open <http://localhost:8377>, click the play button once, and allow MIDI
when the browser asks (Firefox asks once per site). The small slider in the
top-right corner is the volume; the button next to it is full screen.

Without a keyboard, the on-screen keys, pads and knobs work with the mouse or a
finger. Drag a knob up or down to turn it.

## Keyboard setup it expects

The MPK mini mk2's factory layout: pads send notes 23–38, knobs send
controllers 1–8. Notes 23–38 always play animals, so if the octave buttons
shift the keys down two octaves, the lowest keys play animals too.

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

## Credits

Animal recordings: see [CREDITS.md](CREDITS.md). Everything else is public
domain ([LICENSE](LICENSE)).
