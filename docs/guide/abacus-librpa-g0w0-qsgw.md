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
- MgO or other dataset-material QSGW runs that continue through one
  head-wing-refresh outer iteration at a time.
- The user-provided `paper_dataset_GW_pseudopotential+NAO.zip` benchmark
  materials through one material-independent ABACUS -> PyATB -> LibRPA route.

For the full dataset-material contract, see:

- `skills/oh-my-librpa/references/paper-dataset-material-workflow.md`

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

MgO QSGW status as of 2026-05-20:

- The production symmetry+shrink+head-wing-refresh route is running from the
  same 8au Mg/O assets.
- `qsgw_band0` iteration 1 gap: `7.793630 eV`.
- `qsgw_band0` iteration 2 gap after refreshed head/wing: `8.208060 eV`.
- Continuation to iteration 20 is still pending validation; do not treat the
  final MgO QSGW gap as established until the run logs and extracted gaps are
  rechecked.

## Non-Negotiable Workflow Points

- Use AroundPeking/upstream `oh-my-LibRPA` logic as primary.
- Keep ABACUS, PyATB, and LibRPA provenance in the run report.
- Use `exx_singularity_correction massidda`; do not use stale
  `exx_use_ewald`.
- Distinguish exact full-BZ paper G0W0 reproduction from the
  symmetry+shrink production QSGW route. They can use the same physical
  PP/NAO/ABFS setup but not the same q-point workload.
- For QSGW head-wing refresh, SCF must generate symmetry sidecars with
  `symmetry 1`; NSCF band-path calculation stays at `symmetry -1`.
- Generate PyATB data on the full regular MP grid in public x-fast order.
- For `qsgw_band0`, explicitly record the Hamiltonian cut:
  `qsgw_band0_unoccupied_keep = 10`, `qsgw_band0_cut_mode = 2`,
  `qsgw_band0_cut_shift_ha = 20.0`, and
  `qsgw_band0_update_hartree = f` unless a Hartree-update test is explicitly
  requested.
- For refreshed QSGW, each next LibRPA call must restart from the previous
  checkpoint and regenerate PyATB/head-wing data from the previous
  `hrs*_nao_qsgw_iter_*.csr` HR export first.
- Infer occupied bands from `band_out` or band occupations for each material.
  Accept both binary and weighted positive occupations; do not hard-code Si's
  occupied-band count in MgO or other materials.
- Submit real calculations through Slurm. Do not run numerical workloads on
  dongfang login nodes.
