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

    def test_has_phase2_and_phase3_options(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.state_file, ".starbucks_monitor_state.json")
        self.assertEqual(args.notification_history_file, ".starbucks_monitor_notifications.json")
        self.assertIsNone(args.telegram_bot_token)
        self.assertIsNone(args.telegram_chat_id)

if __name__ == "__main__":
    unittest.main()
