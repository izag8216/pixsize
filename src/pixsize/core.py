"""Core image processing logic for pixsize."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".ico",
})


@dataclass(frozen=True)
class ImageInfo:
    """Metadata for a single image file."""

    path: str
    width: int
    height: int
    format: str
    mode: str
    size_bytes: int
    filename: str = ""

    def __post_init__(self) -> None:
        if not self.filename:
            object.__setattr__(self, "filename", Path(self.path).name)

    @property
    def megapixels(self) -> float:
        return round(self.width * self.height / 1_000_000, 2)

    @property
    def aspect_ratio(self) -> str:
        g = _gcd(self.width, self.height)
        return f"{self.width // g}:{self.height // g}"

    @property
    def size_human(self) -> str:
        return _human_bytes(self.size_bytes)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "megapixels": self.megapixels,
            "aspect_ratio": self.aspect_ratio,
            "format": self.format,
            "mode": self.mode,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
        }


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def scan_directory(
    directory: Path,
    recursive: bool = True,
    extensions: Sequence[str] = (),
) -> list[ImageInfo]:
    """Scan a directory for image files and return metadata."""
    glob_pattern = "**/*" if recursive else "*"
    exts = set(extensions) if extensions else SUPPORTED_EXTENSIONS
    results: list[ImageInfo] = []

    for path in sorted(directory.glob(glob_pattern)):
        if not path.is_file():
            continue
        if path.suffix.lower() not in exts:
            continue
        info = get_image_info(path)
        if info is not None:
            results.append(info)

    return results


def get_image_info(path: Path) -> ImageInfo | None:
    """Extract metadata from a single image file."""
    try:
        with Image.open(path) as img:
            img.load()
            return ImageInfo(
                path=str(path),
                width=img.width,
                height=img.height,
                format=img.format or "UNKNOWN",
                mode=img.mode,
                size_bytes=path.stat().st_size,
            )
    except Exception:
        return None


def filter_images(
    images: list[ImageInfo],
    min_width: int = 0,
    max_width: int = 0,
    min_height: int = 0,
    max_height: int = 0,
    min_megapixels: float = 0.0,
    max_megapixels: float = 0.0,
    formats: Sequence[str] = (),
    square_only: bool = False,
    landscape_only: bool = False,
    portrait_only: bool = False,
) -> list[ImageInfo]:
    """Filter images by dimension and format criteria."""
    result = images
    if min_width:
        result = [i for i in result if i.width >= min_width]
    if max_width:
        result = [i for i in result if i.width <= max_width]
    if min_height:
        result = [i for i in result if i.height >= min_height]
    if max_height:
        result = [i for i in result if i.height <= max_height]
    if min_megapixels:
        result = [i for i in result if i.megapixels >= min_megapixels]
    if max_megapixels:
        result = [i for i in result if i.megapixels <= max_megapixels]
    if formats:
        fmts = {f.upper() for f in formats}
        result = [i for i in result if i.format.upper() in fmts]
    if square_only:
        result = [i for i in result if i.width == i.height]
    if landscape_only:
        result = [i for i in result if i.width > i.height]
    if portrait_only:
        result = [i for i in result if i.height > i.width]
    return result


# --- Check: rule-based validation ---

@dataclass
class CheckRule:
    """A single validation rule."""

    name: str
    min_width: int = 0
    max_width: int = 0
    min_height: int = 0
    max_height: int = 0
    allowed_formats: list[str] = field(default_factory=list)
    must_be_square: bool = False
    max_filesize_mb: float = 0.0


@dataclass
class CheckResult:
    """Result of checking one image against a rule."""

    path: str
    rule_name: str
    passed: bool
    violations: list[str] = field(default_factory=list)


def check_image(image: ImageInfo, rule: CheckRule) -> CheckResult:
    """Check an image against a rule and return violations."""
    violations: list[str] = []

    if rule.min_width and image.width < rule.min_width:
        violations.append(f"width {image.width} < min {rule.min_width}")
    if rule.max_width and image.width > rule.max_width:
        violations.append(f"width {image.width} > max {rule.max_width}")
    if rule.min_height and image.height < rule.min_height:
        violations.append(f"height {image.height} < min {rule.min_height}")
    if rule.max_height and image.height > rule.max_height:
        violations.append(f"height {image.height} > max {rule.max_height}")
    if rule.must_be_square and image.width != image.height:
        violations.append(f"not square: {image.width}x{image.height}")
    if rule.max_filesize_mb and image.size_bytes > rule.max_filesize_mb * 1_048_576:
        violations.append(f"size {image.size_human} > max {rule.max_filesize_mb}MB")
    if rule.allowed_formats:
        allowed = {f.upper() for f in rule.allowed_formats}
        if image.format.upper() not in allowed:
            violations.append(
                f"format {image.format} not in {rule.allowed_formats}"
            )

    return CheckResult(
        path=image.path,
        rule_name=rule.name,
        passed=len(violations) == 0,
        violations=violations,
    )


def load_rules(path: Path) -> list[CheckRule]:
    """Load check rules from a YAML file."""
    import yaml

    with open(path) as f:
        data = yaml.safe_load(f)

    rules: list[CheckRule] = []
    for item in data.get("rules", []):
        rules.append(CheckRule(
            name=item.get("name", "unnamed"),
            min_width=item.get("min_width", 0),
            max_width=item.get("max_width", 0),
            min_height=item.get("min_height", 0),
            max_height=item.get("max_height", 0),
            allowed_formats=item.get("allowed_formats", []),
            must_be_square=item.get("must_be_square", False),
            max_filesize_mb=item.get("max_filesize_mb", 0.0),
        ))
    return rules


# --- Resize ---

@dataclass(frozen=True)
class ResizeResult:
    """Result of a resize operation."""

    source: str
    output: str
    width: int
    height: int


def resize_image(
    source: Path,
    output: Path,
    width: int | None = None,
    height: int | None = None,
    max_dim: int | None = None,
    preset: str | None = None,
    keep_aspect: bool = True,
    overwrite: bool = False,
) -> ResizeResult:
    """Resize an image and save to output path."""
    with Image.open(source) as img:
        orig_w, orig_h = img.size
        new_w, new_h = _compute_resize_dims(
            orig_w, orig_h, width, height, max_dim, preset, keep_aspect,
        )

        if new_w == orig_w and new_h == orig_h:
            if output.exists() and not overwrite:
                return ResizeResult(
                    source=str(source), output=str(output),
                    width=new_w, height=new_h,
                )
        elif output.exists() and not overwrite:
            raise ValueError(f"Output already exists: {output}")

        resized = img.resize((new_w, new_h), Image.LANCZOS)
        output.parent.mkdir(parents=True, exist_ok=True)
        resized.save(output)

    return ResizeResult(
        source=str(source),
        output=str(output),
        width=new_w,
        height=new_h,
    )


PRESETS: dict[str, tuple[int, int]] = {
    "hd": (1280, 720),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
    "icon-16": (16, 16),
    "icon-32": (32, 32),
    "icon-64": (64, 64),
    "icon-128": (128, 128),
    "icon-256": (256, 256),
    "icon-512": (512, 512),
    "og-image": (1200, 630),
    "twitter-card": (1200, 675),
    "favicon": (32, 32),
    "thumbnail": (150, 150),
}


def _compute_resize_dims(
    orig_w: int,
    orig_h: int,
    width: int | None,
    height: int | None,
    max_dim: int | None,
    preset: str | None,
    keep_aspect: bool,
) -> tuple[int, int]:
    """Compute target dimensions for resize."""
    if preset:
        if preset not in PRESETS:
            raise ValueError(f"Unknown preset '{preset}'. Available: {', '.join(PRESETS.keys())}")
        return PRESETS[preset]

    if max_dim:
        ratio = min(max_dim / orig_w, max_dim / orig_h)
        return max(1, round(orig_w * ratio)), max(1, round(orig_h * ratio))

    if width and height:
        if keep_aspect:
            ratio = min(width / orig_w, height / orig_h)
            return max(1, round(orig_w * ratio)), max(1, round(orig_h * ratio))
        return width, height

    if width:
        if keep_aspect:
            ratio = width / orig_w
            return width, max(1, round(orig_h * ratio))
        return width, orig_h

    if height:
        if keep_aspect:
            ratio = height / orig_h
            return max(1, round(orig_w * ratio)), height
        return orig_w, height

    raise ValueError("Must specify width, height, max_dim, or preset")


def batch_resize(
    images: list[Path],
    output_dir: Path,
    width: int | None = None,
    height: int | None = None,
    max_dim: int | None = None,
    preset: str | None = None,
    keep_aspect: bool = True,
    overwrite: bool = False,
) -> list[ResizeResult]:
    """Resize multiple images in batch."""
    results: list[ResizeResult] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for src in images:
        out_path = output_dir / src.name
        result = resize_image(
            src, out_path,
            width=width, height=height,
            max_dim=max_dim, preset=preset,
            keep_aspect=keep_aspect, overwrite=overwrite,
        )
        results.append(result)

    return results


# --- Rename ---

@dataclass(frozen=True)
class RenameResult:
    """Result of a rename operation."""

    old_path: str
    new_path: str


def rename_by_pattern(
    images: list[ImageInfo],
    pattern: str,
    dry_run: bool = True,
) -> list[RenameResult]:
    """Rename images according to a pattern.

    Pattern tokens: {w}, {h}, {mp}, {fmt}, {name}, {ext}, {date}, {i}
    """
    results: list[RenameResult] = []

    for idx, info in enumerate(images):
        p = Path(info.path)
        ext = p.suffix
        name = p.stem
        mtime = datetime.fromtimestamp(p.stat().st_mtime)

        new_name = pattern.format(
            w=info.width,
            h=info.height,
            mp=info.megapixels,
            fmt=info.format.lower(),
            name=name,
            ext=ext,
            date=mtime.strftime("%Y%m%d"),
            i=idx + 1,
        )
        if not new_name.endswith(ext):
            new_name += ext

        new_path = p.parent / new_name

        if not dry_run and new_path != p:
            p.rename(new_path)

        results.append(RenameResult(
            old_path=str(p),
            new_path=str(new_path),
        ))

    return results


# --- Output formatting ---

def format_output(
    images: list[ImageInfo],
    fmt: str = "table",
) -> str:
    """Format image info list for output."""
    if fmt == "json":
        return json.dumps([i.to_dict() for i in images], indent=2, ensure_ascii=False)

    if fmt == "csv":
        lines = ["path,filename,width,height,megapixels,aspect_ratio,format,mode,size_bytes"]
        for i in images:
            lines.append(
                f"{i.path},{i.filename},{i.width},{i.height},"
                f"{i.megapixels},{i.aspect_ratio},{i.format},{i.mode},{i.size_bytes}"
            )
        return "\n".join(lines)

    # table (tsv for pipe-friendliness)
    lines = ["path\twidth\theight\tMP\taspect\tformat\tsize"]
    for i in images:
        lines.append(
            f"{i.filename}\t{i.width}\t{i.height}\t{i.megapixels}\t"
            f"{i.aspect_ratio}\t{i.format}\t{i.size_human}"
        )
    return "\n".join(lines)
