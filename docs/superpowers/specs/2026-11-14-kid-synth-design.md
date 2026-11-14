# kid-synth: design

Date: 2026-11-14. Status: waiting for approval.

## Intent

A 13-month-old sits at an Akai MPK mini and plays. Whatever they hit makes a
pleasant sound and a calm picture. It is a toy, not an instrument to learn.

## Goals

- **Keys** play a soft piano-like voice.
- **Pads** play real animal recordings, one animal per pad.
- **Knobs** make sound while they are turned.
- Every sound has a matching picture, so cause and effect are visible.
- One self-contained HTML file: no network, no install, no build needed to run.

## Non-goals

Recording, songs, lessons, a settings screen, phone layout, configuring the
keyboard itself.

## Anti-goals

These would make it a failure even if it works:

- Overstimulation: flashing, fast motion, many things moving at once, saturated colour.
- Loud surprises: a toddler bangs, so hard hits must not be loud.
- Anything that needs reading or a correct sequence to get a result.

## Constraints (found on this machine)

- The keyboard is an MPK mini mk2 (`MPKmini2`). Its current program, read from the device:
  - keys and pads both send on MIDI channel 1
  - pads send notes 23–30 (bank A) and 31–38 (bank B); in their other modes, controllers 1–16 or program changes 0–15
  - knobs send controllers 1–8, range 0–127, with end stops
  - joystick left/right sends pitch bend; up/down sends controller 1 (same as knob 1)
  - the 25 keys start at note 48 until an octave button is pressed
- Firefox is the only browser installed. It does not give MIDI access to a page opened from disk, so the file is served from `localhost`.
- The repo is public domain (Unlicense), so every clip must be CC0 or public domain.

## Approaches

1. **One hand-written HTML file (chosen).** Web Audio makes the key and knob sounds, the animal clips sit in the file as base64, a canvas draws the pictures. A small script rewrites the clip block when a clip changes. Nothing to install, easy to read, about half a megabyte.
2. **Source tree plus a bundler.** Cleaner separation, but it adds tooling to something of roughly 700 lines. Not worth it.
3. **A sampled piano or an audio library.** A more realistic piano, but several megabytes or a network dependency, which breaks "self-contained".

The how was left to the builder; approach 1 is the builder's call.

## Design

### Screen

Laid out like the keyboard itself, so a hand and its picture line up.

```
┌────────────────────────────────────────────────┐
│                                                │
│      soft colour blooms rise where a key       │
│      is played, then fade                      │
│                                                │
│    🐄  🐑  🐈  🐕          ◔  ◔  ◔  ◔        │
│    🦆  🐓  🐎  🐸          ◔  ◔  ◔  ◔        │
│                                                │
│  ▏▕▏▕▏▏▕▏▕▏▕▏▏▕▏▕▏▏▕▏▕▏▕▏  25 keys, lit while held │
└────────────────────────────────────────────────┘
```

- Dark, muted background. Nothing moves unless the child does something.
- Key: the on-screen key lights and one soft circle blooms above it, coloured by note, and fades over about two seconds.
- Pad: its animal grows gently and settles back while the clip plays.
- Knob: its ring fills to the knob's position and glows while it turns.

### Sound

- **Keys:** a synthesized soft electric-piano voice, at most eight notes at once. Hit strength changes loudness only a little.
- **Pads:** eight animals, the same on both pad banks. Planned set: cow, sheep, cat, dog, duck, rooster, horse, frog. Hitting a pad again restarts its clip; at most two animals sound together. Clips are trimmed to about two seconds and levelled.
- **Knobs:** each knob is a small melodic toy. Turning it steps through a five-note scale, so anything it plays sounds fine with the keys. Each knob has its own gentle voice (music box, marimba, water drop, kalimba, soft bell and similar). Silent when still.
- **Joystick:** left/right bends held notes slightly. Up/down acts as knob 1.
- A limiter and a fixed ceiling on the master output. A small volume control for the parent sits in a corner.

### Input

- Web MIDI, any connected device, reconnects if the cable is pulled.
- Notes 23–38 are always animals. If the octave buttons shift the keys down two octaves, the lowest keys play animals too. Accepted.
- Pads also work in their controller and program-change modes where the device allows it.
- Mouse and touch work on the on-screen keys, pads and knobs, for trying it without the keyboard.

### Starting

A parent opens the page and clicks once (browsers require a click before sound). A fullscreen button is offered. After that no further interaction with the computer is needed.

### Animal clips

- Sources: Wikimedia Commons and BigSoundBank, CC0 or public domain only. Commons alone is thin: many of its "animal" clips are people pronouncing words.
- Each clip is listed with its author, source and licence in `CREDITS.md`.
- The final animal set depends on which clips are clean; an animal without a good clip is swapped for one that has one.

## Left to the builder

- Exact voices, colours, timings.
- Animals are drawn with the system's emoji font (present on this machine).
- File layout: `index.html`, `CREDITS.md`, `tools/embed-sounds.py`, `sounds/` (source clips), README with the one-line serve command.

## Verification

- Built-in browser with simulated MIDI messages, mouse input, and the real keyboard if that browser grants MIDI.
- Not verifiable by the builder: how the clips actually sound, and MIDI permission in Firefox. Both need a person at the machine.
