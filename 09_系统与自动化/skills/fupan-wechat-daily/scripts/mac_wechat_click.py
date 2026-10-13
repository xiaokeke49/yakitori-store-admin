#!/usr/bin/env python3
"""Inspect WeChat windows or send one explicitly requested macOS left click."""

import argparse
import ctypes
import json
import math
import plistlib
import subprocess
import sys
import time


class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class MacUI:
    def __init__(self):
        if sys.platform != "darwin":
            raise RuntimeError("macOS only; Windows needs its own implementation")
        self.cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        self.cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.ax = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        self.ax.AXIsProcessTrusted.restype = ctypes.c_bool
        self.cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        self.cg.CGWindowListCopyWindowInfo.restype = ctypes.c_void_p
        self.cf.CFPropertyListCreateData.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long, ctypes.c_ulong, ctypes.c_void_p]
        self.cf.CFPropertyListCreateData.restype = ctypes.c_void_p
        self.cf.CFDataGetLength.argtypes = [ctypes.c_void_p]
        self.cf.CFDataGetLength.restype = ctypes.c_long
        self.cf.CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
        self.cf.CFDataGetBytePtr.restype = ctypes.c_void_p
        self.cf.CFRelease.argtypes = [ctypes.c_void_p]
        self.cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, Point, ctypes.c_uint32]
        self.cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        self.cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]

    def windows(self):
        array = self.cg.CGWindowListCopyWindowInfo(1, 0)
        if not array:
            raise RuntimeError("Cannot read visible windows")
        data = None
        try:
            data = self.cf.CFPropertyListCreateData(None, array, 100, 0, None)
            if not data:
                raise RuntimeError("Cannot decode window list")
            return plistlib.loads(ctypes.string_at(
                self.cf.CFDataGetBytePtr(data), self.cf.CFDataGetLength(data)))
        finally:
            if data:
                self.cf.CFRelease(data)
            self.cf.CFRelease(array)

    def click(self, point):
        # Allocate all events first, so allocation failure cannot leave a held button.
        events = []
        try:
            for event_type in (5, 1, 2):  # move, left down, left up
                event = self.cg.CGEventCreateMouseEvent(None, event_type, Point(*point), 0)
                if not event:
                    raise RuntimeError("Cannot create mouse event")
                events.append(event)
            self.cg.CGEventPost(0, events[0])
            self.cg.CGEventPost(0, events[1])
            try:
                time.sleep(0.08)
            finally:
                self.cg.CGEventPost(0, events[2])
        finally:
            for event in events:
                self.cf.CFRelease(event)


def bounds(window):
    return tuple(window["kCGWindowBounds"][k] for k in ("X", "Y", "Width", "Height"))


def contains(rect, point):
    x, y, w, h = rect
    return x <= point[0] < x + w and y <= point[1] < y + h


def check_target(windows, window_id, expected, point):
    target = next((w for w in windows if w["kCGWindowNumber"] == window_id), None)
    if not target or target.get("kCGWindowOwnerName") not in ("WeChat", "微信"):
        raise RuntimeError("Selected WeChat window is no longer visible")
    if target.get("kCGWindowLayer") != 0 or bounds(target) != tuple(expected):
        raise RuntimeError("Window geometry changed; obtain a fresh screenshot and bounds")
    if not contains(expected, point):
        raise RuntimeError("Point is outside the selected window")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-windows", action="store_true")
    parser.add_argument("--window-id", type=int)
    parser.add_argument("--bounds", type=float, nargs=4, metavar=("X", "Y", "W", "H"))
    parser.add_argument("--point", type=float, nargs=2, metavar=("X", "Y"))
    parser.add_argument("--execute", action="store_true", help="Send click; default only previews")
    args = parser.parse_args()
    if args.list_windows:
        if args.execute or args.window_id is not None or args.bounds or args.point:
            parser.error("--list-windows cannot be combined with click arguments")
    else:
        if args.window_id is None or args.bounds is None or args.point is None:
            parser.error("click preview requires --window-id, --bounds and --point")
        if not all(math.isfinite(n) for n in args.bounds + args.point) or min(args.bounds[2:]) <= 0:
            parser.error("coordinates must be finite and dimensions positive")
    ui = MacUI()
    windows = ui.windows()
    if args.list_windows:
        print(json.dumps([
            {"id": w["kCGWindowNumber"], "title": w.get("kCGWindowName", ""),
             "bounds": bounds(w), "layer": w["kCGWindowLayer"]}
            for w in windows if w.get("kCGWindowOwnerName") in ("WeChat", "微信")
        ], ensure_ascii=False, indent=2))
        return
    target = check_target(windows, args.window_id, args.bounds, args.point)
    if not args.execute:
        print(json.dumps({"mode": "preview", "window_id": args.window_id,
                          "title": target.get("kCGWindowName", ""), "point": args.point}, ensure_ascii=False))
        return
    if not ui.ax.AXIsProcessTrusted():
        raise RuntimeError("Accessibility permission unavailable; no click sent")
    subprocess.run(["osascript", "-e", 'tell application id "com.tencent.xinWeChat" to activate'], check=True)
    time.sleep(0.2)
    windows = ui.windows()
    current = check_target(windows, args.window_id, args.bounds, args.point)
    if current["kCGWindowOwnerPID"] != target["kCGWindowOwnerPID"]:
        raise RuntimeError("WeChat process changed; obtain a fresh observation")
    # On-screen windows are ordered front to back. Refuse a covered target.
    for window in windows:
        if window["kCGWindowNumber"] == args.window_id:
            break
        if window.get("kCGWindowAlpha", 1) > 0 and contains(bounds(window), args.point):
            raise RuntimeError("Another window covers this point; observe again")
    ui.click(args.point)
    print("Left click sent once; verify the resulting UI before any next action")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
