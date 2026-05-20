# ABACUS G0W0/QSGW Golden Runbook

This runbook is the operational path for a new agent or user who needs to run
periodic ABACUS -> PyATB -> LibRPA `g0w0_band` or `qsgw_band0` without relying
on chat history.

Use it together with:

- `skills/oh-my-librpa/references/abacus-g0w0-qsgw-workflow.md`
- `skills/oh-my-librpa/references/paper-dataset-material-workflow.md` when
  using the paper dataset archive
- `docs/guide/abacus-librpa-g0w0-qsgw.md` for current validated benchmark
  values

## 0. Choose the Route

Do this before editing any input.

| Route | Use when | Main consequence |
| --- | --- | --- |
| `paper_strict_full_bz_g0w0` | Reproducing a published dataset G0W0 result exactly | Keep the archived physical setup and symmetry choice. A full 8x8x8 route may process 512 q-points. |
| `production_symmetry_qsgw` | Running QSGW, head-wing refresh, shrink, or continued iterations | Use SCF `symmetry 1`, NSCF `symmetry -1`, ABACUS symmetry sidecars, and full-MP-grid PyATB head/wing data. |

Never mix these two routes silently. A report must say which route is used.

## 1. Record Provenance

Record these before submission:

- ABACUS executable path, branch, and commit
- PyATB source path and API convention
- LibRPA executable path, branch, and commit
- OML branch and commit
- host, partition, nodes, MPI ranks, OpenMP threads, and memory
- PP, NAO, ABFS, `nbands`, `ecutwfc`, k-mesh, band path, and shrink settings

For the current validated dongfang reference, use the provenance in
`abacus-g0w0-qsgw-workflow.md`.

## 2. Prepare a Fresh Case

Create a new run directory. Copy source inputs only:

- `STRU`
- `INPUT_scf`, `INPUT_nscf`
- `KPT_scf`, `KPT_nscf`
- `band_kpath_info`
- `librpa.in` or `librpa.qsgw_band0.in`
- referenced `*.upf`, `*.orb`, and `*.abfs`
- matched helpers: `perform.sh`, `get_diel.py`, `output_librpa.py`,
  `preprocess_abacus_for_librpa_band.py`, plotting helpers, and batch scripts

Do not copy generated outputs into a new source case:

- `OUT.ABACUS`
- `band_out`
- `GW_band_spin_*`, `QSGW_band_spin_*`, `EXX_band_spin_*`
- `coulomb_*`, `Cs_*`, `shrink_sinvS_*`
- `librpa.d`, `LibRPA*.out`, `librpa_para_nprocs_*`

## 3. Normalize Inputs

Patch only interface compatibility unless running an explicit convergence
study.

- Replace stale ABACUS keys:
  - remove `exx_use_ewald`; use `exx_singularity_correction massidda`
  - replace `cs_inv_thr` with `exx_cs_inv_thr`
  - remove `exx_spencer_type`
  - remove `out_bandgap`
- Keep PP/NAO/ABFS, k-mesh, `nbands`, band path, and thresholds from the
  chosen physical source.
- Verify `nbands` from the NAO basis count and keep it identical in SCF and
  NSCF.
- If shrink is used, `STRU` must contain `ABFS_ORBITAL` and `librpa.in` must
  keep `use_shrink_abfs = t`.

## 4. Run G0W0

For `production_symmetry_qsgw` and symmetry-enabled G0W0:

- `INPUT_scf`: `calculation scf`, `symmetry 1`, `rpa 1`, `out_chg 1`,
  `out_mat_xc 1`, `out_mat_hs2 1`, `out_mat_r 1`
- `INPUT_nscf`: `calculation nscf`, `symmetry -1`, `init_chg file`,
  `out_mat_xc 1`, `out_mat_hs 1`, `out_mat_hs2 1`, `out_wfc_lcao 1`
- PyATB must generate `pyatb_librpa_df/` on the full regular MP grid in public
  x-fast order.
- LibRPA uses `task = g0w0_band`, `replace_w_head = t`,
  `option_dielect_func = 3`, `use_pyatb = t`, `use_shrink_abfs = t`, and
  ABACUS symmetry flags when sidecars are present.

Stage success markers:

| Stage | Required markers |
| --- | --- |
| SCF | `OUT.ABACUS/running_scf.log`, charge restart, `vxc_out.dat`, and symmetry sidecars for the symmetry route |
| PyATB | `pyatb_librpa_df/band_out` and `pyatb_librpa_df/KS_eigenvector_*.dat` |
| NSCF | `OUT.ABACUS/running_nscf.log` and `eig.txt` or `eig_occ.txt` |
| Preprocess | `band_kpath_info`, `band_KS_*`, and `band_vxc*` |
| LibRPA G0W0 | successful rank-0 log and `GW_band_spin_*` |

Extract gaps from the current material's occupations. Do not hard-code Si's
four occupied bands.

## 5. Run QSGW Iteration 1

Start from a validated G0W0 source bundle on the production symmetry route.

Use a QSGW input with:

```text
task = qsgw_band0
max_iter = 1
qsgw_checkpoint_every = 1
qsgw_export_hamiltonian_for_pyatb = t
qsgw_hr_export_full_mp_rgrid = t
qsgw_band0_unoccupied_keep = 10
qsgw_band0_cut_mode = 2
qsgw_band0_cut_shift_ha = 20.0
qsgw_band0_update_hartree = f
```

After iteration 1, verify:

- `librpa.d/qsgw_checkpoints/iter_00001/H0_GW_spin_...bin`
- `hrs*_nao_qsgw_iter_0001.csr`
- `QSGW_band_spin_*`
- a finite `Hamiltonian_gap` in the rank-0 log

## 6. Continue QSGW With Head-Wing Refresh

For refreshed head-wing QSGW, do not run many iterations in one LibRPA call
unless the head/wing is intentionally frozen.

Use this loop:

```text
completed iteration i
  -> verify checkpoint iter_i
  -> verify hrs*_nao_qsgw_iter_i.csr
  -> regenerate PyATB/head-wing data from the HR export
  -> write librpa.in with qsgw_restart_iteration = i and max_iter = i + 1
  -> submit the next LibRPA call
```

The template script is:

- `templates/abacus-librpa-gw/template/run_qsgw_headwing_refresh_loop.sh`

It is intentionally conservative: it refuses to run outside a batch allocation
unless explicitly allowed, requires a user-provided PyATB/head-wing refresh
command, archives each iteration, and stops on a LibRPA convergence marker or a
chosen maximum iteration.

## 7. Stop Criteria

Stop when either condition is reached:

- the LibRPA log reports `Converged after N iterations`
- the campaign cap is reached, currently 20 iterations for open MgO-style
  convergence tests unless the user requests otherwise

For every completed iteration, record:

- k-mesh
- route label
- cut mode and unoccupied keep count
- Hartree update flag
- head-wing treatment: refreshed, frozen, or head-only frozen
- `Hamiltonian_gap` and plotted band-path gap
- wall time and resources

## 8. Minimum Final Report

A final report must include:

- route label and provenance
- physical settings: PP/NAO/ABFS, `nbands`, k-mesh, band path, thresholds
- G0W0 baseline gap and plot
- QSGW iteration table
- whether head/wing and Hartree were refreshed
- convergence status and residual risk
- paths to logs, figures, and notebook/report artifacts
