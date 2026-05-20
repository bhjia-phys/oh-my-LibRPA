# Paper Dataset Material Workflow

Load this reference when the user provides or mentions
`paper_dataset_GW_pseudopotential+NAO.zip`, asks to reproduce the paper
benchmark materials, or asks for one workflow that works across the bundled
ABACUS + LibRPA materials.

This is an ABACUS-owned periodic-solid route. Use the strict
`abacus-g0w0-qsgw-workflow.md` stage order and the current ABACUS/PyATB/LibRPA
provenance recorded there.

## Dataset Scope

The benchmark table in the user-provided dataset contains these primary
material entries:

| System | ABACUS+LibRPA G0W0 gap (eV) | Dataset source_dir | Rerun source status |
| --- | ---: | --- | --- |
| AlAs | 2.008 | `benchmark_gap_cases/AlAs__src_paper` | complete |
| AlP | 2.374 | `benchmark_gap_cases/AlP__src_k8_shrink_wing` | complete |
| AlSb | 1.576 | `benchmark_gap_cases/AlSb__src_gw_gth_modspencer` | complete |
| BAs | 1.762 | `benchmark_gap_cases/BAs__src_k8_shrink_wing` | complete |
| BN | 6.324 | `benchmark_gap_cases/BN__src_sg15` | complete |
| BP | 2.030 | `benchmark_gap_cases/BP__src_k8_shrink_wing` | complete |
| C | 5.549 | `benchmark_gap_cases/C__src_sg15_cs1e-5` | complete |
| Si | 1.060 | `benchmark_gap_cases/Si__src_all_kpath` | complete |
| SiC | 2.255 | `benchmark_gap_cases/SiC__src_pca1e-6` | result-only in this zip |
| GaAs | 1.378 | `benchmark_gap_cases/GaAs__src_gw_xsoc_1e-10` | complete |
| GaN | 2.857 | `benchmark_gap_cases/GaN__src_pca1e-6` | complete |
| GaP | 2.245 | `benchmark_gap_cases/GaP__src_gw_shrink_chi` | result-only; use `shared_input_GaP_gw` |
| MgO | 7.392 | `benchmark_gap_cases/MgO__src_fix_gap` | complete |
| NaCl | 7.832 | `benchmark_gap_cases/NaCl__src_sg15` | complete |
| CdS | 2.076 | `benchmark_gap_cases/CdS__src_debug` | complete |
| CaO | 6.368 | `benchmark_gap_cases/CaO__src_24freq` | result-only; use `shared_input_CaO_1mpi` |
| LiF | 14.000 | `benchmark_gap_cases/LiF__src_jy` | complete |

The zip also contains focused studies:

- `Si_convergence_and_C_kpoint/`: Si basis/k/rcut convergence and C k-point
  head/head-wing comparisons.
- `BN_threshold_convergence/`: BN threshold sweeps for chi and Sigc.
- `GaAs_pseudopotential_and_soc/`: GaAs PP, SOC, XSOC, and head-response cases.
- `MgO_compression/`: MgO shrink/compression and pseudo-inverse threshold
  cases. The current primary MgO strict reproduction uses
  `pseudo_inverse_threshold_cases/threshold_1e-3__src_1e-3`, not the older
  benchmark-table MgO setup.

## Source-Bundle Lift Rule

For a complete dataset case, copy only these source items into a fresh run
directory:

- `STRU`
- `INPUT`, `INPUT_scf`, `INPUT_nscf`
- `KPT`, `KPT_scf`, `KPT_nscf`
- `band_kpath_info`
- `librpa.in`
- all referenced `*.upf`, `*.orb`, and `*.abfs`
- workflow helper scripts only if they are intentionally reused

Do not copy generated outputs into a rerun source directory:

- `OUT.ABACUS`
- `band_out`
- `GW_band_spin_*`, `KS_band_spin_*`, `EXX_band_spin_*`,
  `QSGW_band_spin_*`
- `librpa.d`, `LibRPA*.out`, `librpa_para_nprocs_*`
- `coulomb_*`, `Cs_*`, `Cs_data*`, `Cs_shrinked_data_*`,
  `shrink_sinvS_*`, `time.json`

