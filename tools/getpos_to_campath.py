#!/usr/bin/env python3
"""Build an HLAE campath from CS2 `getpos` output.

Fly to each spot in a demo, run `getpos` in the console, and copy the line it
prints, which looks like:

    setpos 1234.000000 -567.000000 128.031250;setang 12.345678 90.000000 0.000000

Give this script four of those lines (start, two middle points, end) and it
writes a campath XML file that `mirv_campath load` accepts. HLAE smooths the
path between the keyframes, so four points are enough for a clean shot.

Paths default to 20 seconds. The script prints the camera speed and warns when
the length or speed is far from what suits cs2-highlights-maker clips.

Examples:

    # Lines as arguments, default 20 second path, written into the map directory
    python3 tools/getpos_to_campath.py -o de_nuke/a-site-flyby.xml \\
        "setpos ...;setang ..." "setpos ...;setang ..." \\
        "setpos ...;setang ..." "setpos ...;setang ..."

    # Lines from a text file (one getpos line per row), 12 second path
    python3 tools/getpos_to_campath.py -d 12 -i points.txt -o de_nuke/a-site-flyby-short.xml

    # No lines given: prompts for them one at a time
    python3 tools/getpos_to_campath.py -o de_nuke/a-site-flyby.xml

Only the Python standard library is used.
"""

import argparse
import math
import re
import sys
from pathlib import Path

POINT_COUNT = 4

# cs2-highlights-maker never stretches a path to fit a clip: a longer path is cut
# off, a shorter one stops early. Clips are lead-in 4s + action + lead-out 3s, and
# reference packs sit around 20-25s at a slow drift, so warn outside these ranges.
DEFAULT_DURATION = 20.0
SHORT_DURATION = 8.0  # seconds; shorter paths end before most clips do
LONG_DURATION = 30.0  # seconds; the end of longer paths rarely gets played
SLOW_SPEED = 10.0  # units per second; slower barely reads as movement
FAST_SPEED = 100.0  # units per second; faster looks rushed (walking is 250)

NUMBER = r"(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
SETPOS_RE = re.compile(r"setpos(?:_exact)?\s+" + r"\s+".join([NUMBER] * 3))
SETANG_RE = re.compile(r"setang(?:_exact)?\s+" + r"\s+".join([NUMBER] * 3))

# Same header comment HLAE writes with `mirv_campath save`.
HEADER = """<?xml version="1.0" encoding="utf-8"?>
<campath>
\t<points>
\t\t<!--Points are in Quake coordinates, meaning x=forward, y=left, z=up and rotation order is first rx, then ry and lastly rz.
Rotation direction follows the right-hand grip rule.
rx (roll), ry (pitch), rz(yaw) are the Euler angles in degrees.
qw, qx, qy, qz are the quaternion values.
When read it is sufficient that either rx, ry, rz OR qw, qx, qy, qz are present.
If both are present then qw, qx, qy, qz take precedence.-->
"""
FOOTER = "\t</points>\n</campath>\n"


class Point:
    def __init__(self, x, y, z, pitch, yaw, roll):
        self.x, self.y, self.z = x, y, z
        self.pitch, self.yaw, self.roll = pitch, yaw, roll

    def distance_to(self, other):
        return math.dist((self.x, self.y, self.z), (other.x, other.y, other.z))


def parse_getpos(line):
    """Parse one `getpos` line into a Point, or raise ValueError."""
    pos = SETPOS_RE.search(line)
    ang = SETANG_RE.search(line)
    if not pos or not ang:
        raise ValueError(
            f"not a getpos line (expected 'setpos X Y Z;setang PITCH YAW ROLL'): {line.strip()!r}"
        )
    x, y, z = (float(v) for v in pos.groups())
    pitch, yaw, roll = (float(v) for v in ang.groups())
    return Point(x, y, z, pitch, yaw, roll)


def quaternion(roll, pitch, yaw):
    """Euler angles in degrees to (qw, qx, qy, qz), matching HLAE's output."""
    r, p, y = (math.radians(a) / 2 for a in (roll, pitch, yaw))
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    )


def unwrap_yaw(points):
    """Keep yaw continuous so 170 -> -170 turns 20 degrees, not 340."""
    for prev, cur in zip(points, points[1:]):
        delta = (cur.yaw - prev.yaw + 180) % 360 - 180
        cur.yaw = prev.yaw + delta


def keyframe_times(points, duration, start, spacing):
    """Times for each point. 'distance' keeps the camera at a steady speed."""
    if spacing == "even":
        weights = [1.0] * (len(points) - 1)
    else:
        weights = [a.distance_to(b) for a, b in zip(points, points[1:])]
        if sum(weights) == 0:
            weights = [1.0] * (len(points) - 1)
    total = sum(weights)
    times = [start]
    for w in weights:
        times.append(times[-1] + duration * w / total)
    return times


def path_length(points):
    return sum(a.distance_to(b) for a, b in zip(points, points[1:]))


