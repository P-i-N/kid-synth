"""Tests for play.py, the launcher. Run: python3 -m unittest discover -s test"""
import importlib.util, pathlib, threading, unittest, urllib.request

path = pathlib.Path(__file__).resolve().parent.parent / 'play.py'
spec = importlib.util.spec_from_file_location('play', path)
play = importlib.util.module_from_spec(spec)
spec.loader.exec_module(play)


class Launcher(unittest.TestCase):
    def setUp(self):
        self.server = play.server(0)                      # port 0: any free port
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_serves_the_app_from_its_own_folder_whatever_the_working_directory(self):
        with urllib.request.urlopen(f'http://localhost:{self.port}/', timeout=5) as r:
            self.assertIn('<title>kid-synth</title>', r.read(2000).decode())

    def test_listens_on_this_machine_only(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')

    def test_recognises_a_port_that_already_serves_the_app(self):
        self.assertTrue(play.serves_kid_synth(self.port))

    def test_a_dead_port_does_not_serve_the_app(self):
        self.server.shutdown()
        self.server.server_close()
        self.assertFalse(play.serves_kid_synth(self.port))
        self.server = play.server(0)                      # so tearDown has something to close
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def test_prefers_the_usual_port_and_moves_on_when_it_is_taken_by_something_else(self):
        taken = {8377: 'other', 8378: 'free'}
        self.assertEqual(play.choose({8377: 'free', 8378: 'free'}.get), (8377, 'free'))
        self.assertEqual(play.choose({8377: 'ours'}.get), (8377, 'ours'))
        self.assertEqual(play.choose(taken.get), (8378, 'free'))


if __name__ == '__main__':
    unittest.main()
