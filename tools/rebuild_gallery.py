#!/usr/bin/env python3

import argparse
import subprocess
import sys

from add_photo import (
    AddPhotoError,
    PHOTOS_DIR,
    TOOLS_DIR,
    derived_path,
    is_generated_path,
    is_image_path,
    is_original_image,
    load_image,
    resized_image,
    save_image,
)


def iter_album_dirs():
    if not PHOTOS_DIR.is_dir():
        return []
    return sorted(path for path in PHOTOS_DIR.iterdir() if path.is_dir())


def iter_originals():
    for album_dir in iter_album_dirs():
        for path in sorted(album_dir.iterdir()):
            if is_original_image(path):
                yield path


def iter_generated_files():
    if not PHOTOS_DIR.is_dir():
        return
    for path in PHOTOS_DIR.rglob("*"):
        if path.is_file() and is_image_path(path) and is_generated_path(path):
            yield path


def original_for_generated(path):
    name = path.name
    for marker in (".min.", ".placeholder."):
        if marker in name:
            return path.with_name(name.replace(marker, ".", 1))
    return None


def rebuild_sidecars(original, args):
    image = load_image(original)
    min_path = derived_path(original, "min")
    placeholder_path = derived_path(original, "placeholder")

    save_image(resized_image(image, args.min_size), min_path, args.min_quality)
    save_image(
        resized_image(image, args.placeholder_size),
        placeholder_path,
        args.placeholder_quality,
    )
    return min_path, placeholder_path


def rebuild_config():
    subprocess.run([sys.executable, str(TOOLS_DIR / "setup.py")], check=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rebuild gallery sidecar images and config without renaming or watermarking originals."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show planned work without writing files.")
    parser.add_argument(
        "--clean-orphans",
        action="store_true",
        help="Remove .min and .placeholder files whose original image no longer exists.",
    )
    parser.add_argument("--skip-config", action="store_true", help="Do not refresh config.json.")
    parser.add_argument("--min-size", type=int, default=1200, help="Max side length for .min images.")
    parser.add_argument(
        "--placeholder-size",
        type=int,
        default=32,
        help="Max side length for .placeholder images.",
    )
    parser.add_argument("--min-quality", type=int, default=85, help="JPEG quality for .min images.")
    parser.add_argument(
        "--placeholder-quality",
        type=int,
        default=50,
        help="JPEG quality for .placeholder images.",
    )
    return parser.parse_args()


def validate_args(args):
    for name in ("min_size", "placeholder_size"):
        if getattr(args, name) <= 0:
            raise AddPhotoError(f"--{name.replace('_', '-')} must be positive.")

    for name in ("min_quality", "placeholder_quality"):
        value = getattr(args, name)
        if value < 1 or value > 100:
            raise AddPhotoError(f"--{name.replace('_', '-')} must be between 1 and 100.")


def run(args):
    validate_args(args)
    originals = list(iter_originals())

    print(f"Found {len(originals)} original image(s).")
    for original in originals:
        min_path = derived_path(original, "min")
        placeholder_path = derived_path(original, "placeholder")
        print(f"rebuild: {original.relative_to(PHOTOS_DIR)}")
        print(f"  min: {min_path.name}")
        print(f"  placeholder: {placeholder_path.name}")

    orphaned = [
        path
        for path in iter_generated_files()
        if (original_for_generated(path) is not None and not original_for_generated(path).exists())
    ]
    if orphaned:
        action = "remove" if args.clean_orphans else "keep"
        print(f"{action}: {len(orphaned)} orphaned generated file(s)")
        for path in orphaned:
            print(f"  {path.relative_to(PHOTOS_DIR)}")

    if args.dry_run:
        print("Dry run complete; no files were written.")
        return 0

    for original in originals:
        rebuild_sidecars(original, args)

    if args.clean_orphans:
        for path in orphaned:
            path.unlink()

    if not args.skip_config:
        print("Refreshing config.json...")
        sys.stdout.flush()
        rebuild_config()

    return 0


def main():
    args = parse_args()
    try:
        return run(args)
    except (AddPhotoError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
