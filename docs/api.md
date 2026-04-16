# API Reference

## Core Module (`pixsize.core`)

### `scan_directory(directory, recursive=True, extensions=())`

Scan a directory for image files and return metadata.

**Parameters:**
- `directory` (Path): Directory to scan
- `recursive` (bool): Include subdirectories
- `extensions` (Sequence[str]): File extensions to include (default: all supported)

**Returns:** `list[ImageInfo]`

### `get_image_info(path)`

Extract metadata from a single image file.

**Parameters:**
- `path` (Path): Path to image file

**Returns:** `ImageInfo | None`

### `filter_images(images, **criteria)`

Filter a list of ImageInfo objects by dimension and format criteria.

**Keyword Args:** `min_width`, `max_width`, `min_height`, `max_height`, `min_megapixels`, `max_megapixels`, `formats`, `square_only`, `landscape_only`, `portrait_only`

**Returns:** `list[ImageInfo]`

### `check_image(image, rule)`

Check an image against a CheckRule.

**Returns:** `CheckResult`

### `resize_image(source, output, **options)`

Resize a single image.

**Keyword Args:** `width`, `height`, `max_dim`, `preset`, `keep_aspect`, `overwrite`

**Returns:** `ResizeResult`

### `rename_by_pattern(images, pattern, dry_run=True)`

Rename images according to a pattern string.

**Pattern tokens:** `{w}`, `{h}`, `{mp}`, `{fmt}`, `{name}`, `{ext}`, `{date}`, `{i}`

**Returns:** `list[RenameResult]`

## Data Classes

### `ImageInfo`

| Field | Type | Description |
|-------|------|-------------|
| `path` | str | Full file path |
| `width` | int | Width in pixels |
| `height` | int | Height in pixels |
| `format` | str | Image format (PNG, JPEG, etc.) |
| `mode` | str | Color mode (RGB, RGBA, etc.) |
| `size_bytes` | int | File size in bytes |
| `megapixels` | float | Computed megapixels |
| `aspect_ratio` | str | Simplified ratio (e.g. "16:9") |

### `CheckRule`

| Field | Type | Default |
|-------|------|---------|
| `name` | str | required |
| `min_width` | int | 0 |
| `max_width` | int | 0 |
| `min_height` | int | 0 |
| `max_height` | int | 0 |
| `allowed_formats` | list[str] | [] |
| `must_be_square` | bool | False |
| `max_filesize_mb` | float | 0.0 |

## Presets

| Preset | Dimensions |
|--------|------------|
| `hd` | 1280x720 |
| `fhd` | 1920x1080 |
| `2k` | 2560x1440 |
| `4k` | 3840x2160 |
| `icon-16` | 16x16 |
| `icon-32` | 32x32 |
| `icon-64` | 64x64 |
| `icon-128` | 128x128 |
| `icon-256` | 256x256 |
| `icon-512` | 512x512 |
| `og-image` | 1200x630 |
| `twitter-card` | 1200x675 |
| `favicon` | 32x32 |
| `thumbnail` | 150x150 |
