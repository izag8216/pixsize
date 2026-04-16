[![en](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![ja](https://img.shields.io/badge/lang-日本語-red.svg)](README.ja.md)

![pixsize](https://capsule-render.vercel.app/api?type=candy&color=gradient&customColorList=12&text=pixsize&fontSize=42&fontColor=ffffff&animation=twinkling&fontAlignY=35&desc=Batch%20Image%20Metadata%20CLI%20for%20Creators&descAlignY=55&descSize=16)

[![Python](https://img.shields.io/badge/Python-3.10+-for-the-badge?style=for-the-badge&logo=python&logoColor=white&color=3776AB)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-Pytest-for-the-badge?style=for-the-badge&logo=pytest&logoColor=white&color=0A9EDC)](https://pytest.org)
[![Coverage](https://img.shields.io/badge/Coverage-80%25+-for-the-badge?style=for-the-badge&logo=codecov&logoColor=white&color=F01F7A)](https://codecov.io)
[![License](https://img.shields.io/badge/License-MIT-for-the-badge?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=green)](LICENSE)
[![Linter](https://img.shields.io/badge/Linter-Ruff-for-the-badge?style=for-the-badge&logo=ruff&logoColor=white&color=D2FFED)](https://docs.astral.sh/ruff/)

**pixsize** is a lightweight CLI for game devs, designers, and web developers who need to scan, validate, resize, and batch-rename images -- without the bloat of ImageMagick.

## Features

- **`pixsize scan`** -- Scan directories, filter by dimensions/format/aspect ratio
- **`pixsize check`** -- Validate images against YAML rules (sprite sheets, icon sizes, web specs)
- **`pixsize resize`** -- Batch resize with presets (HD, 4K, icons, OG images) or custom dimensions
- **`pixsize rename`** -- Rename files by pattern (dimensions, date, index)
- **Multiple outputs** -- Table, JSON, CSV (pipe-friendly)
- **Zero API dependencies** -- Pure Python + Pillow

## Install

```bash
pip install pixsize
```

## Quick Start

```bash
# Scan current directory for images
pixsize scan .

# Scan with filters
pixsize scan ./sprites --min-width 32 --max-width 256 --square -o json

# Check images against rules
pixsize check ./icons --rules rules.yaml
pixsize check ./assets --min-width 100 --max-height 1000

# Resize with presets
pixsize resize ./photos -o ./resized --preset fhd
pixsize resize icon.png -w 32 -h 32 --no-keep-aspect

# Rename by pattern
pixsize rename ./assets --pattern "{w}x{h}_{name}{ext}" --dry-run
pixsize rename ./assets --pattern "img_{i:03d}{ext}" --no-dry-run
```

## Commands

### `pixsize scan`

Scan directories and display image metadata.

```bash
pixsize scan DIRECTORY [OPTIONS]

Options:
  -r, --recursive / --no-recursive   Scan subdirectories (default: true)
  --min-width INT                     Minimum width filter
  --max-width INT                     Maximum width filter
  --min-height INT                    Minimum height filter
  --max-height INT                    Maximum height filter
  --min-mp FLOAT                      Minimum megapixels filter
  --max-mp FLOAT                      Maximum megapixels filter
  --format TEXT                       Filter by format (repeatable)
  --square                            Only square images
  --landscape                         Only landscape images
  --portrait                          Only portrait images
  -o, --output [table|json|csv]       Output format (default: table)
```

### `pixsize check`

Validate images against dimension and format rules.

```bash
pixsize check PATHS... [OPTIONS]

Options:
  --rules FILE           YAML rules file
  --min-width INT        Minimum width
  --max-width INT        Maximum width
  --min-height INT       Minimum height
  --max-height INT       Maximum height
  --square               Must be square
  --max-size-mb FLOAT    Max file size in MB
  --format TEXT          Allowed formats (repeatable)
```

**Rules file example (`rules.yaml`):**

```yaml
rules:
  - name: sprite-tile
    min_width: 16
    max_width: 256
    must_be_square: true
    allowed_formats: [PNG]

  - name: web-upload
    max_filesize_mb: 5.0
    max_width: 4096
    max_height: 4096
    allowed_formats: [PNG, JPEG, WEBP]
```

### `pixsize resize`

Resize images with presets or custom dimensions.

```bash
pixsize resize SOURCES... [OPTIONS]

Options:
  -o, --output-dir PATH       Output directory
  -w, --width INT             Target width
  -h, --height INT            Target height
  --max-dim INT               Max dimension (keeps aspect ratio)
  --preset PRESET             Size preset
  --keep-aspect / --no-keep-aspect  Maintain aspect ratio (default: true)
  --overwrite                 Overwrite existing files
```

**Presets:** `hd`, `fhd`, `2k`, `4k`, `icon-16`, `icon-32`, `icon-64`, `icon-128`, `icon-256`, `icon-512`, `og-image`, `twitter-card`, `favicon`, `thumbnail`

### `pixsize rename`

Rename images by pattern tokens.

```bash
pixsize rename DIRECTORY [OPTIONS]

Options:
  -p, --pattern TEXT        Rename pattern (default: {name}_{w}x{h}{ext})
  --recursive / --no-recursive  Scan subdirectories (default: true)
  --dry-run / --no-dry-run  Preview without renaming (default: true)
```

**Pattern tokens:** `{w}` width, `{h}` height, `{mp}` megapixels, `{fmt}` format, `{name}` original name, `{ext}` extension, `{date}` YYYYMMDD, `{i}` index

## Development

```bash
# Clone
git clone https://github.com/izag8216/pixsize.git
cd pixsize

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=pixsize

# Lint
ruff check src/ tests/
```

## License

MIT License -- see [LICENSE](LICENSE) for details.

---

![footer](https://capsule-render.vercel.app/api?type=candy&color=gradient&customColorList=12&section=footer&fontSize=14&text=Made%20with%20pixsize&fontColor=ffffff)