If the dataset entry is result-only, do not claim it is rerunnable from that
directory alone. Either use the matching `shared_input_*` directory listed
above, reconstruct a complete case from the asset library and the paper
structure, or ask the user for the missing ABACUS source bundle.

## Current-Interface Normalization

Many archived dataset inputs used older ABACUS keywords. Before any new
submission, normalize them to the current successful Si/MgO interface:

| Archived key or pattern | Current action |
| --- | --- |
| `exx_use_ewald 1` | remove it and set `exx_singularity_correction massidda` |
| `cs_inv_thr <x>` | replace with `exx_cs_inv_thr <x>` |
| `exx_spencer_type` | remove; use the current singularity-correction key |
| missing `out_mat_hs` in NSCF | add `out_mat_hs 1` for periodic GW/QSGW |
| missing `out_mat_hs2` in NSCF | add `out_mat_hs2 1` |
| missing `out_mat_xc` in SCF/NSCF | add `out_mat_xc 1` |

Always run `scripts/intake_preflight.sh` and `scripts/check_consistency.sh`
after this normalization. These checks intentionally fail on stale keys.

## Material-Independent G0W0 Route

For each complete non-SOC periodic benchmark material:

1. Use the dataset `STRU`, `KPT_scf`, `KPT_nscf`, PP, NAO, ABFS, `nbands`,
   `ecutwfc`, and material-specific shrink thresholds as the physical source
   of truth.
2. Normalize only API/interface keywords needed by the current ABACUS branch.
   Do not change the basis, pseudopotential family, k-mesh, band path,
   `nbands`, or convergence thresholds unless running an explicit convergence
   study.
3. Run the strict periodic route:
   `ABACUS SCF -> PyATB full MP grid -> ABACUS NSCF band path -> preprocess -> LibRPA g0w0_band`.
4. Keep `replace_w_head = t`, `option_dielect_func = 3`, `use_pyatb = t`,
   and `use_shrink_abfs = t` when the source bundle was a shrink+head-wing
   case.
5. Plot with `plot_gw_band_paper.py` or a helper that reads occupations from
   `band_out`; never hard-code the number of occupied bands from Si.

For SOC cases such as GaAs SOC/XSOC:

- keep the SOC case on its original no-symmetry lane unless a validated SOC
  symmetry route exists;
- set the ABACUS spin/SOC keys, `get_diel.py`, preprocess, and `librpa.in`
  consistently;
- use SOC pseudopotentials only.

When the goal is exact paper-table reproduction, keep the archived
full-BZ/no-symmetry route if that is what the source bundle used. When the
goal is a continued QSGW calculation with refreshed head/wing, switch to the
validated production symmetry route below and label the route change in the
run report.

## QSGW Upgrade Rule

Use the validated G0W0 case as the source for QSGW, but do not reuse a
no-symmetry G0W0 SCF when head-wing refresh is requested.

For `qsgw_band0` with head-wing refresh:

1. Rerun SCF with `symmetry 1` so ABACUS writes the symmetry sidecars.
2. Keep NSCF band path on `symmetry -1`.
3. Regenerate PyATB on the full regular MP grid using public x-fast ordering.
4. Use:

```text
task = qsgw_band0
max_iter = <target iteration for this LibRPA call>
qsgw_checkpoint_every = 1
qsgw_export_hamiltonian_for_pyatb = t
qsgw_hr_export_full_mp_rgrid = t
qsgw_band0_unoccupied_keep = 10
qsgw_band0_cut_mode = 2
qsgw_band0_cut_shift_ha = 20.0
qsgw_band0_update_hartree = f
```

5. Between refresh iterations, rebuild the PyATB/head-wing input from the
   exported `hrs*_nao_qsgw_iter_*.csr` Hamiltonian.

For a refreshed head-wing campaign, use one LibRPA outer step per refresh:

1. Finish iteration `i`.
2. Keep the checkpoint directory `librpa.d/qsgw_checkpoints/iter_<i>/` for
   restart.
3. Use `hrs*_nao_qsgw_iter_<i>.csr` to regenerate full-MP-grid PyATB/head-wing
   inputs.
4. Restart LibRPA with `qsgw_restart_iteration = i` and
   `max_iter = i + 1`.
