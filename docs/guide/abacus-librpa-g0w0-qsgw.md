# ABACUS + PyATB + LibRPA G0W0/QSGW Guide

This guide points humans to the strict agent workflow for periodic ABACUS-owned
solid calculations.

The executable workflow contract lives in:

- `skills/oh-my-librpa/references/abacus-g0w0-qsgw-workflow.md`

Use that reference when reproducing:

- Si public-style `G0W0 -> qsgw_band0` with shrink, symmetry, and head-wing
  correction.
- Si QSGW branch comparisons: refreshed head+wing, frozen head+wing, and
  head-only frozen.
- MgO paper-strict G0W0 using the user-provided 8au Mg/O PP/NAO/ABFS bundle.

## Current Validated Benchmarks

Si, 8x8x8, paper-path extraction:

- KS gap: `0.56060 eV`
- G0W0 gap: `1.09289 eV`
- QSGW `qsgw_band0` iteration 1 gap: `1.23721 eV`
- QSGW refreshed head+wing iteration 10 gap: `1.139710 eV`

MgO, 8x8x8, paper-strict G0W0:

- DFT gap: `4.7199201 eV`
- G0W0 gap: `7.1921789 eV`
- paper-dataset reference: `7.1921781 eV`
- delta: `8.0e-7 eV`

MgO QSGW is still a pending validation target as of 2026-05-20.

## Non-Negotiable Workflow Points

- Use AroundPeking/upstream `oh-my-LibRPA` logic as primary.
- Keep ABACUS, PyATB, and LibRPA provenance in the run report.
- Use `exx_singularity_correction massidda`; do not use stale
  `exx_use_ewald`.
- For QSGW head-wing refresh, SCF must generate symmetry sidecars with
  `symmetry 1`; NSCF band-path calculation stays at `symmetry -1`.
- Generate PyATB data on the full regular MP grid in public x-fast order.
- For `qsgw_band0`, explicitly record the Hamiltonian cut:
  `qsgw_band0_unoccupied_keep = 10`, `qsgw_band0_cut_mode = 2`,
  `qsgw_band0_cut_shift_ha = 20.0`.
- Submit real calculations through Slurm. Do not run numerical workloads on
  dongfang login nodes.

