# Gallery Workflow

Forked from [andyzg/gallery](https://github.com/andyzg/gallery).

![Gallery webpage preview](assets/preview.png)

This is a static photo gallery. The site reads `config.json`, which points each
photo to three files:

- the original image used for zooming
- a `.min` image used in the page
- a tiny `.placeholder` image used while lazy loading

The normal workflow is to add originals with `tools/add_photo.py`. It assigns
the next number, optionally applies a watermark, creates the generated versions,
and refreshes `config.json`. Web-display `.min` images are sharpened after
Lanczos downsampling with settings closely matching the former ImageMagick
`-unsharp 0.5x0.5+0.5+0.008` step. Originals and loading placeholders are not
sharpened.

## Photo Order

Set `photo_sort` in `_config.yml` to choose how each album is ordered:

- `colorspace` follows an OKLCh hue path from purple through blue, cyan, green,
  yellow, orange, and red in visual reading order (left-to-right, then
  top-to-bottom). Within each nearby hue family, it chooses the path that first
  minimizes the largest adjacent lightness jump, then minimizes the remaining
  squared lightness changes. Hue families never cross one another.
- `shuffle` randomizes the order on every page load.
- `filename` keeps the order from `config.json`.

The colorspace coordinates and final rank are calculated from each web-display
image when `config.json` is rebuilt, so visitors do not pay the cost of image
analysis.
The old `shuffle` boolean remains as a fallback for configs that do not define
`photo_sort`.

Prerequisite:

```bash
python3 -m pip install Pillow
```

## Start Your Own Gallery

Remove the sample photos, then add your first batch into a new album:

```bash
rm -rf "photos/Yuyang Wang's Gallery"
python3 tools/add_photo.py --album "My Gallery" --create-album ~/Pictures/first-batch/
```

If you want watermarks, put a transparent PNG named `watermark.png` at the
project root before adding photos. Watermarking is optional: when
`watermark.png` is missing, photos are processed without one. Use
`--require-watermark` when you want the command to fail instead.

## Add Photos

Add one photo:

```bash
python3 tools/add_photo.py ~/Desktop/new-photo.jpg
```

Add several photos or a whole directory:

```bash
python3 tools/add_photo.py ~/Desktop/photo-1.jpg ~/Desktop/photo-2.jpg
python3 tools/add_photo.py ~/Desktop/new-gallery-picks/
```

Preview the numbering before writing files:

```bash
python3 tools/add_photo.py --dry-run ~/Desktop/new-photo.jpg
```

Useful options:

- `--album "Album Name"` chooses an album when more than one exists.
- `--create-album` creates the chosen album for a first import.
- `--move` moves source files instead of copying them.
- `--skip-watermark` ignores `watermark.png` for this run.
- `--require-watermark` refuses to import without a watermark.

## Rebuild Generated Files

If originals are already in `photos/` and you only need to rebuild `.min`,
`.placeholder`, and `config.json`, run:

```bash
./setup.command
```

That root command is now only a compatibility wrapper for:

```bash
python3 tools/rebuild_gallery.py
```

Pass original paths to rebuild only selected photos:

```bash
python3 tools/rebuild_gallery.py --skip-config \
  "photos/My Gallery/my_gallery_031.jpeg" \
  "photos/My Gallery/my_gallery_032.jpeg"
```

It does not rename originals and does not apply watermarks. Watermarking happens
when photos are first added with `tools/add_photo.py`.
