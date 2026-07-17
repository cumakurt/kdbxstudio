"""Generate PNG icons from the SVG asset (requires PySide6)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def render(svg_path: Path, png_path: Path, size: int) -> None:
    renderer = QSvgRenderer(str(svg_path))
    image = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    image.save(str(png_path))


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[1]
    svg = root / "assets" / "kdbxstudio.svg"
    out_dir = root / "assets" / "icons"
    out_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication(argv)
    _ = app
    for size in (256, 128, 64, 48, 32):
        render(svg, out_dir / f"kdbxstudio-{size}.png", size)
    # Canonical path used by packaging
    render(svg, root / "assets" / "kdbxstudio.png", 256)
    print(f"Wrote icons under {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
