#!/usr/bin/env python3

import argparse
import math
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    print(
        "error: Pillow is required. Install it with: python3 -m pip install Pillow",
        file=sys.stderr,
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
PHOTOS_DIR = ROOT / "photos"
DEFAULT_WATERMARK_PATH = ROOT / "watermark.png"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
GENERATED_MARKERS = (".min.", ".placeholder.")
NUMBERED_RE = re.compile(r"^(?P<prefix>.+)_(?P<number>\d+)\.(?:jpe?g|png)$", re.I)

# Closest 8-bit Pillow equivalent of the former ImageMagick setting:
# -unsharp 0.5x0.5+0.5+0.008
WEB_SHARPEN_RADIUS = 0.5
WEB_SHARPEN_PERCENT = 50
WEB_SHARPEN_THRESHOLD = 2

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS


class AddPhotoError(Exception):
    pass


@dataclass
class PhotoJob:
    source: Path
    target: Path
    min_path: Path
    placeholder_path: Path
    action: str


def is_image_path(path):
    return path.suffix.lower() in IMAGE_EXTENSIONS


def is_generated_path(path):
    name = path.name.lower()
    return any(marker in name for marker in GENERATED_MARKERS)


def is_original_image(path):
    return path.is_file() and is_image_path(path) and not is_generated_path(path)


def resolve_path(raw_path):
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def get_album_dir(album_name, create_album=False):
    if not PHOTOS_DIR.is_dir():
        if create_album:
            PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        else:
            raise AddPhotoError(f"Missing photos directory: {PHOTOS_DIR}")

    albums = sorted([path for path in PHOTOS_DIR.iterdir() if path.is_dir()])
    if album_name:
        direct = PHOTOS_DIR / album_name
        if direct.is_dir():
            return direct

        matches = [path for path in albums if path.name.lower() == album_name.lower()]
        if len(matches) == 1:
            return matches[0]

        if create_album:
            direct.mkdir(parents=True, exist_ok=False)
            return direct

        names = ", ".join(path.name for path in albums) or "none"
        raise AddPhotoError(
            f'Album "{album_name}" was not found. '
            f"Available albums: {names}. Pass --create-album to create it."
        )

    if len(albums) == 1:
        return albums[0]

    if not albums:
        raise AddPhotoError(
            f"No albums found in {PHOTOS_DIR}. Pass --album NAME --create-album."
        )

    names = ", ".join(path.name for path in albums)
    raise AddPhotoError(f"Multiple albums found; pass --album. Available albums: {names}")


def expand_sources(raw_sources):
    sources = []
    seen = set()

    for raw_source in raw_sources:
        source = resolve_path(raw_source)
        if source.is_dir():
            candidates = sorted(path for path in source.iterdir() if is_original_image(path))
            if not candidates:
                raise AddPhotoError(f"No original images found in directory: {source}")
        else:
            candidates = [source]

        for candidate in candidates:
            if not candidate.is_file():
                raise AddPhotoError(f"Source file does not exist: {candidate}")
            if not is_image_path(candidate):
                raise AddPhotoError(f"Source is not a supported image: {candidate}")
            if is_generated_path(candidate):
                raise AddPhotoError(f"Source looks like a generated image, not an original: {candidate}")

            key = candidate.resolve()
            if key not in seen:
                sources.append(candidate)
                seen.add(key)

    return sources


def album_slug(album_name):
    return album_name.replace(" ", "_").lower()


def get_numbering(album_dir):
    matches = []
    for path in album_dir.iterdir():
        if not is_original_image(path):
            continue
        match = NUMBERED_RE.match(path.name)
        if match:
            matches.append(
                (
                    match.group("prefix"),
                    int(match.group("number")),
                    len(match.group("number")),
                )
            )

    if not matches:
        return album_slug(album_dir.name), 3, 1

    prefix = Counter(match[0] for match in matches).most_common(1)[0][0]
    prefix_matches = [match for match in matches if match[0] == prefix]
    digits = max(3, max(match[2] for match in prefix_matches))
    next_number = max(match[1] for match in prefix_matches) + 1
    return prefix, digits, next_number


def derived_path(path, label):
    return path.with_name(f"{path.stem}.{label}{path.suffix.lower()}")


def is_inside(path, directory):
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def is_processed_numbered_source(source, album_dir):
    return source.parent.resolve() == album_dir.resolve() and NUMBERED_RE.match(source.name)


def next_available_target(album_dir, prefix, digits, start_number, source_suffix, reserved):
    number = start_number
    while True:
        target = album_dir / f"{prefix}_{number:0{digits}d}{source_suffix.lower()}"
        min_path = derived_path(target, "min")
        placeholder_path = derived_path(target, "placeholder")
        paths = {target.resolve(), min_path.resolve(), placeholder_path.resolve()}

        if not paths & reserved and not target.exists() and not min_path.exists() and not placeholder_path.exists():
            return target, number + 1

        number += 1


def plan_jobs(sources, album_dir, move_sources):
    prefix, digits, next_number = get_numbering(album_dir)
    reserved = set()
    jobs = []

    for source in sources:
        if is_processed_numbered_source(source, album_dir):
            target = source
            min_path = derived_path(target, "min")
            placeholder_path = derived_path(target, "placeholder")
            if min_path.exists() or placeholder_path.exists():
                raise AddPhotoError(
                    f"{source.name} already has generated versions; refusing to watermark it again."
                )
            action = "process in place"
        else:
            target, next_number = next_available_target(
                album_dir, prefix, digits, next_number, source.suffix, reserved
            )
            min_path = derived_path(target, "min")
            placeholder_path = derived_path(target, "placeholder")
            action = "move" if move_sources or is_inside(source, album_dir) else "copy"

        paths = {target.resolve(), min_path.resolve(), placeholder_path.resolve()}
        if paths & reserved:
            raise AddPhotoError(f"Multiple inputs would write the same target: {target}")
        reserved.update(paths)
        jobs.append(PhotoJob(source, target, min_path, placeholder_path, action))

    return jobs


def load_image(path):
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).copy()


