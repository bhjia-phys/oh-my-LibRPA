#!/usr/bin/env python3
"""Trim ABACUS .abfs radial-basis files to explicit per-l channel counts."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


L_LABELS = {
    0: "S",
    1: "P",
    2: "D",
    3: "F",
    4: "G",
    5: "H",
    6: "I",
    7: "J",
    8: "K",
}


@dataclass
class RadialChannel:
    l: int
    n: int
    values: List[float]


@dataclass
class RadialBasisFile:
    element: str
    energy_cutoff: str
    radius_cutoff: str
    mesh: int
    dr: str
    counts: Dict[int, int]
    channels: List[RadialChannel]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Trim an ABACUS .abfs radial-basis file to explicit per-angular-momentum "
            "channel counts while rewriting the header consistently."
        )
    )
    parser.add_argument("--input", required=True, help="Input .abfs file")
    parser.add_argument("--output", required=True, help="Output .abfs file")
    parser.add_argument(
        "--count",
        action="append",
        default=[],
        metavar="L=N",
        help="Retain the first N channels for angular momentum L. Repeat as needed.",
    )
    return parser.parse_args()


def extract_field(text: str, pattern: str, name: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"missing required header field: {name}")
    return match.group(1).strip()


def parse_counts_args(items: Iterable[str]) -> Dict[int, int]:
    counts: Dict[int, int] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"invalid --count value: {item!r}")
        left, right = item.split("=", 1)
        l_value = int(left)
        count = int(right)
        if l_value < 0:
            raise ValueError(f"angular momentum must be non-negative: {item!r}")
        if count < 0:
            raise ValueError(f"channel count must be non-negative: {item!r}")
        if l_value not in L_LABELS:
            raise ValueError(f"unsupported angular momentum l={l_value}")
        counts[l_value] = count
    return counts


def parse_radial_basis(path: Path) -> RadialBasisFile:
    text = path.read_text(encoding="utf-8")

    element = extract_field(text, r"^Element\s+(.+)$", "Element")
    energy_cutoff = extract_field(text, r"^Energy Cutoff\(Ry\)\s+(.+)$", "Energy Cutoff(Ry)")
    radius_cutoff = extract_field(text, r"^Radius Cutoff\(a\.u\.\)\s+(.+)$", "Radius Cutoff(a.u.)")
    mesh = int(extract_field(text, r"^Mesh\s+(\d+)$", "Mesh"))
    dr = extract_field(text, r"^dr\s+(.+)$", "dr")

    counts: Dict[int, int] = {}
    for l_value, label in L_LABELS.items():
        match = re.search(rf"^Number of {label}orbital-->\s+(\d+)$", text, flags=re.MULTILINE)
        if match:
            counts[l_value] = int(match.group(1))

    channels: List[RadialChannel] = []
    lines = text.splitlines()
    idx = 0
    int_triplet = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s*$")
    while idx < len(lines):
        match = int_triplet.match(lines[idx])
        if not match:
            idx += 1
            continue
        _kind, l_value, n_value = (int(match.group(i)) for i in range(1, 4))
        idx += 1
        values: List[float] = []
        while idx < len(lines) and len(values) < mesh:
            raw_line = lines[idx].strip()
            if not raw_line:
                idx += 1
                continue
            next_match = int_triplet.match(lines[idx])
            if next_match:
                break
            values.extend(float(token) for token in raw_line.split())
            idx += 1
        if len(values) != mesh:
            raise ValueError(
                f"channel l={l_value} n={n_value} has {len(values)} samples, expected {mesh}"
            )
        channels.append(RadialChannel(l=l_value, n=n_value, values=values))

    if not channels:
        raise ValueError("no radial channels found in input file")

    return RadialBasisFile(
        element=element,
        energy_cutoff=energy_cutoff,
        radius_cutoff=radius_cutoff,
        mesh=mesh,
        dr=dr,
        counts=counts,
        channels=channels,
    )


def trimmed_counts(basis: RadialBasisFile, requested: Dict[int, int]) -> Dict[int, int]:
    actual: Dict[int, int] = {}
    for channel in basis.channels:
        actual[channel.l] = actual.get(channel.l, 0) + 1
    result = dict(actual)
    result.update(requested)
    for l_value, count in result.items():
        if count > actual.get(l_value, 0):
            raise ValueError(
                f"requested l={l_value} count {count} exceeds available {actual.get(l_value, 0)}"
            )
    return result


def trim_channels(basis: RadialBasisFile, requested: Dict[int, int]) -> RadialBasisFile:
    counts = trimmed_counts(basis, requested)
    by_l: Dict[int, List[RadialChannel]] = {}
    for channel in sorted(basis.channels, key=lambda item: (item.l, item.n)):
        by_l.setdefault(channel.l, []).append(channel)

    output_channels: List[RadialChannel] = []
    for l_value in sorted(by_l):
        keep = counts.get(l_value, len(by_l[l_value]))
        output_channels.extend(by_l[l_value][:keep])

    retained_counts: Dict[int, int] = {}
    for channel in output_channels:
        retained_counts[channel.l] = retained_counts.get(channel.l, 0) + 1
    if not output_channels:
        raise ValueError("cannot trim away every channel")

    return RadialBasisFile(
        element=basis.element,
        energy_cutoff=basis.energy_cutoff,
        radius_cutoff=basis.radius_cutoff,
        mesh=basis.mesh,
        dr=basis.dr,
        counts=retained_counts,
        channels=output_channels,
    )


def format_header(basis: RadialBasisFile) -> str:
    lmax = max(basis.counts)
    lines = [
        "---------------------------------------------------------------------------",
        f"Element                     {basis.element}",
        f"Energy Cutoff(Ry)           {basis.energy_cutoff}",
        f"Radius Cutoff(a.u.)         {basis.radius_cutoff}",
        f"Lmax                        {lmax}",
    ]
    for l_value in range(lmax + 1):
        label = L_LABELS[l_value]
        lines.append(f"Number of {label}orbital-->       {basis.counts.get(l_value, 0)}")
    lines.extend(
        [
            "---------------------------------------------------------------------------",
            "SUMMARY  END",
            "",
            f"Mesh                        {basis.mesh}",
            f"dr                          {basis.dr}",
        ]
    )
    return "\n".join(lines) + "\n"


def format_channel(channel: RadialChannel) -> str:
    lines = [
        "                Type               L               N",
        f"                   0               {channel.l}               {channel.n}",
    ]
    for start in range(0, len(channel.values), 4):
        chunk = channel.values[start : start + 4]
        lines.append("".join(f"   {value:.14e}" for value in chunk))
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    requested = parse_counts_args(args.count)
    basis = parse_radial_basis(input_path)
    trimmed = trim_channels(basis, requested)

    output_text = format_header(trimmed)
    for channel in trimmed.channels:
        output_text += format_channel(channel)
    output_path.write_text(output_text, encoding="utf-8")

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "requested_counts": requested,
        "written_counts": trimmed.counts,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
