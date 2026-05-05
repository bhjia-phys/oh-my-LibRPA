#!/usr/bin/env python3
"""Append smooth Gaussian high-l auxiliary channels to an ABACUS .orb file.

Default behavior:
- if the input has no f channel yet, append one Gaussian f and one Gaussian g
- if the input already has f but no g, append one Gaussian g only

This matches the alpha-MnTe Dojo-NC-SR 10au TZDP route where the NAO already
contains f and the auxiliary tail only needs a nonzero g channel.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


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
class OrbitalChannel:
    l: int
    n: int
    values: List[float]


@dataclass
class OrbitalFile:
    element: str
    energy_cutoff: str
    radius_cutoff: float
    mesh: int
    dr: float
    counts: Dict[int, int]
    channels: List[OrbitalChannel]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Append smooth Gaussian auxiliary channels to an ABACUS .orb file. "
            "If the file already contains f but no g, only a g channel is added."
        )
    )
    parser.add_argument("--input", required=True, help="Input ABACUS .orb file")
    parser.add_argument("--output", required=True, help="Output ABACUS .orb file")
    parser.add_argument(
        "--reference-l",
        type=int,
        default=None,
        help="Reference angular momentum to match. Defaults to the highest existing l in the file.",
    )
    parser.add_argument(
        "--f-scale",
        type=float,
        default=1.10,
        help="Scale factor from reference peak radius to f peak radius. Default: 1.10",
    )
    parser.add_argument(
        "--g-scale",
        type=float,
        default=1.25,
        help=(
            "Scale factor for g. If f is newly generated, g uses g_scale * f_peak. "
            "If f already exists, g uses g_scale * reference_peak."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("single", "extend"),
        default="single",
        help="single: one primitive per channel; extend: add a broader same-sign primitive.",
    )
    parser.add_argument(
        "--extend-ratio",
        type=float,
        default=4.0,
        help="Second primitive alpha ratio in extend mode. alpha2 = alpha1 / ratio. Default: 4.0",
    )
    parser.add_argument(
        "--f-extend-weight",
        type=float,
        default=0.30,
        help="Coefficient of the broad f primitive in extend mode. Default: 0.30",
    )
    parser.add_argument(
        "--g-extend-weight",
        type=float,
        default=0.25,
        help="Coefficient of the broad g primitive in extend mode. Default: 0.25",
    )
    parser.add_argument(
        "--window-start-fraction",
        type=float,
        default=0.85,
        help="Start the smooth cutoff window at this fraction of rcut. Default: 0.85",
    )
    return parser.parse_args()


def extract_field(text: str, pattern: str, name: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"missing required header field: {name}")
    return match.group(1).strip()


def parse_orbital_file(path: Path) -> OrbitalFile:
    text = path.read_text(encoding="utf-8")

    element = extract_field(text, r"^Element\s+(.+)$", "Element")
    energy_cutoff = extract_field(text, r"^Energy Cutoff\(Ry\)\s+(.+)$", "Energy Cutoff(Ry)")
    radius_cutoff = float(extract_field(text, r"^Radius Cutoff\(a\.u\.\)\s+(.+)$", "Radius Cutoff(a.u.)"))
    mesh = int(extract_field(text, r"^Mesh\s+(\d+)$", "Mesh"))
    dr = float(extract_field(text, r"^dr\s+(.+)$", "dr"))

    counts: Dict[int, int] = {}
    for l, label in L_LABELS.items():
        match = re.search(rf"^Number of {label}orbital-->\s+(\d+)$", text, flags=re.MULTILINE)
        if match:
            counts[l] = int(match.group(1))

    lines = text.splitlines()
    channels: List[OrbitalChannel] = []
    idx = 0
    int_triplet = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s*$")
    while idx < len(lines):
        match = int_triplet.match(lines[idx])
        if not match:
            idx += 1
            continue
        _type, l_value, n_value = (int(match.group(i)) for i in range(1, 4))
        idx += 1
        values: List[float] = []
        while idx < len(lines) and len(values) < mesh:
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue
            if int_triplet.match(lines[idx]):
                break
            values.extend(float(token) for token in line.split())
            idx += 1
        if len(values) != mesh:
            raise ValueError(
                f"channel l={l_value} n={n_value} has {len(values)} samples, expected {mesh}"
            )
        channels.append(OrbitalChannel(l=l_value, n=n_value, values=values))

    if not channels:
        raise ValueError("no orbital channels found in input file")

    return OrbitalFile(
        element=element,
        energy_cutoff=energy_cutoff,
        radius_cutoff=radius_cutoff,
        mesh=mesh,
        dr=dr,
        counts=counts,
        channels=channels,
    )


def max_existing_l(orb: OrbitalFile) -> int:
    return max(channel.l for channel in orb.channels)


def smooth_cutoff(radius: float, start_radius: float, cutoff_radius: float) -> float:
    if radius <= start_radius:
        return 1.0
    if radius >= cutoff_radius:
        return 0.0
    t_value = (radius - start_radius) / (cutoff_radius - start_radius)
    return 1.0 - 10.0 * t_value**3 + 15.0 * t_value**4 - 6.0 * t_value**5


def normalize_channel(values: Sequence[float], dr: float) -> List[float]:
    norm = 0.0
    for idx, value in enumerate(values):
        radius = idx * dr
        norm += radius * radius * value * value * dr
    if norm <= 0.0:
        raise ValueError("cannot normalize a zero-valued channel")
    factor = 1.0 / math.sqrt(norm)
    return [value * factor for value in values]


def build_gaussian_channel(
    l_value: int,
    mesh: int,
    dr: float,
    cutoff_radius: float,
    start_fraction: float,
    primitives: Sequence[Dict[str, float]],
) -> List[float]:
    start_radius = start_fraction * cutoff_radius
    values: List[float] = []
    for idx in range(mesh):
        radius = idx * dr
        raw_value = 0.0
        radius_l = radius**l_value if radius > 0.0 or l_value == 0 else 0.0
        for primitive in primitives:
            raw_value += primitive["coefficient"] * radius_l * math.exp(
                -primitive["alpha"] * radius * radius
            )
        raw_value *= smooth_cutoff(radius, start_radius, cutoff_radius)
        values.append(raw_value)
    values[-1] = 0.0
    return normalize_channel(values, dr)


def channel_peak_radius(channel: OrbitalChannel, dr: float) -> float:
    peak_index = max(range(len(channel.values)), key=lambda idx: abs(channel.values[idx]))
    return peak_index * dr


def alpha_from_peak(l_value: int, peak_radius: float) -> float:
    if peak_radius <= 0.0:
        raise ValueError("peak radius must be positive")
    return float(l_value) / (2.0 * peak_radius * peak_radius)


def primitives_for_channel(
    l_value: int,
    peak_radius: float,
    mode: str,
    extend_ratio: float,
    extend_weight: float,
) -> List[Dict[str, float]]:
    base_alpha = alpha_from_peak(l_value, peak_radius)
    primitives = [{"alpha": base_alpha, "coefficient": 1.0}]
    if mode == "extend":
        primitives.append(
            {
                "alpha": base_alpha / extend_ratio,
                "coefficient": extend_weight,
            }
        )
    return primitives


def format_header(orb: OrbitalFile, counts: Dict[int, int], lmax: int) -> str:
    lines = [
        "---------------------------------------------------------------------------",
        f"Element                     {orb.element}",
        f"Energy Cutoff(Ry)           {orb.energy_cutoff}",
        f"Radius Cutoff(a.u.)         {orb.radius_cutoff:g}",
        f"Lmax                        {lmax}",
    ]
    for l_value in range(lmax + 1):
        label = L_LABELS.get(l_value)
        if label is None:
            raise ValueError(f"unsupported angular momentum for header formatting: l={l_value}")
        lines.append(f"Number of {label}orbital-->       {counts.get(l_value, 0)}")
    lines.extend(
        [
            "---------------------------------------------------------------------------",
            "SUMMARY  END",
            "",
            f"Mesh                        {orb.mesh}",
            f"dr                          {orb.dr:g}",
        ]
    )
    return "\n".join(lines) + "\n"


def format_channel(channel: OrbitalChannel) -> str:
    lines = [
        "                Type               L               N",
        f"                   0               {channel.l}               {channel.n}",
    ]
    for start in range(0, len(channel.values), 4):
        chunk = channel.values[start : start + 4]
        lines.append("".join(f"   {value:.14e}" for value in chunk))
    lines.append("")
    return "\n".join(lines) + "\n"


def next_channel_index(channels: Sequence[OrbitalChannel], l_value: int) -> int:
    matching = [channel.n for channel in channels if channel.l == l_value]
    return max(matching) + 1 if matching else 0


def resolve_generation_plan(
    orbital_file: OrbitalFile,
    reference_l: int,
    args: argparse.Namespace,
) -> List[tuple[int, List[float]]]:
    reference_channels = [channel for channel in orbital_file.channels if channel.l == reference_l]
    if not reference_channels:
        raise SystemExit(f"reference l={reference_l} is not present in the input file")
    reference_channel = max(reference_channels, key=lambda channel: channel.n)
    reference_peak = channel_peak_radius(reference_channel, orbital_file.dr)

    existing_lmax = max_existing_l(orbital_file)
    has_f = orbital_file.counts.get(3, 0) > 0
    has_g = orbital_file.counts.get(4, 0) > 0
    if has_g:
        raise SystemExit("input already contains a g channel; refusing to append a duplicate g tail")
    if existing_lmax > 4:
        raise SystemExit("input already contains l > 4 channels; explicit support is required")

    plan: List[tuple[int, List[float]]] = []
    if not has_f:
        f_peak = reference_peak * args.f_scale
        f_primitives = primitives_for_channel(
            l_value=3,
            peak_radius=f_peak,
            mode=args.mode,
            extend_ratio=args.extend_ratio,
            extend_weight=args.f_extend_weight,
        )
        f_values = build_gaussian_channel(
            l_value=3,
            mesh=orbital_file.mesh,
            dr=orbital_file.dr,
            cutoff_radius=orbital_file.radius_cutoff,
            start_fraction=args.window_start_fraction,
            primitives=f_primitives,
        )
        plan.append((3, f_values))
        g_reference_peak = f_peak
    else:
        g_reference_peak = reference_peak

    g_peak = g_reference_peak * args.g_scale
    g_primitives = primitives_for_channel(
        l_value=4,
        peak_radius=g_peak,
        mode=args.mode,
        extend_ratio=args.extend_ratio,
        extend_weight=args.g_extend_weight,
    )
    g_values = build_gaussian_channel(
        l_value=4,
        mesh=orbital_file.mesh,
        dr=orbital_file.dr,
        cutoff_radius=orbital_file.radius_cutoff,
        start_fraction=args.window_start_fraction,
        primitives=g_primitives,
    )
    plan.append((4, g_values))
    return plan


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    orbital_file = parse_orbital_file(input_path)
    existing_lmax = max_existing_l(orbital_file)
    reference_l = args.reference_l if args.reference_l is not None else existing_lmax
    append_plan = resolve_generation_plan(orbital_file, reference_l, args)

    counts = dict(orbital_file.counts)
    output_channels = list(orbital_file.channels)
    appended_ls = []
    for l_value, values in append_plan:
        n_value = next_channel_index(output_channels, l_value)
        counts[l_value] = counts.get(l_value, 0) + 1
        output_channels.append(OrbitalChannel(l=l_value, n=n_value, values=values))
        appended_ls.append(l_value)

    output_channels.sort(key=lambda channel: (channel.l, channel.n))
    new_lmax = max(max_existing_l(orbital_file), max(appended_ls))

    output_text = format_header(orbital_file, counts, new_lmax)
    for channel in output_channels:
        output_text += format_channel(channel)
    output_path.write_text(output_text, encoding="utf-8")

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "mode": args.mode,
        "reference_l": reference_l,
        "appended_l": appended_ls,
        "counts": counts,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
