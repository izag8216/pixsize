"""Tests for pixsize.cli module."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from pixsize.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def img_dir(tmp_path: Path) -> Path:
    """Create a directory with test images."""
    for name, w, h in [("a.png", 100, 80), ("b.png", 200, 150), ("c.jpg", 512, 512)]:
        img = Image.new("RGB", (w, h), color="red")
        fmt = "JPEG" if name.endswith(".jpg") else "PNG"
        img.save(tmp_path / name, fmt)
    return tmp_path


class TestScanCommand:
    def test_scan_basic(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["scan", str(img_dir), "-o", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert len(data) == 3

    def test_scan_with_filters(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["scan", str(img_dir), "--min-width", "200", "-o", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert len(data) == 2  # b.png (200x150) + c.jpg (512x512)

    def test_scan_csv_output(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["scan", str(img_dir), "-o", "csv"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert lines[0].startswith("path,")

    def test_scan_empty_dir(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["scan", str(tmp_path), "-o", "json"])
        assert result.exit_code == 0

    def test_scan_no_recursive(self, runner: CliRunner, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        Image.new("RGB", (10, 10)).save(sub / "nested.png")
        Image.new("RGB", (10, 10)).save(tmp_path / "top.png")

        result = runner.invoke(main, ["scan", str(tmp_path), "--no-recursive", "-o", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert len(data) == 1


class TestCheckCommand:
    def test_check_pass(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["check", str(img_dir / "a.png"), "--min-width", "50"])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_check_fail(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["check", str(img_dir / "a.png"), "--min-width", "200"])
        assert result.exit_code == 1
        assert "FAIL" in result.output

    def test_check_with_rules_file(self, runner: CliRunner, img_dir: Path, tmp_path: Path) -> None:
        rules = tmp_path / "rules.yaml"
        rules.write_text("""rules:
  - name: test-rule
    min_width: 50
    max_width: 300
""")
        result = runner.invoke(main, ["check", str(img_dir / "a.png"), "--rules", str(rules)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_check_directory(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["check", str(img_dir), "--min-width", "10"])
        assert result.exit_code == 0


class TestResizeCommand:
    def test_resize_by_width(self, runner: CliRunner, img_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        result = runner.invoke(main, ["resize", str(img_dir / "a.png"), "-o", str(out), "-w", "50"])
        assert result.exit_code == 0
        assert out.exists()

    def test_resize_preset(self, runner: CliRunner, img_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        result = runner.invoke(
            main, ["resize", str(img_dir / "a.png"), "-o", str(out), "--preset", "icon-32"],
        )
        assert result.exit_code == 0
        files = list(out.glob("*"))
        assert len(files) == 1

    def test_resize_batch(self, runner: CliRunner, img_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        result = runner.invoke(main, ["resize", str(img_dir), "-o", str(out), "--max-dim", "100"])
        assert result.exit_code == 0
        files = list(out.glob("*"))
        assert len(files) == 3


class TestRenameCommand:
    def test_rename_dry_run(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["rename", str(img_dir), "--pattern", "{w}x{h}_{name}{ext}"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_rename_execute(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(
            main, ["rename", str(img_dir), "--pattern", "{w}x{h}_{name}{ext}", "--no-dry-run"],
        )
        assert result.exit_code == 0

    def test_rename_with_index(self, runner: CliRunner, img_dir: Path) -> None:
        result = runner.invoke(main, ["rename", str(img_dir), "--pattern", "img_{i:03d}{ext}"])
        assert result.exit_code == 0
        assert "WOULD RENAME" in result.output


class TestVersion:
    def test_version_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "pixsize" in result.output
