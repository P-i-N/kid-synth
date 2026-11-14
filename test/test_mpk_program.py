"""Tests for tools/mpk-program.py. Run: python3 -m unittest discover -s test"""
import importlib.util, pathlib, unittest

path = pathlib.Path(__file__).resolve().parent.parent / 'tools' / 'mpk-program.py'
spec = importlib.util.spec_from_file_location('mpk_program', path)
mpk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mpk)

# What this project's MPK mini mk2 answered when asked for its current program, before any change.
FACTORY_REPLY = bytes.fromhex(
    'F0 47 00 26 67 00 6D 00 00 00 04 00 00 00 00 00 00 03 01 00 00 00 00 00 01 01 01'
    ' 17 00 01 00 18 01 02 00 19 02 03 00 1A 03 04 00 1B 04 05 00 1C 05 06 00 1D 06 07 00 1E 07 08 00'
    ' 1F 08 09 00 20 09 0A 00 21 0A 0B 00 22 0B 0C 00 23 0C 0D 00 24 0D 0E 00 25 0E 0F 00 26 0F 10 00'
    ' 01 00 7F 02 00 7F 03 00 7F 04 00 7F 05 00 7F 06 00 7F 07 00 7F 08 00 7F 0C F7')


class Request(unittest.TestCase):
    def test_asks_for_one_program(self):
        self.assertEqual(mpk.request(0), bytes.fromhex('F0 47 00 26 66 00 01 00 F7'))
        self.assertEqual(mpk.request(4), bytes.fromhex('F0 47 00 26 66 00 01 04 F7'))

    def test_only_ram_and_four_slots_exist(self):
        for slot in (-1, 5, 127):
            with self.assertRaises(ValueError):
                mpk.request(slot)


class ToddlerProgram(unittest.TestCase):
    def setUp(self):
        self.p = mpk.toddler_program(1)

    def test_is_a_whole_send_message_for_its_slot(self):
        self.assertEqual(len(self.p), 117)
        self.assertEqual(self.p[:7], bytes.fromhex('F0 47 00 26 64 00 6D'))
        self.assertEqual(self.p[7], 1)
        self.assertEqual(self.p[116], 0xF7)
        self.assertEqual(mpk.toddler_program(0)[7], 0)
        self.assertEqual(mpk.toddler_program(4)[7], 4)
        with self.assertRaises(ValueError):
            mpk.toddler_program(5)

    def test_every_data_byte_is_a_legal_midi_data_byte(self):
        self.assertTrue(all(b < 0x80 for b in self.p[1:116]))

    def test_pads_get_their_own_channel_and_keys_stay_on_channel_1(self):
        self.assertEqual(self.p[8], 9)    # pads: channel 10
        self.assertEqual(self.p[9], 0)    # keys and knobs: channel 1

    def test_starts_with_no_octave_shift_and_no_transpose(self):
        self.assertEqual(self.p[10], 4)
        self.assertEqual(self.p[115], 12)

    def test_arpeggiator_is_off_unlatched_and_as_slow_as_it_goes(self):
        self.assertEqual(self.p[11], 0)                    # off
        self.assertEqual(self.p[13], 0)                    # quarter notes
        self.assertEqual(self.p[14], 0)                    # internal clock
        self.assertEqual(self.p[15], 0)                    # latch off
        self.assertEqual(self.p[17], 4)                    # tap tempo needs four taps
        self.assertEqual(self.p[18] * 128 + self.p[19], 30)  # 30 BPM, the slowest

    def test_joystick_is_left_as_the_factory_has_it(self):
        self.assertEqual(self.p[21:27], FACTORY_REPLY[21:27])

    def test_pads_keep_their_notes_and_get_numbers_no_knob_uses(self):
        for i in range(16):
            note, second, third, kind = self.p[27 + 4 * i: 31 + 4 * i]
            self.assertEqual(note, 23 + i)
            # Sources disagree on which of these two is the controller and which the program change,
            # so both carry the same number: 24–39, clear of the knobs' 1–8, and 24+i ≡ i (mod 8).
            self.assertEqual((second, third), (24 + i, 24 + i))
            self.assertEqual(kind, 0)                      # momentary

    def test_knobs_are_left_as_the_factory_has_them(self):
        self.assertEqual(self.p[91:115], FACTORY_REPLY[91:115])


class Restoring(unittest.TestCase):
    def test_a_saved_reply_becomes_a_message_that_writes_it_back(self):
        back = mpk.as_send(FACTORY_REPLY, 3)
        self.assertEqual(back[4], 0x64)
        self.assertEqual(back[7], 3)
        self.assertEqual(back[8:], FACTORY_REPLY[8:])
        self.assertEqual(back[:4], FACTORY_REPLY[:4])

    def test_refuses_anything_that_is_not_a_whole_program(self):
        for bad in (b'', FACTORY_REPLY[:-1], b'\xF0\x7E' + FACTORY_REPLY[2:], FACTORY_REPLY[:-1] + b'\x00'):
            with self.assertRaises(ValueError):
                mpk.as_send(bad, 1)


class ReadingReplies(unittest.TestCase):
    def test_finds_the_program_in_what_aseqdump_prints(self):
        hexes = FACTORY_REPLY.hex(' ').upper()
        text = ('Waiting for data. Press Ctrl+C to end.\n'
                'Source  Event                  Ch  Data\n'
                ' 24:0   Note on                 0, note 60, velocity 90\n'
                f' 24:0   System exclusive           {hexes[:120]}\n'
                f' 24:0   System exclusive           {hexes[120:]}\n')
        self.assertEqual(mpk.parse_dump(text), FACTORY_REPLY)

    def test_no_reply_is_none(self):
        self.assertIsNone(mpk.parse_dump('Waiting for data.\n 24:0   Note on  0, note 60, velocity 90\n'))


class Comparing(unittest.TestCase):
    def test_same_settings_whatever_the_command_and_slot(self):
        self.assertEqual(mpk.differences(FACTORY_REPLY, mpk.as_send(FACTORY_REPLY, 2)), [])

    def test_names_the_bytes_that_differ(self):
        self.assertEqual(mpk.differences(FACTORY_REPLY, mpk.toddler_program(0))[:3], [8, 17, 18])


if __name__ == '__main__':
    unittest.main()
