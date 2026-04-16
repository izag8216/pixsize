"""Shared test fixtures for pixsize."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def tmp_image(tmp_path: Path) -> Path:
    """Create a simple 100x80 PNG test image."""
    img = Image.new("RGB", (100, 80), color="red")
    path = tmp_path / "test.png"
    img.save(path, "PNG")
    return path


@pytest.fixture
def tmp_images(tmp_path: Path) -> list[Path]:
    """Create multiple test images with different sizes."""
    specs = [
        ("small.png", 32, 32, "blue"),
        ("medium.png", 200, 150, "green"),
        ("large.png", 1920, 1080, "red"),
        ("square.jpg", 512, 512, "yellow"),
    ]
    paths = []
    for name, w, h, color in specs:
        img = Image.new("RGB", (w, h), color=color)
        p = tmp_path / name
        fmt = "JPEG" if name.endswith(".jpg") else "PNG"
        img.save(p, fmt)
        paths.append(p)
    return paths


@pytest.fixture
def rules_file(tmp_path: Path) -> Path:
    """Create a sample YAML rules file."""
    content = """rules:
  - name: icon-size
    min_width: 16
    max_width: 256
    min_height: 16
    max_height: 256
    must_be_square: true
  - name: web-image
    max_filesize_mb: 5.0
    allowed_formats:
      - PNG
      - JPEG
"""
    path = tmp_path / "rules.yaml"
    path.write_text(content)
    return path
