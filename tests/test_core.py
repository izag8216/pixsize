"""Tests for pixsize.core module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from pixsize.core import (
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


class TestImageInfo:
    def test_basic_properties(self) -> None:
        info = ImageInfo(
            path="/img/test.png", width=100, height=80,
            format="PNG", mode="RGB", size_bytes=1024,
        )
        assert info.filename == "test.png"
        assert info.megapixels == 0.01
        assert info.aspect_ratio == "5:4"
        assert info.size_human == "1.0 KB"

    def test_human_bytes(self) -> None:
        assert "KB" in ImageInfo("", 1, 1, "", "", 2048).size_human
        assert "MB" in ImageInfo("", 1, 1, "", "", 2_097_152).size_human

    def test_to_dict(self) -> None:
        info = ImageInfo(
            path="/img/a.png", width=10, height=10,
            format="PNG", mode="RGB", size_bytes=100,
        )
        d = info.to_dict()
        assert d["width"] == 10
        assert d["filename"] == "a.png"
        assert "aspect_ratio" in d

    def test_square_aspect_ratio(self) -> None:
        info = ImageInfo("", 256, 256, "", "", 0)
        assert info.aspect_ratio == "1:1"


class TestScanDirectory:
    def test_scan_finds_images(self, tmp_images: list[Path]) -> None:
        directory = tmp_images[0].parent
        results = scan_directory(directory, recursive=False)
        assert len(results) == 4

    def test_scan_recursive(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        img = Image.new("RGB", (50, 50))
        img.save(sub / "nested.png")
        img.save(tmp_path / "top.png")

        results = scan_directory(tmp_path, recursive=True)
        assert len(results) == 2

    def test_scan_nonrecursive(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        img = Image.new("RGB", (50, 50))
        img.save(sub / "nested.png")
        img.save(tmp_path / "top.png")

        results = scan_directory(tmp_path, recursive=False)
        assert len(results) == 1

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        results = scan_directory(tmp_path)
        assert results == []

    def test_scan_ignores_non_images(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("hello")
        (tmp_path / "data.json").write_text("{}")
        results = scan_directory(tmp_path)
        assert results == []

    def test_scan_with_extension_filter(self, tmp_images: list[Path]) -> None:
        directory = tmp_images[0].parent
        results = scan_directory(directory, extensions={".jpg"})
        assert len(results) == 1
        assert results[0].format == "JPEG"


class TestGetImageInfo:
    def test_valid_image(self, tmp_image: Path) -> None:
        info = get_image_info(tmp_image)
        assert info is not None
        assert info.width == 100
        assert info.height == 80
        assert info.format == "PNG"

    def test_invalid_path(self, tmp_path: Path) -> None:
        info = get_image_info(tmp_path / "nonexistent.png")
        assert info is None

    def test_corrupt_file(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.png"
        bad.write_bytes(b"not an image")
        info = get_image_info(bad)
        assert info is None


class TestFilterImages:
    def _make_info(self, w: int, h: int, fmt: str = "PNG") -> ImageInfo:
        return ImageInfo(
            path=f"/img/{w}x{h}.{fmt.lower()}", width=w, height=h,
            format=fmt, mode="RGB", size_bytes=1000,
        )

    def test_min_width(self) -> None:
        imgs = [self._make_info(100, 100), self._make_info(200, 200)]
        result = filter_images(imgs, min_width=150)
        assert len(result) == 1
        assert result[0].width == 200

    def test_max_height(self) -> None:
        imgs = [self._make_info(100, 100), self._make_info(100, 200)]
        result = filter_images(imgs, max_height=150)
        assert len(result) == 1

    def test_format_filter(self) -> None:
        imgs = [self._make_info(100, 100, "PNG"), self._make_info(100, 100, "JPEG")]
        result = filter_images(imgs, formats=["PNG"])
        assert len(result) == 1

    def test_square_only(self) -> None:
        imgs = [self._make_info(100, 100), self._make_info(200, 100)]
        result = filter_images(imgs, square_only=True)
        assert len(result) == 1

    def test_landscape_only(self) -> None:
        imgs = [self._make_info(200, 100), self._make_info(100, 200)]
        result = filter_images(imgs, landscape_only=True)
        assert len(result) == 1

    def test_portrait_only(self) -> None:
        imgs = [self._make_info(200, 100), self._make_info(100, 200)]
        result = filter_images(imgs, portrait_only=True)
        assert len(result) == 1

    def test_megapixels_filter(self) -> None:
        imgs = [self._make_info(100, 100), self._make_info(2000, 2000)]
        result = filter_images(imgs, min_megapixels=1.0)
        assert len(result) == 1


class TestCheck:
    def test_pass_rule(self) -> None:
        info = ImageInfo("", 100, 100, "PNG", "RGB", 500)
        rule = CheckRule(name="test", min_width=50, max_width=200)
        result = check_image(info, rule)
        assert result.passed

    def test_fail_min_width(self) -> None:
        info = ImageInfo("", 30, 30, "PNG", "RGB", 500)
        rule = CheckRule(name="test", min_width=50)
        result = check_image(info, rule)
        assert not result.passed
        assert any("width" in v for v in result.violations)

    def test_fail_not_square(self) -> None:
        info = ImageInfo("", 100, 80, "PNG", "RGB", 500)
        rule = CheckRule(name="test", must_be_square=True)
        result = check_image(info, rule)
        assert not result.passed

    def test_fail_format(self) -> None:
        info = ImageInfo("", 100, 100, "BMP", "RGB", 500)
        rule = CheckRule(name="test", allowed_formats=["PNG", "JPEG"])
        result = check_image(info, rule)
        assert not result.passed

    def test_fail_filesize(self) -> None:
        info = ImageInfo("", 100, 100, "PNG", "RGB", 10_000_000)
        rule = CheckRule(name="test", max_filesize_mb=5.0)
        result = check_image(info, rule)
        assert not result.passed

    def test_load_rules_yaml(self, rules_file: Path) -> None:
        rules = load_rules(rules_file)
        assert len(rules) == 2
        assert rules[0].name == "icon-size"
        assert rules[0].must_be_square is True
        assert rules[1].max_filesize_mb == 5.0


class TestResize:
    def test_resize_by_width(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "resized.png"
        result = resize_image(tmp_image, out, width=50)
        assert result.width == 50
        assert result.height == 40  # keep aspect: 80 * 50/100

    def test_resize_by_height(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "resized.png"
        result = resize_image(tmp_image, out, height=40)
        assert result.height == 40
        assert result.width == 50

    def test_resize_max_dim(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "resized.png"
        result = resize_image(tmp_image, out, max_dim=50)
        assert result.width <= 50
        assert result.height <= 50

    def test_resize_preset(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "resized.png"
        result = resize_image(tmp_image, out, preset="icon-32")
        assert result.width == 32
        assert result.height == 32

    def test_resize_no_keep_aspect(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "resized.png"
        result = resize_image(tmp_image, out, width=50, height=50, keep_aspect=False)
        assert result.width == 50
        assert result.height == 50

    def test_resize_unknown_preset(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "resized.png"
        with pytest.raises(ValueError, match="Unknown preset"):
            resize_image(tmp_image, out, preset="mega-hd")

    def test_batch_resize(self, tmp_images: list[Path], tmp_path: Path) -> None:
        out_dir = tmp_path / "output"
        results = batch_resize(tmp_images, out_dir, max_dim=100)
        assert len(results) == 4
        for r in results:
            assert r.width <= 100
            assert r.height <= 100

    def test_resize_output_dir_created(self, tmp_image: Path, tmp_path: Path) -> None:
        out = tmp_path / "deep" / "nested" / "dir" / "out.png"
        resize_image(tmp_image, out, width=50)
        assert out.exists()


class TestRename:
    def test_rename_dry_run(self, tmp_images: list[Path]) -> None:
        directory = tmp_images[0].parent
        images = scan_directory(directory, recursive=False)
        results = rename_by_pattern(images, "{w}x{h}_{name}{ext}", dry_run=True)
        assert len(results) == 4
        # Files should not actually change
        for img in tmp_images:
            assert img.exists()

    def test_rename_with_dimensions(self, tmp_images: list[Path]) -> None:
        directory = tmp_images[0].parent
        images = scan_directory(directory, recursive=False)
        results = rename_by_pattern(images, "{w}x{h}{ext}", dry_run=False)
        assert len(results) == 4
        # Check that files were renamed
        for r in results:
            if r.old_path != r.new_path:
                assert Path(r.new_path).exists()

    def test_rename_with_index(self, tmp_images: list[Path]) -> None:
        directory = tmp_images[0].parent
        images = scan_directory(directory, recursive=False)
        results = rename_by_pattern(images, "img_{i:03d}{ext}", dry_run=True)
        names = [Path(r.new_path).name for r in results]
        assert "img_001.png" in names or "img_001.jpg" in names


class TestFormatOutput:
    def test_json_output(self) -> None:
        info = ImageInfo("/a.png", 100, 80, "PNG", "RGB", 1024)
        output = format_output([info], fmt="json")
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["width"] == 100

    def test_csv_output(self) -> None:
        info = ImageInfo("/a.png", 100, 80, "PNG", "RGB", 1024)
        output = format_output([info], fmt="csv")
        lines = output.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "width" in lines[0]

    def test_table_output(self) -> None:
        info = ImageInfo("/a.png", 100, 80, "PNG", "RGB", 1024)
        output = format_output([info], fmt="table")
        assert "a.png" in output
        assert "100" in output
