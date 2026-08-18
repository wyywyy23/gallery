#!/usr/bin/env python

import json
import math
import os
import re
import sys

from PIL import Image, ImageOps

PATH = os.path.abspath(os.path.dirname(__file__) + "/../")
RELATIVE_PATH = "photos"
PHOTO_PATH = PATH + "/" + RELATIVE_PATH
COLOR_SAMPLE_SIZE = 64

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

# OKLCh hue is unwrapped at magenta so the ordered path runs through these
# perceptual color families: purple, blue, cyan, green, yellow, orange, red.
HUE_PATH_START = 330.0
HUE_STAGE_BOUNDARIES = (0.0, 60.0, 120.0, 175.0, 230.0, 275.0, 315.0, 360.0)
HUE_WEIGHT_POWER = 2
MAX_EXACT_STAGE_SIZE = 12


def is_original(path):
    return ".min." not in path and ".placeholder." not in path and is_image_path(path)


def is_not_min_path(path):
    return not is_min_path(path) and is_image_path(path)


def is_min_path(path):
    return ".min." in path and is_image_path(path)


def get_directories():
    items = sorted(os.listdir(PHOTO_PATH))
    return list(filter(lambda x: os.path.isdir(PHOTO_PATH + "/" + x), items))


def is_image_path(path):
    return re.search(r"\.(jpe?g|png|JPE?G|PNG)$", path)


def get_placeholder_path(path):
    return get_path(path, "placeholder")


def get_min_path(path):
    return get_path(path, "min")


def get_path(path, ext):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", "." + ext + r".\1", path)


def srgb_to_linear(value):
    value = value / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def rgb_to_oklab(pixel):
    red, green, blue = (srgb_to_linear(value) for value in pixel)
    light = 0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    medium = 0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    short = 0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue

    light = max(light, 0) ** (1 / 3)
    medium = max(medium, 0) ** (1 / 3)
    short = max(short, 0) ** (1 / 3)

    return (
        0.2104542553 * light + 0.7936177850 * medium - 0.0040720468 * short,
        1.9779984951 * light - 2.4285922050 * medium + 0.4505937099 * short,
        0.0259040371 * light + 0.7827717662 * medium - 0.8086757660 * short,
    )


def hue_path(hue):
    return (HUE_PATH_START - hue) % 360.0


def color_coordinates(image):
    """Return representative OKLCh coordinates for an image."""
    sample = ImageOps.exif_transpose(image).convert("RGB")
    sample.thumbnail((COLOR_SAMPLE_SIZE, COLOR_SAMPLE_SIZE), RESAMPLE)

    hue_samples = []
    lightness_total = 0.0
    chroma_total = 0.0
    for pixel in sample.getdata():
        lightness, axis_a, axis_b = rgb_to_oklab(pixel)
        chroma = math.hypot(axis_a, axis_b)
        hue = (math.degrees(math.atan2(axis_b, axis_a)) + 360.0) % 360.0

        # A chroma-squared weight makes small but visually strong color regions
        # count without letting neutral pixels make the hue unstable. The
        # weighted median avoids complementary colors cancelling into a false
        # intermediate hue.
        tone_weight = max(0.2, 1.0 - abs(lightness - 0.55) * 1.4)
        weight = (chroma ** HUE_WEIGHT_POWER) * tone_weight
        hue_samples.append((hue_path(hue), weight))
        lightness_total += lightness
        chroma_total += chroma

    pixel_count = len(hue_samples)
    if pixel_count == 0:
        return {"lightness": 0.0, "chroma": 0.0, "hue": HUE_PATH_START}

    hue_samples.sort(key=lambda sample: sample[0])
    total_hue_weight = sum(weight for _, weight in hue_samples)
    if total_hue_weight <= 1e-12:
        representative_path = 180.0
    else:
        midpoint = total_hue_weight / 2.0
        cumulative_weight = 0.0
        representative_path = hue_samples[-1][0]
        for path, weight in hue_samples:
            cumulative_weight += weight
            if cumulative_weight >= midpoint:
                representative_path = path
                break

    return {
        "lightness": round(lightness_total / pixel_count, 6),
        "chroma": round(chroma_total / pixel_count, 6),
        "hue": round((HUE_PATH_START - representative_path) % 360.0, 6),
    }


def extend_lightness_cost(cost, jump):
    return max(cost[0], jump), cost[1] + jump * jump


def combine_lightness_cost(previous, internal, boundary_jump):
    return (
        max(previous[0], internal[0], boundary_jump),
        previous[1] + internal[1] + boundary_jump * boundary_jump,
    )


def path_tiebreak(photos):
    hue_distance = sum(
        abs(hue_path(current["color_hue"]) - hue_path(previous["color_hue"]))
        for previous, current in zip(photos, photos[1:])
    )
    return hue_distance, tuple(photo["path"] for photo in photos)


def index_path_cost(stage, path):
    cost = (0.0, 0.0)
    for previous, current in zip(path, path[1:]):
        jump = abs(
            stage[current]["color_lightness"]
            - stage[previous]["color_lightness"]
        )
        cost = extend_lightness_cost(cost, jump)
    return cost


