from __future__ import annotations

import argparse
import re
from pathlib import Path

SEGMENT_RE = re.compile(r"(\.s\.s(\d+)\{[^{}]*?animation-name:s\d+)(\})")


def extract_eaten_times(svg: str) -> list[float]:
    """Return the percentages where contribution cells disappear after being eaten."""
    times = sorted(
        {
            float(value)
            for value in re.findall(
                r"(\d+(?:\.\d+)?)%,100%\{fill:var\(--ce\)\}", svg
            )
        }
    )

    if not times:
        raise RuntimeError(
            "Could not find contribution-eating timestamps in generated SVG"
        )

    return times


def build_reveal_animation(name: str, reveal_at: float) -> str:
    """Keep a body segment hidden until the snake has eaten enough cells."""
    hold = max(0.0, reveal_at - 0.02)
    return (
        f"@keyframes {name}{{"
        f"0%,{hold:g}%{{opacity:0}}"
        f"{reveal_at:g}%,100%{{opacity:1}}"
        f"}}"
    )


def enhance_svg(path: Path, initial_visible: int) -> None:
    svg = path.read_text(encoding="utf-8")

    if "snakeReveal" in svg:
        print(f"Already enhanced: {path}")
        return

    eaten_times = extract_eaten_times(svg)
    segments = list(SEGMENT_RE.finditer(svg))

    if not segments:
        raise RuntimeError(f"Could not find snake segments in {path}")

    total_segments = len(segments)
    initial_visible = max(1, min(initial_visible, total_segments))
    extra_segments = total_segments - initial_visible

    reveal_keyframes: list[str] = []
    replacements: list[tuple[str, str]] = []

    for position, match in enumerate(segments):
        full_rule = match.group(0)
        segment_index = int(match.group(2))
        rule_prefix = match.group(1)
        reveal_name = f"snakeReveal{segment_index}"

        if position < initial_visible or extra_segments == 0:
            reveal_keyframes.append(
                f"@keyframes {reveal_name}{{0%,100%{{opacity:1}}}}"
            )
        else:
            growth_progress = (position - initial_visible + 1) / extra_segments
            eaten_index = round((len(eaten_times) - 1) * growth_progress)
            reveal_at = eaten_times[min(len(eaten_times) - 1, eaten_index)]
            reveal_keyframes.append(
                build_reveal_animation(reveal_name, reveal_at)
            )

        replacement = (
            f"{rule_prefix};opacity:1;"
            f"animation-name:s{segment_index},{reveal_name}{match.group(3)}"
        )
        replacements.append((full_rule, replacement))

    snake_style = ".s{shape-rendering:geometricPrecision;fill:var(--cs);"
    enhanced_style = (
        ".s{shape-rendering:geometricPrecision;fill:var(--cs);"
        "will-change:opacity;"
    )

    if snake_style in svg:
        svg = svg.replace(snake_style, enhanced_style, 1)

    for original, replacement in replacements:
        svg = svg.replace(original, replacement, 1)

    svg = svg.replace(
        "</style>",
        "".join(reveal_keyframes) + "</style>",
        1,
    )

    path.write_text(svg, encoding="utf-8")
    print(
        f"Enhanced {path}: {total_segments} body segments, "
        "snake now grows in length while eating contributions"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Make Platane/snk SVG grow in length as contribution cells are eaten."
        )
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--initial-visible", type=int, default=4)
    args = parser.parse_args()

    for file_path in args.files:
        enhance_svg(file_path, args.initial_visible)


if __name__ == "__main__":
    main()