5. Stop at `Converged after N iterations` or at the chosen campaign cap. Use
   20 iterations as the current default cap for open MgO-style tests.

Checkpoint binaries and HR exports are not interchangeable. The checkpoint is
the restart state; the HR export is the bridge back to PyATB.

The Hamiltonian cut is material independent in form but material dependent in
`N0`: LibRPA counts occupied bands from the Fermi level. All occupied bands are
kept, then the first `qsgw_band0_unoccupied_keep` unoccupied bands are kept.
Do not assume Si's `N0 = 4` for MgO, BN, GaAs, or any other material.

Cut modes:

- `qsgw_band0_cut_mode = 0`: no active-window cut.
- `qsgw_band0_cut_mode = 1`: outside the occupied plus kept-unoccupied
  window, zero off-diagonal H0_GW and reset the diagonal to KS.
- `qsgw_band0_cut_mode = 2`: same off-diagonal cut, but reset the outside
  diagonal to KS plus `qsgw_band0_cut_shift_ha`.

Hartree updates are available in the current LibRPA branch but are disabled in
the validated Si/MgO ABACUS route by `qsgw_band0_update_hartree = f`. Enable
them only in a separately labeled Hartree-update study.

## Occupation and Gap Extraction Rule

Post-processing must infer occupations from the current run:

- Prefer `band_out` occupations for band-path plots and gap extraction.
  Some ABACUS/PyATB `band_out` files store occupied states as small positive
  weighted values rather than `2.0`; infer the occupied manifold from the
  leading nonzero block, not from `occ > 0.5` alone.
- If using `GW_band_spin_*` or `QSGW_band_spin_*`, use the occupation columns
  in that file or align them to `band_out`.
- Do not hard-code `nocc = 4`. MgO has 8 occupied bands in the current
  `qsgw_band0` band-path output.
- If the gap extractor reports a gap that disagrees with
  `Hamiltonian_gap:` in the LibRPA log by many eV, treat the extractor as
  wrong until the occupied manifold has been checked.

## Material Notes

- Si: use `Si/sg15` as the public-style reference setup.
- MgO strict paper reproduction: use `Mg/sg15_8au` and `O/sg15_8au` from the
  user dataset; this reproduced the `7.1921781 eV` paper-dataset G0W0 gap.
- MgO QSGW production route: use the same 8au Mg/O assets, SCF
  `symmetry 1`, NSCF `symmetry -1`, shrink, and refreshed head+wing. The
  current validated partial data are iteration 1 `7.793630 eV` and iteration 2
  `8.208060 eV`; the continuation to iteration 20 is still a running/pending
  convergence campaign until logs and gaps are rechecked.
- MgO benchmark-table reproduction: `MgO__src_fix_gap` is a different older
  10au/2f2g setup with table gap `7.392 eV`; do not mix it with the strict
  MgO 8au test.
- CaO and GaP: benchmark result directories are output-oriented; pair them
  with `shared_input_CaO_1mpi` or `shared_input_GaP_gw` before rerunning.
- SiC: the listed benchmark directory in this zip is result-only. Treat the
  ABACUS outputs as reference data, not as a complete rerun source bundle.
- BN threshold studies: keep the threshold being swept as the only intentional
  variable.
- GaAs PP/SOC studies: do not collapse standard, SOC, XSOC, and
  head-response directories into one route; they answer different questions.

## Minimum Acceptance Checklist

Before saying a material is ready to run:

- The case has a complete source bundle or an explicitly documented
  reconstruction path.
- `STRU` references existing PP/NAO/ABFS files.
- `nbands` matches the ABACUS basis count and is the same in SCF/NSCF.
- Current ABACUS keywords have replaced archived stale keys.
- Shrink settings match the presence of ABFS/shrink artifacts.
- For QSGW refresh, SCF sidecars and full-MP-grid PyATB generation are ready.
- For QSGW refresh, the previous iteration's HR export, not only the
  checkpoint binaries, is available before launching the next iteration.
- The route label distinguishes exact full-BZ paper G0W0 reproduction from the
  symmetry+shrink QSGW production route.
- The gap/plot script infers occupied bands from the run rather than from a
  material-specific constant.
