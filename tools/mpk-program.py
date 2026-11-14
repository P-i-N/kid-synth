#!/usr/bin/env python3
"""Put the "toddler program" into an Akai MPK mini mk2, or take it out again.

    python3 tools/mpk-program.py show             what the keyboard holds now
    python3 tools/mpk-program.py backup [DIR]     save its four programs (never overwrites a backup)
    python3 tools/mpk-program.py write [DIR]      back up if needed, then write the toddler program
    python3 tools/mpk-program.py restore [DIR]    put the saved programs back

The keyboard holds four stored programs and the one in use ("RAM"). The toddler
program is written to all five, so PROG SELECT changes nothing. What it sets:

  - pads on MIDI channel 10, keys and knobs on channel 1, so a key can never be
    mistaken for a pad, whatever the octave buttons do
  - pads' controller and program-change numbers 24–39, clear of the knobs' 1–8
  - no octave shift, no transpose
  - arpeggiator off, unlatched, and as slow as it goes (quarter notes at 30 BPM)
    in case it is switched on: this also slows NOTE REPEAT and the tempo light

It cannot switch off any button or light: the keyboard has no setting for that.

DIR defaults to keyboard-backup/ next to this repository's index.html.
Linux only: uses aseqdump and aplaymidi (alsa-utils), which can share the
keyboard with a browser that has it open.

The format is from https://github.com/mungewell/mpd-utils (mpk_mini.py) and
from this keyboard's own replies. Offsets below count from the start of the
117-byte message.
"""
import pathlib, re, subprocess, sys, tempfile, time

HEAD = bytes.fromhex('F0 47 00 26')      # SysEx start, Akai, MPK mini mk2
SEND, REQUEST, REPLY = 0x64, 0x66, 0x67
LENGTH = 117                             # 7 header bytes, 109 of settings, 1 end byte
SLOTS = (1, 2, 3, 4)                     # 0 is the program in use, not stored

ROOT = pathlib.Path(__file__).resolve().parent.parent


# ---------- messages (pure) ----------

def _check_slot(slot):
    if slot not in (0,) + SLOTS:
        raise ValueError(f'program {slot}: the keyboard has 0 (in use) and 1–4 (stored)')


def request(slot):
    """The message that asks the keyboard for one program."""
    _check_slot(slot)
    return HEAD + bytes([REQUEST, 0x00, 0x01, slot, 0xF7])


def toddler_program(slot):
    """The message that writes the toddler program into one slot."""
    _check_slot(slot)
    settings = [
        slot,
        9,              # 8   pad channel: 10
        0,              # 9   key and knob channel: 1
        4,              # 10  octave: no shift
        0,              # 11  arpeggiator off
        0,              # 12  arpeggiator mode: up
        0,              # 13  time division: quarter notes
        0,              # 14  clock: internal
        0,              # 15  latch off
        0,              # 16  swing: none
        4,              # 17  tap tempo needs four taps
        0, 30,          # 18  tempo: 30 BPM (value = first × 128 + second)
        0,              # 20  arpeggiator range: one octave
        0, 0, 0,        # 21  joystick left/right: pitch bend
        1, 1, 1,        # 24  joystick up/down: controller 1
    ]
    for pad in range(16):
        # note, then program-change and controller number (the sources disagree on
        # their order, so both are the same), then 0 = momentary.
        settings += [23 + pad, 24 + pad, 24 + pad, 0]
    for knob in range(8):
        settings += [1 + knob, 0, 127]       # controller, lowest value, highest value
    settings.append(12)                      # 115 transpose: none
    message = HEAD + bytes([SEND, 0x00, len(settings)]) + bytes(settings) + b'\xF7'
    assert len(message) == LENGTH
    return message


def _check_program(message):
    if (len(message) != LENGTH or message[:4] != HEAD or message[4] not in (SEND, REPLY)
            or message[-1] != 0xF7 or any(b > 0x7F for b in message[1:-1])):
        raise ValueError('not a whole MPK mini mk2 program')


def as_send(program, slot):
    """Turn a program as the keyboard reported it into the message that writes it to a slot."""
    _check_program(program)
    _check_slot(slot)
    return program[:4] + bytes([SEND]) + program[5:7] + bytes([slot]) + program[8:]


def differences(a, b):
    """Offsets where two programs' settings differ. Command and slot bytes do not count."""
    _check_program(a)
    _check_program(b)
    return [i for i in range(8, LENGTH - 1) if a[i] != b[i]]


def parse_dump(text):
    """The first whole program in aseqdump's output, or None. Long messages come in pieces."""
    data = bytearray()
    for line in text.splitlines():
        m = re.search(r'System exclusive\s+((?:[0-9A-Fa-f]{2}\s*)+)$', line)
        if not m:
            continue
        data += bytes.fromhex(m.group(1))
        if data and data[-1] == 0xF7:
            if len(data) == LENGTH and data[:4] == HEAD and data[4] == REPLY:
                return bytes(data)
            data.clear()
    return None