def apply_watermark(image, watermark_path):
    with Image.open(watermark_path) as watermark_image:
        watermark = ImageOps.exif_transpose(watermark_image).convert("RGBA")

    width, height = image.size
    watermark_width, watermark_height = watermark.size
    target_width = max(1, int(max(width, height) * 0.15))
    scale = watermark_width / target_width
    watermark = watermark.resize(
        (
            max(1, int(watermark_width / scale)),
            max(1, int(watermark_height / scale)),
        ),
        RESAMPLE,
    )

    x = int(width / 2 - watermark.width / 2)
    y = int(watermark.height / 2)
    x = min(max(0, x), max(0, width - watermark.width))
    y = min(max(0, y), max(0, height - watermark.height))

    region = image.convert("RGB").crop((x, y, x + watermark.width, y + watermark.height))
    avg_intensity = sum(region.convert("L").getdata()) / (watermark.width * watermark.height)
    opacity = math.sqrt(avg_intensity / 255)

    alpha = watermark.getchannel("A").point(lambda value: int(value * opacity))
    watermark.putalpha(alpha)

    base = image.convert("RGBA")
    base.alpha_composite(watermark, dest=(x, y))
    return base.convert("RGB")


def resized_image(image, max_size):
    result = image.copy()
    result.thumbnail((max_size, max_size), RESAMPLE)
    return result


def web_display_image(image, max_size):
    resized = resized_image(image, max_size)
    return resized.filter(
        ImageFilter.UnsharpMask(
            radius=WEB_SHARPEN_RADIUS,
            percent=WEB_SHARPEN_PERCENT,
            threshold=WEB_SHARPEN_THRESHOLD,
        )
    )


def save_image(image, path, quality):
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        image.convert("RGB").save(
            path,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
        )
        return

    if suffix == ".png":
        image.save(path, format="PNG", optimize=True)
        return

    raise AddPhotoError(f"Unsupported output format: {path}")


