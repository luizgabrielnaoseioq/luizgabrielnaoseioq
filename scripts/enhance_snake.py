from __future__ import annotations

import argparse
import re
from pathlib import Path


def build_growth_keyframes(svg: str, max_stroke_px: float) -> str:
    """Create stepped growth synchronized with contribution cells being eaten."""
    eaten_times = sorted(
        {
            float(value)
            for value in re.findall(
                r"(\d+(?:\.\d+)?)%,100%\{fill:var\(--ce\)\}", svg
            )
        }
    )

    if not eaten_times:
        raise RuntimeError("Could not find contribution-eating timestamps in generated SVG")

    frames = ["@keyframes snakeGrow{0%{stroke-width:0}"]
    total = len(eaten_times)

    for index, percentage in enumerate(eaten_times, start=1):
        # Slightly faster growth at the beginning while still increasing on every cell.
        progress = (index / total) ** 0.72
        stroke = max_stroke_px * progress
        frames.append(f"{percentage:g}%{{stroke-width:{stroke:.3f}px}}")

    frames.append(f"100%{{stroke-width:{max_stroke_px:.3f}px}}}}")
    return "".join(frames)


def enhance_svg(path: Path, max_stroke_px: float) -> None:
    svg = path.read_text(encoding="utf-8")

    if "@keyframes snakeGrow" in svg:
        print(f"Already enhanced: {path}")
        return

    keyframes = build_growth_keyframes(svg, max_stroke_px)

    snake_base = ".s{shape-rendering:geometricPrecision;fill:var(--cs);"
    snake_enhanced = (
        ".s{shape-rendering:geometricPrecision;fill:var(--cs);"
        "stroke:var(--cs);stroke-linejoin:round;paint-order:stroke fill;"
        "vector-effect:non-scaling-stroke;"
    )

    if snake_base not in svg:
        raise RuntimeError(f"Could not find base snake style in {path}")

    svg = svg.replace(snake_base, snake_enhanced, 1)

    svg, updated_segments = re.subn(
        r"(\.s\.s\d+\{[^{}]*?animation-name:s\d+)(\})",
        r"\1,snakeGrow\2",
        svg,
    )

    if updated_segments == 0:
        raise RuntimeError(f"Could not attach growth animation to snake segments in {path}")

    svg = svg.replace("</style>", f"{keyframes}</style>", 1)
    path.write_text(svg, encoding="utf-8")
    print(
        f"Enhanced {path}: {updated_segments} segments, "
        f"growth synchronized with contribution cells"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Make Platane/snk SVG visually grow after each contribution cell eaten."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--max-stroke", type=float, default=7.0)
    args = parser.parse_args()

    for file_path in args.files:
        enhance_svg(file_path, args.max_stroke)


if __name__ == "__main__":
    main()