def stage_lightness_paths(stage):
    """Return the best lightness path for every possible stage endpoint pair."""
    length = len(stage)
    if length > MAX_EXACT_STAGE_SIZE:
        ascending = sorted(
            range(length),
            key=lambda index: (
                stage[index]["color_lightness"],
                hue_path(stage[index]["color_hue"]),
                stage[index]["path"],
            ),
        )
        descending = list(reversed(ascending))
        return {
            (path[0], path[-1]): (index_path_cost(stage, path), path)
            for path in (ascending, descending)
        }

    complete_mask = (1 << length) - 1
    result = {}

    for start in range(length):
        states = {(1 << start, start): ((0.0, 0.0), [start])}
        for mask in range(1 << length):
            for end in range(length):
                current = states.get((mask, end))
                if current is None:
                    continue

                cost, path = current
                for next_index in range(length):
                    if mask & (1 << next_index):
                        continue

                    jump = abs(
                        stage[end]["color_lightness"]
                        - stage[next_index]["color_lightness"]
                    )
                    candidate_cost = extend_lightness_cost(cost, jump)
                    candidate_path = path + [next_index]
                    key = (mask | (1 << next_index), next_index)
                    existing = states.get(key)
                    if existing is None:
                        states[key] = (candidate_cost, candidate_path)
                        continue

                    candidate_photos = [stage[index] for index in candidate_path]
                    existing_photos = [stage[index] for index in existing[1]]
                    if (candidate_cost, path_tiebreak(candidate_photos)) < (
                        existing[0],
                        path_tiebreak(existing_photos),
                    ):
                        states[key] = (candidate_cost, candidate_path)

        for end in range(length):
            state = states.get((complete_mask, end))
            if state is not None:
                result[(start, end)] = state

    return result


def assign_colorspace_order(photos):
    """Assign ranks along the hue chain while smoothing adjacent lightness."""
    stages = []
    for lower, upper in zip(HUE_STAGE_BOUNDARIES, HUE_STAGE_BOUNDARIES[1:]):
        stage = sorted(
            [
                photo
                for photo in photos
                if lower <= hue_path(photo["color_hue"]) < upper
            ],
            key=lambda photo: (hue_path(photo["color_hue"]), photo["path"]),
        )
        if not stage:
            continue
        stages.append(stage)

    if not stages:
        return

    first_stage = stages[0]
    first_options = stage_lightness_paths(first_stage)
    states = {}
    for end in range(len(first_stage)):
        candidates = []
        for start in range(len(first_stage)):
            option = first_options.get((start, end))
            if option is None:
                continue
            cost, path = option
            sequence = [first_stage[index] for index in path]
            candidates.append((cost, sequence))
        if candidates:
            states[end] = min(
                candidates,
                key=lambda candidate: (candidate[0], path_tiebreak(candidate[1])),
            )

    for stage in stages[1:]:
        options = stage_lightness_paths(stage)
        next_states = {}
        for end in range(len(stage)):
            candidates = []
            for previous_cost, previous_sequence in states.values():
                for start in range(len(stage)):
                    option = options.get((start, end))
                    if option is None:
                        continue
                    internal_cost, path = option
                    current_sequence = [stage[index] for index in path]
                    boundary_jump = abs(
                        previous_sequence[-1]["color_lightness"]
                        - current_sequence[0]["color_lightness"]
                    )
                    combined_cost = combine_lightness_cost(
                        previous_cost,
                        internal_cost,
                        boundary_jump,
                    )
                    candidates.append(
                        (combined_cost, previous_sequence + current_sequence)
                    )
            if candidates:
                next_states[end] = min(
                    candidates,
                    key=lambda candidate: (
                        candidate[0],
                        path_tiebreak(candidate[1]),
                    ),
                )
        states = next_states

    _, ordered = min(
        states.values(),
        key=lambda state: (state[0], path_tiebreak(state[1])),
    )
    for rank, photo in enumerate(ordered):
        photo["color_sort"] = rank


def get_images(path):
    items = sorted(os.listdir(PHOTO_PATH + "/" + path))
    filtered_items = list(filter(is_original, items))

    result = []
    for img in filtered_items:
        width, height = 0, 0
        has_compressed = False
        p = "./" + RELATIVE_PATH + "/" + path + "/" + img
        original_path = PHOTO_PATH + "/" + path + "/" + img
        with open(original_path, "rb") as f:
            im = Image.open(f)
            im = ImageOps.exif_transpose(im)
            width, height = im.size
        if os.path.isfile(get_min_path(p)):
            has_compressed = True
        color_source = get_min_path(original_path) if has_compressed else original_path
        with Image.open(color_source) as im:
            color = color_coordinates(im)
        result.append(
            {
                "width": width,
                "height": height,
                "path": "./" + RELATIVE_PATH + "/" + path + "/" + img,
                "compressed_path": get_min_path(p),
                "compressed": has_compressed,
                "placeholder_path": get_placeholder_path(p),
                "color_lightness": color["lightness"],
                "color_chroma": color["chroma"],
                "color_hue": color["hue"],
            }
        )
    assign_colorspace_order(result)
    return result


def write_config(config):
    with open(PATH + "/config.json", "w") as f:
        f.write(json.dumps(config, indent=2, separators=(",", ": ")))


def run():
    print("Starting to collect all albums within the /photos directory...")
    config = {}
    dirs = sorted(get_directories(), reverse=True)
    print("Found {length} directories".format(length=len(dirs)))
    for i, path in enumerate(dirs):
        print(
            str(i + 1)
            + ': Processing photos for the album "{album}"'.format(album=path)
        )
        config[path] = get_images(path)

        print(
            '   Done processing {l} photos for "{album}"\n'.format(
                l=len(config[path]), album=path
            )
        )

    print("Done processing all {length} albums".format(length=len(dirs)))
    print("Writing files to {path} now...".format(path=PATH + "/config.json"))
    write_config(config)
    print(
        """Done writing config.json."""
    )
    return 0


if __name__ == "__main__":
    sys.exit(run())
