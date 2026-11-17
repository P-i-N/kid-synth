#!/usr/bin/env python3
"""Open kid-synth in the browser, the way that lets it reach the keyboard.

    python3 play.py

Browsers do not give MIDI to a page opened as a file (index.html double-clicked),
so this serves the folder on this machine only and opens http://localhost:8377/.
If that is already being served, it just opens the page. Stop it with Ctrl+C.

    python3 play.py --no-browser      serve without opening anything
"""
import functools, http.server, pathlib, socket, sys, urllib.request, webbrowser

ROOT = pathlib.Path(__file__).resolve().parent
PORTS = range(8377, 8387)     # the browser remembers its MIDI permission per port: 8377 whenever possible


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def server(port):
    """A server for this folder that only this machine can reach."""
    handler = functools.partial(Quiet, directory=str(ROOT))
    return http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)


def serves_kid_synth(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1) as reply:
            return b'<title>kid-synth</title>' in reply.read(2000)
    except (OSError, ValueError):
        return False


def state(port):
    """'ours' (already serving kid-synth), 'free', or 'other' (something else has it)."""
    if serves_kid_synth(port):
        return 'ours'
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(('127.0.0.1', port))
        except OSError:
            return 'other'
    return 'free'


def choose(state_of):
    """The first usable port and whether it is 'ours' or 'free'."""
    for port in PORTS:
        what = state_of(port)
        if what in ('ours', 'free'):
            return port, what
    sys.exit(f'Ports {PORTS[0]}–{PORTS[-1]} are all in use by something else.')


def main():
    port, what = choose(state)
    url = f'http://localhost:{port}/'
    browse = '--no-browser' not in sys.argv
    if what == 'ours':
        print(f'kid-synth is already being served at {url}')
        if browse:
            webbrowser.open(url)
        return
    httpd = server(port)
    print(f'kid-synth is at {url}   (Ctrl+C stops it)')
    if browse:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
