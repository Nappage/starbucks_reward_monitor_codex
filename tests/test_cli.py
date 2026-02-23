import unittest

from starbucks_monitor.cli import build_parser


class CLITest(unittest.TestCase):
    def test_default_mode_is_static(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.mode, "static")

    def test_accepts_rendered_mode(self):
        parser = build_parser()
        args = parser.parse_args(["--mode", "rendered"])
        self.assertEqual(args.mode, "rendered")


if __name__ == "__main__":
    unittest.main()
