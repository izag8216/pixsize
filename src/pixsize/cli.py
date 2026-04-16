"""CLI entry point for pixsize."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .core import (
    CheckRule,
    ImageInfo,
    batch_resize,
    check_image,
    filter_images,
    format_output,
    get_image_info,
    load_rules,
    rename_by_pattern,
    resize_image,
    scan_directory,
)

console = Console()
err_console = Console(stderr=True)


def _version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value:
        return
    click.echo(f"pixsize {__version__}")
    ctx.exit()


@click.group()
@click.option("--version", is_flag=True, callback=_version, expose_value=False, is_eager=True)
def main() -> None:
    """pixsize -- Batch image metadata CLI for creators."""


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-r", "--recursive/--no-recursive", default=True, help="Scan subdirectories")
@click.option("--min-width", type=int, default=0, help="Minimum width filter")
@click.option("--max-width", type=int, default=0, help="Maximum width filter")
@click.option("--min-height", type=int, default=0, help="Minimum height filter")
@click.option("--max-height", type=int, default=0, help="Maximum height filter")
@click.option("--min-mp", type=float, default=0, help="Minimum megapixels filter")
@click.option("--max-mp", type=float, default=0, help="Maximum megapixels filter")
@click.option("--format", "formats", multiple=True, help="Filter by format (e.g. PNG, JPEG)")
@click.option("--square", is_flag=True, help="Only square images")
@click.option("--landscape", is_flag=True, help="Only landscape images")
@click.option("--portrait", is_flag=True, help="Only portrait images")
@click.option("-o", "--output", type=click.Choice(["table", "json", "csv"]), default="table")
def scan(
    directory: Path,
    recursive: bool,
    min_width: int,
    max_width: int,
    min_height: int,
    max_height: int,
    min_mp: float,
    max_mp: float,
    formats: tuple[str, ...],
    square: bool,
    landscape: bool,
    portrait: bool,
    output: str,
) -> None:
    """Scan directory for images and display metadata."""
    images = scan_directory(directory, recursive=recursive)

    images = filter_images(
        images,
        min_width=min_width,
        max_width=max_width,
        min_height=min_height,
        max_height=max_height,
        min_megapixels=min_mp,
        max_megapixels=max_mp,
        formats=formats,
        square_only=square,
        landscape_only=landscape,
        portrait_only=portrait,
    )

    if not images:
        err_console.print("[yellow]No images found matching criteria.[/yellow]")
        sys.exit(0)

    if output == "table" and sys.stdout.isatty():
        _print_rich_table(images)
    else:
        click.echo(format_output(images, fmt=output))


@main.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--rules", "rules_file",
    type=click.Path(exists=True, path_type=Path), help="YAML rules file",
)
@click.option("--min-width", type=int, default=0, help="Minimum width")
@click.option("--max-width", type=int, default=0, help="Maximum width")
@click.option("--min-height", type=int, default=0, help="Minimum height")
@click.option("--max-height", type=int, default=0, help="Maximum height")
@click.option("--square", is_flag=True, help="Must be square")
@click.option("--max-size-mb", type=float, default=0, help="Max file size in MB")
@click.option("--format", "formats", multiple=True, help="Allowed formats")
def check(
    paths: tuple[Path, ...],
    rules_file: Path | None,
    min_width: int,
    max_width: int,
    min_height: int,
    max_height: int,
    square: bool,
    max_size_mb: float,
    formats: tuple[str, ...],
) -> None:
    """Check images against dimension/format rules."""
    rules: list[CheckRule] = []

    if rules_file:
        rules = load_rules(rules_file)
    else:
        rules = [CheckRule(
            name="cli-rule",
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            must_be_square=square,
            max_filesize_mb=max_size_mb,
            allowed_formats=list(formats),
        )]

    all_passed = True
    for p in paths:
        if p.is_dir():
            imgs = scan_directory(p)
        else:
            info = get_image_info(p)
            imgs = [info] if info else []

        for img in imgs:
            for rule in rules:
                result = check_image(img, rule)
                if result.passed:
                    console.print(f"[green]PASS[/green] {img.filename} ({rule.name})")
                else:
                    all_passed = False
                    console.print(f"[red]FAIL[/red] {img.filename} ({rule.name})")
                    for v in result.violations:
                        console.print(f"  - {v}")

    if not all_passed:
        sys.exit(1)


def list_resize_presets() -> list[str]:
    """Return available resize preset names (for Click choice validation)."""
    from .core import PRESETS
    return list(PRESETS.keys())


@main.command()
@click.argument("sources", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output-dir", type=click.Path(path_type=Path), help="Output directory")
@click.option("-w", "--width", type=int, help="Target width")
@click.option("-h", "--height", type=int, help="Target height")
@click.option("--max-dim", type=int, help="Max dimension (keeps aspect ratio)")
@click.option("--preset", type=click.Choice(list_resize_presets()), help="Size preset")
@click.option("--keep-aspect/--no-keep-aspect", default=True, help="Maintain aspect ratio")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files")
def resize(
    sources: tuple[Path, ...],
    output_dir: Path | None,
    width: int | None,
    height: int | None,
    max_dim: int | None,
    preset: str | None,
    keep_aspect: bool,
    overwrite: bool,
) -> None:
    """Resize images to target dimensions."""
    image_files: list[Path] = []
    for s in sources:
        if s.is_dir():
            from .core import SUPPORTED_EXTENSIONS
            image_files.extend(
                p for p in sorted(s.glob("**/*"))
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
            )
        else:
            image_files.append(s)

    if not image_files:
        err_console.print("[yellow]No images found.[/yellow]")
        sys.exit(0)

    if output_dir:
        results = batch_resize(
            image_files, output_dir,
            width=width, height=height,
            max_dim=max_dim, preset=preset,
            keep_aspect=keep_aspect, overwrite=overwrite,
        )
        for r in results:
            msg = f"[green]Resized:[/green] {r.source} -> {r.output} "
            console.print(f"{msg}({r.width}x{r.height})")
    else:
        for src in image_files:
            out = src
            result = resize_image(
                src, out,
                width=width, height=height,
                max_dim=max_dim, preset=preset,
                keep_aspect=keep_aspect, overwrite=overwrite,
            )
            msg = f"[green]Resized:[/green] {result.source} -> "
            console.print(f"{msg}({result.width}x{result.height})")


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-p", "--pattern", default="{name}_{w}x{h}{ext}", help="Rename pattern")
@click.option("--recursive/--no-recursive", default=True, help="Scan subdirectories")
@click.option("--dry-run/--no-dry-run", default=True, help="Preview without renaming")
def rename(
    directory: Path,
    pattern: str,
    recursive: bool,
    dry_run: bool,
) -> None:
    """Rename images by dimension/date pattern.

    Tokens: {w} {h} {mp} {fmt} {name} {ext} {date} {i}
    """
    images = scan_directory(directory, recursive=recursive)
    if not images:
        err_console.print("[yellow]No images found.[/yellow]")
        sys.exit(0)

    results = rename_by_pattern(images, pattern, dry_run=dry_run)

    if dry_run:
        console.print("[yellow]DRY RUN -- no files renamed[/yellow]")

    for r in results:
        if r.old_path == r.new_path:
            continue
        label = "[green]RENAMED[/green]" if not dry_run else "[blue]WOULD RENAME[/blue]"
        console.print(f"{label}: {Path(r.old_path).name} -> {Path(r.new_path).name}")


def _print_rich_table(images: list[ImageInfo]) -> None:
    """Print a rich table of image info."""
    table = Table(title=f"Images ({len(images)} found)")
    table.add_column("Filename", style="cyan", no_wrap=True)
    table.add_column("Width", justify="right")
    table.add_column("Height", justify="right")
    table.add_column("MP", justify="right")
    table.add_column("Aspect")
    table.add_column("Format")
    table.add_column("Size")

    for img in images:
        table.add_row(
            img.filename,
            str(img.width),
            str(img.height),
            str(img.megapixels),
            img.aspect_ratio,
            img.format,
            img.size_human,
        )

    console.print(table)


if __name__ == "__main__":
    main()