def pacing_warnings(duration, speed):
    """Warnings for a path whose length or speed suits highlight clips poorly."""
    warnings = []
    if duration < SHORT_DURATION:
        warnings.append(f"{duration:g}s is short: most clips run longer, so the camera will stop early")
    elif duration > LONG_DURATION:
        warnings.append(f"{duration:g}s is long: clips rarely run this long, so the end will be cut off")
    # A path that only turns in place has no speed to judge.
    if 0 < speed < SLOW_SPEED:
        warnings.append(f"{speed:.0f} units/s is very slow: shorten -d or spread the points out")
    elif speed > FAST_SPEED:
        warnings.append(f"{speed:.0f} units/s is fast: lengthen -d or move the points closer")
    return warnings


def build_campath(points, times, fovs):
    lines = [HEADER]
    previous = None
    for p, t, fov in zip(points, times, fovs):
        q = quaternion(p.roll, p.pitch, p.yaw)
        # q and -q are the same rotation; keep neighbours on the same side so
        # interpolation never takes the long way round.
        if previous and sum(a * b for a, b in zip(q, previous)) < 0:
            q = tuple(-c for c in q)
        previous = q
        qw, qx, qy, qz = q
        lines.append(
            f'\t\t<p t="{t:.6f}" x="{p.x:.6f}" y="{p.y:.6f}" z="{p.z:.6f}" fov="{fov:.6f}"'
            f' rx="{p.roll:.6f}" ry="{p.pitch:.6f}" rz="{p.yaw:.6f}"'
            f' qw="{qw:.6f}" qx="{qx:.6f}" qy="{qy:.6f}" qz="{qz:.6f}"/>\n'
        )
    lines.append(FOOTER)
    return "".join(lines)


def read_lines(args):
    if args.lines:
        return args.lines
    if args.input:
        text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
        return [l for l in text.splitlines() if "setpos" in l]
    if not sys.stdin.isatty():
        return [l for l in sys.stdin.read().splitlines() if "setpos" in l]
    labels = ["start", "second", "third", "end"]
    lines = []
    for label in labels:
        lines.append(input(f"Paste getpos for the {label} point: "))
    return lines


def parse_fovs(value):
    fovs = [float(v) for v in value.split(",")]
    if len(fovs) == 1:
        return fovs * POINT_COUNT
    if len(fovs) != POINT_COUNT:
        raise argparse.ArgumentTypeError(f"give one FOV or {POINT_COUNT} comma-separated FOVs")
    return fovs


def main():
    parser = argparse.ArgumentParser(
        description="Generate an HLAE campath from four CS2 getpos lines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run with no getpos lines to be prompted for each one.",
    )
    parser.add_argument("lines", nargs="*", help="four getpos lines, in path order")
    parser.add_argument("-i", "--input", help="file with getpos lines, one per row ('-' for stdin)")
    parser.add_argument("-o", "--output", help="campath file to write (default: print to stdout)")
    parser.add_argument("-d", "--duration", type=float, default=DEFAULT_DURATION,
                        help=f"length of the path in seconds (default: {DEFAULT_DURATION:g}, "
                             f"best kept within {SHORT_DURATION:g}-{LONG_DURATION:g})")
    parser.add_argument("-s", "--start", type=float, default=0.0,
                        help="time of the first keyframe in seconds (default: 0)")
    parser.add_argument("--fov", type=parse_fovs, default=parse_fovs("90"),
                        help=f"FOV for every point, or {POINT_COUNT} comma-separated values (default: 90)")
    parser.add_argument("--spacing", choices=["distance", "even"], default="distance",
                        help="'distance' times keyframes for a steady camera speed, "
                             "'even' splits the duration equally (default: distance)")
    parser.add_argument("-f", "--force", action="store_true", help="overwrite an existing output file")
    args = parser.parse_args()

    if args.duration <= 0:
        parser.error("--duration must be greater than 0")

    try:
        points = [parse_getpos(l) for l in read_lines(args)]
    except ValueError as e:
        parser.error(str(e))
    except (EOFError, KeyboardInterrupt):
        sys.exit(1)
    if len(points) != POINT_COUNT:
        parser.error(f"expected {POINT_COUNT} getpos lines, got {len(points)}")

    unwrap_yaw(points)
    times = keyframe_times(points, args.duration, args.start, args.spacing)
    xml = build_campath(points, times, args.fov)
    length = path_length(points)
    speed = length / args.duration
    summary = f"{POINT_COUNT} keyframes, {args.duration:g}s, {length:.0f} units, {speed:.0f} units/s"

    if args.output:
        out = Path(args.output)
        if out.exists() and not args.force:
            parser.error(f"{out} already exists (use --force to overwrite, or add a -v2 suffix)")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(xml)
        print(f"Wrote {out} ({summary})", file=sys.stderr)
    else:
        sys.stdout.write(xml)
        print(f"Campath: {summary}", file=sys.stderr)
    for warning in pacing_warnings(args.duration, speed):
        print(f"Warning: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()
