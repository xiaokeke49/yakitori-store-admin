"""Geometry checks must reject stale or unintended click targets without input."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'mac_wechat_click.py'
spec = importlib.util.spec_from_file_location('wechat_click', SCRIPT)
click = importlib.util.module_from_spec(spec)
spec.loader.exec_module(click)


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.window = {
            'kCGWindowNumber': 7, 'kCGWindowOwnerName': 'WeChat',
            'kCGWindowLayer': 0,
            'kCGWindowBounds': dict(X=-500, Y=20, Width=400, Height=600),
        }
        self.bounds = [-500, 20, 400, 600]
        self.point = [-300, 100]

    def test_negative_monitor_coordinates(self):
        self.assertIs(click.check_target([self.window], 7, self.bounds, self.point), self.window)

    def test_moved_window(self):
        with self.assertRaises(RuntimeError):
            click.check_target([self.window], 7, [-499, 20, 400, 600], self.point)

    def test_closed_window(self):
        with self.assertRaises(RuntimeError):
            click.check_target([], 7, self.bounds, self.point)

    def test_other_application(self):
        other = dict(self.window, kCGWindowOwnerName='Other')
        with self.assertRaises(RuntimeError):
            click.check_target([other], 7, self.bounds, self.point)

    def test_outside_point(self):
        with self.assertRaises(RuntimeError):
            click.check_target([self.window], 7, self.bounds, [-100, 100])


if __name__ == '__main__':
    unittest.main()
