"""Contrast and surface-contract tests for the public warm paper palette."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "web/styles.css").read_text(encoding="utf-8")
ACTIVE = CSS.split("/* UX refinement:", 1)[1]


def _rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def _linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _luminance(value):
    red, green, blue = _rgb(value)
    return 0.2126 * _linear(red) + 0.7152 * _linear(green) + 0.0722 * _linear(blue)


def _contrast(foreground, background):
    first, second = _luminance(foreground), _luminance(background)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


class SurfacePaletteTests(unittest.TestCase):
    COLORS = {
        "ink": "#1d211f",
        "muted": "#59605c",
        "paper": "#ebe6dc",
        "panel": "#f4f1eb",
        "raised": "#f0ece4",
        "accent": "#6b3437",
        "focus": "#8a5c14",
        "closed": "#715523",
        "closed_soft": "#eee5d4",
        "hover": "#e1dbd0",
    }

    def test_active_palette_uses_intentional_warm_surface_hierarchy(self):
        for token in (
            "--paper:#ebe6dc",
            "--panel:#f4f1eb",
            "--panel-raised:#f0ece4",
            "--surface-hover:#e1dbd0",
        ):
            self.assertIn(token, ACTIVE)
        self.assertNotEqual(self.COLORS["paper"], self.COLORS["panel"])
        self.assertNotEqual(self.COLORS["panel"], self.COLORS["raised"])

    def test_key_text_and_control_contrast(self):
        self.assertGreaterEqual(_contrast(self.COLORS["ink"], self.COLORS["paper"]), 7)
        self.assertGreaterEqual(_contrast(self.COLORS["ink"], self.COLORS["panel"]), 7)
        self.assertGreaterEqual(_contrast(self.COLORS["muted"], self.COLORS["paper"]), 4.5)
        self.assertGreaterEqual(_contrast(self.COLORS["muted"], self.COLORS["panel"]), 4.5)
        self.assertGreaterEqual(_contrast(self.COLORS["accent"], self.COLORS["paper"]), 4.5)
        self.assertGreaterEqual(_contrast(self.COLORS["accent"], self.COLORS["panel"]), 4.5)
        self.assertGreaterEqual(_contrast(self.COLORS["focus"], self.COLORS["paper"]), 4.5)
        self.assertGreaterEqual(_contrast(self.COLORS["closed"], self.COLORS["closed_soft"]), 4.5)

    def test_hover_and_focus_surfaces_remain_perceivable(self):
        self.assertGreater(_contrast(self.COLORS["hover"], self.COLORS["paper"]), 1.05)
        self.assertIn("outline-color:var(--focus)", ACTIVE)
        self.assertIn("background:var(--surface-hover)", ACTIVE)

    def test_active_surface_block_has_no_unintended_major_white_surface(self):
        self.assertNotRegex(ACTIVE, r"background(?:-color)?:\s*(?:#fff|#ffffff|white)")
        self.assertNotRegex(ACTIVE, r"--(?:paper|panel|panel-raised):\s*(?:#fff|#ffffff|white)")

    def test_legacy_white_literals_are_classifiable(self):
        self.assertIn("var(--panel,#fff)", (ROOT / "web/operations.css").read_text(encoding="utf-8"))
        self.assertIn("var(--panel,#fff)", (ROOT / "web/history.css").read_text(encoding="utf-8"))
        self.assertIn("--white:#fff", CSS)
        self.assertRegex(CSS, r"\.fatal[^}]*color:white")


if __name__ == "__main__":
    unittest.main()
