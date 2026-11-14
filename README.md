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

Or serve it yourself. Browsers only give MIDI access to a served page, not to a
file opened from disk:

```bash
python3 -m http.server 8377
```

Then open <http://localhost:8377>, click the play button once, and allow MIDI
when the browser asks (Firefox asks once per site). The small slider in the
top-right corner is the volume; the button next to it is full screen.

Without a keyboard, the on-screen keys, pads and knobs work with the mouse or a
finger. Drag a knob up or down to turn it.

If the keyboard is unplugged and plugged back in, it should play again within a
few seconds. If it does not, reload the page and click play.

A held key fades out by itself after a few seconds, like a piano string, so a
key that is leaned on (or a key-up that gets lost) never drones.

## Keyboard setup it expects

The MPK mini mk2's factory layout: pads send notes 23–38, knobs send
controllers 1–8, joystick left/right sends pitch bend.

## The keyboard's other buttons

A toddler presses everything. What each button does to the toy:

| button | effect |
|--------|--------|
| OCT − / OCT + | None on the keys: the same key plays and lights the same note in any octave. One exception: notes 23–38 are the pads' notes, so with the octave shifted down the lowest keys play animals. |
| BANK A/B | None: both banks play the same animals. |
| FULL LEVEL | None: hit strength barely changes loudness anyway. |
| PROG CHANGE | None: pads still play animals. |
| CC | Bank B pads still play animals. Bank A pads send the knobs' own controller numbers, so they play knob sounds. |
| NOTE REPEAT, ARP ON/OFF, TAP TEMPO | The keyboard repeats notes by itself while a pad or key is held. Press ARP ON/OFF to stop an arpeggio. |
| PROG SELECT + pad | Loads another of the keyboard's four stored programs, which may use other pad notes. Switch back the same way. |

The buttons' lights belong to the keyboard and cannot be switched off from here.


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