def process_job(job, args):
    image = load_image(job.source)
    if args.watermark:
        image = apply_watermark(image, args.watermark)

    save_image(image, job.target, args.original_quality)
    save_image(web_display_image(image, args.min_size), job.min_path, args.min_quality)
    save_image(
        resized_image(image, args.placeholder_size),
        job.placeholder_path,
        args.placeholder_quality,
    )

    if job.action == "move" and job.source.resolve() != job.target.resolve():
        job.source.unlink()


def rebuild_config():
    subprocess.run([sys.executable, str(TOOLS_DIR / "setup.py")], check=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Add new photos to the gallery with numbering, watermarking, and generated sizes."
    )
    parser.add_argument("photos", nargs="+", help="Image files or directories of images to add.")
    parser.add_argument("--album", help="Album folder under photos/. Defaults to the only album.")
    parser.add_argument(
        "--create-album",
        action="store_true",
        help="Create --album if it does not already exist.",
    )
    parser.add_argument(
        "--watermark",
        type=Path,
        help="Watermark image path. Defaults to ./watermark.png when that file exists.",
    )
    parser.add_argument(
        "--require-watermark",
        action="store_true",
        help="Fail if no usable watermark file is found.",
    )
    parser.add_argument(
        "--skip-watermark",
        action="store_true",
        help="Do not apply a watermark even if watermark.png exists.",
    )
    parser.add_argument("--move", action="store_true", help="Move source files instead of copying them.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned work without writing files.")
    parser.add_argument("--min-size", type=int, default=1200, help="Max side length for .min images.")
    parser.add_argument(
        "--placeholder-size",
        type=int,
        default=32,
        help="Max side length for .placeholder images.",
    )
    parser.add_argument("--original-quality", type=int, default=92, help="JPEG quality for originals.")
    parser.add_argument("--min-quality", type=int, default=85, help="JPEG quality for .min images.")
    parser.add_argument(
        "--placeholder-quality",
        type=int,
        default=50,
        help="JPEG quality for .placeholder images.",
    )
    return parser.parse_args()


def validate_args(args):
    explicit_watermark = args.watermark is not None
    watermark_path = resolve_path(args.watermark or DEFAULT_WATERMARK_PATH)

    if args.skip_watermark:
        args.watermark = None
    elif watermark_path.is_file():
        args.watermark = watermark_path
    elif args.require_watermark or explicit_watermark:
        raise AddPhotoError(f"Watermark file is missing: {watermark_path}")
    else:
        args.watermark = None

    for name in ("min_size", "placeholder_size"):
        if getattr(args, name) <= 0:
            raise AddPhotoError(f"--{name.replace('_', '-')} must be positive.")

    for name in ("original_quality", "min_quality", "placeholder_quality"):
        value = getattr(args, name)
        if value < 1 or value > 100:
            raise AddPhotoError(f"--{name.replace('_', '-')} must be between 1 and 100.")


def main():
    args = parse_args()
    try:
        validate_args(args)
        album_dir = get_album_dir(args.album, args.create_album)
        sources = expand_sources(args.photos)
        jobs = plan_jobs(sources, album_dir, args.move)

        print(f'Album: "{album_dir.name}"')
        if args.watermark:
            print(f"Watermark: {args.watermark}")
        elif not args.skip_watermark:
            print("Watermark: none found; continuing without one")
        else:
            print("Watermark: skipped")
        for job in jobs:
            print(f"{job.action}: {job.source} -> {job.target.name}")
            print(f"  min: {job.min_path.name}")
            print(f"  placeholder: {job.placeholder_path.name}")

        if args.dry_run:
            print("Dry run complete; no files were written.")
            return 0

        sys.stdout.flush()
        for job in jobs:
            process_job(job, args)

        print("Refreshing config.json...")
        sys.stdout.flush()
        rebuild_config()
        return 0
    except (AddPhotoError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
