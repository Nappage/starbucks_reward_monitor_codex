import unittest
from unittest.mock import patch

from starbucks_monitor import cli


class CLIRuntimeValidationTest(unittest.TestCase):
    def test_send_test_notification_requires_telegram_credentials(self):
        with patch('sys.argv', ['starbucks_monitor.cli', '--send-test-notification']):
            self.assertEqual(cli.main(), 1)


if __name__ == '__main__':
    unittest.main()
