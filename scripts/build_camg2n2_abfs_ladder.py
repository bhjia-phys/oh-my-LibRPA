#!/usr/bin/env python3
"""Build synchronized CaMg2N2 ABFS ladder stages between nofg and the large endpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from trim_abfs_channels import L_LABELS, RadialBasisFile, RadialChannel, format_channel, format_header, parse_radial_basis


ELEMENTS = ("Ca", "Mg", "N")
STOICHIOMETRY = {"Ca": 1, "Mg": 2, "N": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate synchronized intermediate Ca/Mg/N .abfs ladders for the "
            "CaMg2N2 no-shrink convergence path."
        )
    )
    parser.add_argument("--base-dir", help="Directory containing the trusted nofg .abfs files")
    parser.add_argument("--full-dir", help="Directory containing the large endpoint .abfs files")
    parser.add_argument("--output-root", help="Root directory for generated stage folders")
    parser.add_argument(
        "--stage",
        action="append",
        choices=("G1", "G2", "G3", "G4"),
        help="Only build the selected stage(s). Default: all stages.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the stage count tables and estimated cell sizes without writing files.",
    )
    return parser.parse_args()


def find_abfs_file(directory: Path, element: str) -> Path:
    matches = sorted(directory.glob(f"{element}_*.abfs"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {element} .abfs in {directory}, found {len(matches)}")
    return matches[0]


def positive_counts(base_counts: Dict[int, int], full_counts: Dict[int, int], max_l: int) -> Dict[int, int]:
    counts: Dict[int, int] = {}
    for l_value in range(max_l + 1):
        counts[l_value] = max(base_counts.get(l_value, 0), full_counts.get(l_value, 0))
    return counts


def stage_counts(base_counts: Dict[int, int], full_counts: Dict[int, int]) -> Dict[str, Dict[int, int]]:
    g1 = dict(base_counts)
    for l_value in range(5):
        if full_counts.get(l_value, 0) > base_counts.get(l_value, 0):
            g1[l_value] = base_counts.get(l_value, 0) + 1
    for l_value in range(5, 9):
        g1[l_value] = 0

    g2 = positive_counts(base_counts, full_counts, 4)
    for l_value in range(5, 9):
        g2[l_value] = 0

    g3 = dict(g2)
    for l_value in (5, 6):
        g3[l_value] = full_counts.get(l_value, 0)
    g3[7] = 0
    g3[8] = 0

    g4 = dict(g3)
    g4[7] = full_counts.get(7, 0)
    g4[8] = 0

    return {"G1": g1, "G2": g2, "G3": g3, "G4": g4}


def weighted_count(counts: Dict[int, int]) -> int:
    return sum(count * (2 * l_value + 1) for l_value, count in counts.items() if count > 0)


def estimate_cell_size(stage_map: Dict[str, Dict[int, Dict[int, int]]], stage_name: str) -> int:
    total = 0
    for element in ELEMENTS:
        total += STOICHIOMETRY[element] * weighted_count(stage_map[stage_name][element])
    return total


def discover_counts(directory: Path) -> Tuple[Dict[str, Path], Dict[str, Dict[int, int]]]:
    paths: Dict[str, Path] = {}
    counts: Dict[str, Dict[int, int]] = {}
    for element in ELEMENTS:
        path = find_abfs_file(directory, element)
        paths[element] = path
        counts[element] = parse_radial_basis(path).counts
    return paths, counts


def build_stage_tables(base_counts: Dict[str, Dict[int, int]], full_counts: Dict[str, Dict[int, int]]) -> Dict[str, Dict[str, Dict[int, int]]]:
    tables: Dict[str, Dict[str, Dict[int, int]]] = {}
    for element in ELEMENTS:
        per_stage = stage_counts(base_counts[element], full_counts[element])
        for stage_name, counts in per_stage.items():
            tables.setdefault(stage_name, {})[element] = counts
    return tables


def merge_basis_channels(
    base_basis: RadialBasisFile,
    full_basis: RadialBasisFile,
    desired_counts: Dict[int, int],
) -> RadialBasisFile:
    base_by_l: Dict[int, List[RadialChannel]] = {}
    full_by_l: Dict[int, List[RadialChannel]] = {}
    for channel in sorted(base_basis.channels, key=lambda item: (item.l, item.n)):
        base_by_l.setdefault(channel.l, []).append(channel)
    for channel in sorted(full_basis.channels, key=lambda item: (item.l, item.n)):
        full_by_l.setdefault(channel.l, []).append(channel)

    output_channels: List[RadialChannel] = []
    output_counts: Dict[int, int] = {}
    for l_value in sorted(desired_counts):
        keep = desired_counts[l_value]
        if keep <= 0:
            continue
        base_channels = base_by_l.get(l_value, [])
        full_channels = full_by_l.get(l_value, [])

        if len(full_channels) >= keep and len(full_channels) >= len(base_channels):
            source = full_channels
        elif len(base_channels) >= keep:
            source = base_channels
        elif len(full_channels) >= keep:
            source = full_channels
        else:
            raise ValueError(
                f"cannot satisfy l={l_value} count {keep}: base has {len(base_channels)}, "
                f"full has {len(full_channels)}"
            )
        output_channels.extend(source[:keep])
        output_counts[l_value] = keep

    if not output_channels:
        raise ValueError("cannot build an empty stage basis")

    return RadialBasisFile(
        element=full_basis.element,
        energy_cutoff=full_basis.energy_cutoff,
        radius_cutoff=full_basis.radius_cutoff,
        mesh=full_basis.mesh,
        dr=full_basis.dr,
        counts=output_counts,
        channels=sorted(output_channels, key=lambda item: (item.l, item.n)),
    )


def write_stage_files(
    base_paths: Dict[str, Path],
    full_paths: Dict[str, Path],
    stage_map: Dict[str, Dict[str, Dict[int, int]]],
    output_root: Path,
    selected_stages: List[str],
) -> List[Dict[str, object]]:
    manifest: List[Dict[str, object]] = []
    for stage_name in selected_stages:
        stage_dir = output_root / stage_name
        stage_dir.mkdir(parents=True, exist_ok=True)
        stage_record = {
            "stage": stage_name,
            "estimated_cell_size": estimate_cell_size(stage_map, stage_name),
            "files": [],
        }
        for element in ELEMENTS:
            base_path = base_paths[element]
            source_path = full_paths[element]
            base_basis = parse_radial_basis(base_path)
            full_basis = parse_radial_basis(source_path)
            trimmed = merge_basis_channels(base_basis, full_basis, stage_map[stage_name][element])
            stage_weight = weighted_count(trimmed.counts)
            output_name = f"{source_path.stem}_{stage_name}_{stage_weight}.abfs"
            output_path = stage_dir / output_name

            output_text = format_header(trimmed)
            for channel in trimmed.channels:
                output_text += format_channel(channel)
            output_path.write_text(output_text, encoding="utf-8")

            stage_record["files"].append(
                {
                    "element": element,
                    "base_source": str(base_path),
                    "source": str(source_path),
                    "output": str(output_path),
                    "weighted_count": stage_weight,
                    "counts": trimmed.counts,
                }
            )
        manifest.append(stage_record)
    return manifest


def main() -> int:
    args = parse_args()
    selected_stages = args.stage or ["G1", "G2", "G3", "G4"]

    if args.base_dir:
        base_dir = Path(args.base_dir).expanduser().resolve()
        base_paths, base_counts = discover_counts(base_dir)
    else:
        raise SystemExit("--base-dir is required")

    if args.full_dir:
        full_dir = Path(args.full_dir).expanduser().resolve()
        full_paths, full_counts = discover_counts(full_dir)
    else:
        raise SystemExit("--full-dir is required")

    stage_map = build_stage_tables(base_counts, full_counts)
    summary = {
        "stages": {
            stage_name: {
                "estimated_cell_size": estimate_cell_size(stage_map, stage_name),
                "elements": stage_map[stage_name],
            }
            for stage_name in selected_stages
        }
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if not args.output_root:
        raise SystemExit("--output-root is required unless --dry-run is used")

    output_root = Path(args.output_root).expanduser().resolve()
    manifest = write_stage_files(base_paths, full_paths, stage_map, output_root, selected_stages)
    print(json.dumps({"summary": summary, "manifest": manifest}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
