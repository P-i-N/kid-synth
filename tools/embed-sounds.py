#!/usr/bin/env python3
"""Write sounds/0-*.ogg … sounds/7-*.ogg into index.html as base64.

    python3 tools/embed-sounds.py

Replaces everything between the SOUNDS-BEGIN and SOUNDS-END markers.
"""
import base64, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BEGIN, END = '/*SOUNDS-BEGIN*/', '/*SOUNDS-END*/'


def main():
    files = sorted((ROOT / 'sounds').glob('[0-7]-*.ogg'))
    if [f.name[0] for f in files] != list('01234567'):
        sys.exit(f'need exactly one clip for each of 0–7 in sounds/, found: {[f.name for f in files]}')
    page = ROOT / 'index.html'
    html = page.read_text(encoding='utf-8')
    if html.count(BEGIN) != 1 or html.count(END) != 1 or html.index(BEGIN) > html.index(END):
        sys.exit(f'index.html must contain {BEGIN} then {END}, once each')
    lines = [f'  "data:audio/ogg;base64,{base64.b64encode(f.read_bytes()).decode()}", // {f.stem}' for f in files]
    block = BEGIN + '\nconst CLIPS = [\n' + '\n'.join(lines) + '\n];\n' + END
    page.write_text(html[:html.index(BEGIN)] + block + html[html.index(END) + len(END):], encoding='utf-8')
    print(f'embedded {len(files)} clips, {sum(f.stat().st_size for f in files) / 1024:.0f} kB of audio')


if __name__ == '__main__':
    main()
