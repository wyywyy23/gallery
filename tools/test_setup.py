#!/usr/bin/env python3

import unittest

from PIL import Image

from setup import color_sort_key


class ColorSortKeyTest(unittest.TestCase):
    def test_orders_reference_colors_from_cool_to_warm(self):
        colors = [
            ("blue", (0, 96, 255)),
            ("purple", (127, 63, 191)),
            ("orange", (224, 112, 32)),
            ("red", (208, 48, 32)),
        ]

        scores = [
            color_sort_key(Image.new("RGB", (8, 8), color))
            for _, color in colors
        ]

        self.assertEqual(scores, sorted(scores))

    def test_is_deterministic(self):
        image = Image.new("RGB", (8, 8), (80, 120, 160))
        self.assertEqual(color_sort_key(image), color_sort_key(image))


if __name__ == "__main__":
    unittest.main()
