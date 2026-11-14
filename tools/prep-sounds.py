#!/usr/bin/env python3
"""Cut, level and encode the animal clips into sounds/.

    python3 tools/prep-sounds.py [CACHE_DIR]

Downloads each source recording (unless it is already in CACHE_DIR), takes the
slice listed below, matches its loudness to the others, limits its peaks and
writes sounds/<n>-<animal>.ogg. Needs ffmpeg. Run tools/embed-sounds.py after.
The originals stay in CACHE_DIR, outside the repo. Licences: see CREDITS.md.
"""
import array, math, pathlib, subprocess, sys, tempfile, urllib.request

# animal, source recording, slice start and end in seconds.
# Each slice starts right where the animal does: a pad that is hit must be heard at once.
SOURCES = [
    ('cow',     'https://bigsoundbank.com/UPLOAD/ogg/2384.ogg', 0.82, 2.80),
    ('sheep',   'https://upload.wikimedia.org/wikipedia/commons/1/13/Sheep_bleating.ogg', 5.61, 7.35),
    ('cat',     'https://bigsoundbank.com/UPLOAD/ogg/1472.ogg', 0.12, 0.97),
    ('dog',     'https://bigsoundbank.com/UPLOAD/ogg/2954.ogg', 2.43, 3.30),
    ('duck',    'https://bigsoundbank.com/UPLOAD/ogg/0276.ogg', 17.98, 20.40),
    ('rooster', 'https://upload.wikimedia.org/wikipedia/commons/0/0d/Medium_rooster_crowing.ogg', 2.85, 5.35),
    ('horse',   'https://upload.wikimedia.org/wikipedia/commons/d/db/Wiehern.ogg', 0.09, 2.27),
    ('frog',    'https://bigsoundbank.com/UPLOAD/ogg/0819.ogg', 2.32, 3.80),
]

RATE = 44100
LOUDNESS_DB = -16.0   # loudest 400 ms of every clip is brought to this level
PEAK = 0.7            # limiter ceiling, about -3 dBFS

ROOT = pathlib.Path(__file__).resolve().parent.parent


def ffmpeg(*args, capture=False):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], capture_output=capture, check=True)
    return r.stdout if capture else None


def loudest_window_db(pcm, window=int(RATE * 0.4)):
    """RMS of the loudest 400 ms, in dBFS, of mono 16-bit samples."""
    a = array.array('h')
    a.frombytes(pcm[:len(pcm) // 2 * 2])
    best = 1.0
    for i in range(0, max(1, len(a) - window + 1), window // 4):
        chunk = a[i:i + window]
        best = max(best, math.sqrt(sum(x * x for x in chunk) / len(chunk)))
    return 20 * math.log10(best / 32768)


def main():
    cache = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(tempfile.gettempdir()) / 'kid-synth-src'
    cache.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / 'sounds'
    out_dir.mkdir(exist_ok=True)
    for n, (name, url, start, end) in enumerate(SOURCES):
        src = cache / f'{n}-{name}.ogg'
        if not src.exists():
            req = urllib.request.Request(url, headers={'User-Agent': 'kid-synth-prep/1.0'})
            src.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        dur = end - start
        fade = min(0.3, dur * 0.25)
        shape = (f'atrim={start}:{end},asetpts=PTS-STARTPTS,highpass=f=70,'
                 f'afade=t=in:d=0.01,afade=t=out:st={dur - fade:.3f}:d={fade:.3f}')
        common = ['-i', str(src), '-ac', '1', '-ar', str(RATE)]
        pcm = ffmpeg(*common, '-af', shape, '-f', 's16le', '-', capture=True)
        gain = LOUDNESS_DB - loudest_window_db(pcm)
        dst = out_dir / f'{n}-{name}.ogg'
        ffmpeg(*common, '-af',
               f'{shape},volume={gain:.2f}dB,alimiter=limit={PEAK}:level=disabled:attack=2:release=40',
               '-c:a', 'libvorbis', '-q:a', '3', str(dst))
        print(f'{dst.name:16} {dur:4.2f} s  gain {gain:+5.1f} dB  {dst.stat().st_size / 1024:5.1f} kB')


if __name__ == '__main__':
    main()