def describe(program):
    _check_program(program)
    p = program
    pads = ' '.join(str(p[27 + 4 * i]) for i in range(16))
    second = ' '.join(str(p[28 + 4 * i]) for i in range(16))
    knobs = ' '.join(str(p[91 + 3 * i]) for i in range(8))
    return (f'pads ch {p[8] + 1}, keys ch {p[9] + 1}, octave {p[10] - 4:+d}, '
            f'arp {"on" if p[11] else "off"}, latch {"on" if p[15] else "off"}, '
            f'tempo {p[18] * 128 + p[19]}, transpose {p[115] - 12:+d}\n'
            f'    pad notes   {pads}\n    pad numbers {second}\n    knob controllers {knobs}')


# ---------- talking to the keyboard ----------

def find_port():
    out = subprocess.run(['aseqdump', '-l'], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        m = re.match(r'\s*(\d+:\d+)\s+(.*)', line)
        if m and re.search(r'mpk\s*mini', m.group(2), re.I):
            return m.group(1)
    sys.exit('No MPK mini found. Is it plugged in?')


def send(port, message):
    """Send one SysEx message through the sequencer, as a one-event MIDI file."""
    body = message[1:]
    assert len(body) < 128
    track = b'\x00\xF0' + bytes([len(body)]) + body + b'\x00\xFF\x2F\x00'
    smf = (b'MThd' + (6).to_bytes(4, 'big') + b'\x00\x00\x00\x01\x00\x60'
           + b'MTrk' + len(track).to_bytes(4, 'big') + track)
    with tempfile.NamedTemporaryFile(suffix='.mid') as f:
        f.write(smf)
        f.flush()
        subprocess.run(['aplaymidi', '-p', port, f.name], check=True, capture_output=True)


def read(port, slot, tries=3):
    """Ask for one program and wait for the answer."""
    for _ in range(tries):
        with tempfile.TemporaryFile(mode='w+') as out:
            listener = subprocess.Popen(['aseqdump', '-p', port], stdout=out, stderr=subprocess.DEVNULL)
            try:
                time.sleep(0.4)                  # let it subscribe before the reply can come
                send(port, request(slot))
                time.sleep(0.8)
            finally:
                listener.terminate()
                listener.wait()
            out.seek(0)
            program = parse_dump(out.read())
        if program is not None:
            return program
    sys.exit(f'The keyboard did not answer when asked for program {slot}.')


def backup_dir(argv):
    return pathlib.Path(argv[2]) if len(argv) > 2 else ROOT / 'keyboard-backup'


def backup(port, folder):
    files = {slot: folder / f'program-{slot}.syx' for slot in SLOTS}
    have = [f for f in files.values() if f.exists()]
    if len(have) == len(files):
        print(f'Backup already in {folder}: left untouched.')
        return
    if have:
        sys.exit(f'{folder} holds only part of a backup. Move it away and run again.')
    folder.mkdir(parents=True, exist_ok=True)
    for slot, f in files.items():
        program = read(port, slot)
        f.write_bytes(program)
        print(f'saved program {slot} → {f}\n    {describe(program)}')


def write(port, folder):
    backup(port, folder)
    for slot in SLOTS + (0,):
        wanted = toddler_program(slot)
        send(port, wanted)
        time.sleep(0.3)
        diff = differences(read(port, slot), wanted)
        name = f'program {slot}' if slot else 'program in use'
        if diff:
            sys.exit(f'{name}: the keyboard reads back differently at bytes {diff}. Stopped. '
                     f'Restore with: python3 tools/mpk-program.py restore')
        print(f'{name}: written and read back the same')


def restore(port, folder):
    programs = {}
    for slot in SLOTS:
        f = folder / f'program-{slot}.syx'
        if not f.exists():
            sys.exit(f'No backup at {f}.')
        programs[slot] = f.read_bytes()
        as_send(programs[slot], slot)            # refuse a damaged file before touching the keyboard
    for slot in SLOTS + (0,):
        saved = programs[slot or 1]              # program 1 also becomes the one in use
        send(port, as_send(saved, slot))
        time.sleep(0.3)
        diff = differences(read(port, slot), saved)
        name = f'program {slot}' if slot else 'program in use (a copy of program 1)'
        if diff:
            sys.exit(f'{name}: the keyboard reads back differently at bytes {diff}. Stopped.')
        print(f'{name}: restored')


def main(argv):
    command = argv[1] if len(argv) > 1 else ''
    if command not in ('show', 'backup', 'write', 'restore'):
        sys.exit(__doc__)
    port = find_port()
    if command == 'show':
        for slot in (0,) + SLOTS:
            print(f'{"in use" if slot == 0 else f"program {slot}"}: {describe(read(port, slot))}')
    elif command == 'backup':
        backup(port, backup_dir(argv))
    elif command == 'write':
        write(port, backup_dir(argv))
    else:
        restore(port, backup_dir(argv))


if __name__ == '__main__':
    main(sys.argv)
