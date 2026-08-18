#!/usr/bin/env python3

import unittest

from PIL import Image

from setup import assign_colorspace_order, color_coordinates, hue_path


class ColorspaceOrderTest(unittest.TestCase):
    def test_orders_reference_colors_along_oklch_hue_path(self):
        colors = [
            ("purple", (127, 63, 191)),
            ("blue", (0, 96, 255)),
            ("cyan", (0, 180, 190)),
            ("green", (30, 160, 70)),
            ("yellow", (230, 200, 30)),
            ("orange", (224, 112, 32)),
            ("red", (208, 48, 32)),
        ]

        paths = [
            hue_path(color_coordinates(Image.new("RGB", (8, 8), color))["hue"])
            for _, color in colors
        ]

        self.assertEqual(paths, sorted(paths))

    def test_smooths_lightness_without_crossing_hue_stages(self):
        photos = [
            {
                "path": "purple.jpg",
                "color_hue": 280.0,
                "color_lightness": 0.54,
            },
            *[
                {
                    "path": f"blue-{index}.jpg",
                    "color_hue": 250.0,
                    "color_lightness": lightness,
                }
                for index, lightness in enumerate((0.25, 0.47, 0.51, 0.59, 0.63, 0.87))
            ],
            {
                "path": "green.jpg",
                "color_hue": 130.0,
                "color_lightness": 0.47,
            },
        ]

        assign_colorspace_order(photos)
        ordered = sorted(photos, key=lambda photo: photo["color_sort"])
        stages = [int(hue_path(photo["color_hue"]) // 60) for photo in ordered]
        jumps = [
            abs(current["color_lightness"] - previous["color_lightness"])
            for previous, current in zip(ordered, ordered[1:])
        ]

        self.assertEqual(stages, sorted(stages))
        self.assertLessEqual(max(jumps), 0.29)


if __name__ == "__main__":
    unittest.main()
