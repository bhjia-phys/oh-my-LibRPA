# ABACUS G0W0/QSGW Golden Runbook for Agents

Load this after `abacus-g0w0-qsgw-workflow.md` when the task is to actually
prepare, run, continue, or audit a periodic ABACUS -> PyATB -> LibRPA
`g0w0_band` or `qsgw_band0` calculation.

## First Decision

Choose exactly one route and record it:

- `paper_strict_full_bz_g0w0`: exact G0W0 reproduction of a source bundle.
- `production_symmetry_qsgw`: QSGW, head-wing refresh, shrink, or continued
  iterations.

Do not infer physical settings from Si unless the material is Si. Infer
occupied bands from the current run.

## Minimal Execution Contract

1. Create a fresh run directory.
2. Copy only source inputs and matched helper scripts.
3. Normalize stale ABACUS interface keys only.
4. Verify PP/NAO/ABFS, `nbands`, shrink, k-mesh, and band path.
5. Run static checks before any remote submission.
6. Run stages in order:
   `SCF -> full-grid PyATB -> NSCF -> preprocess -> LibRPA`.
7. Verify stage markers before moving to the next stage.
8. Extract gaps using material-specific occupations.

## G0W0 Success Markers

- SCF: `running_scf.log`, charge restart, `vxc_out.dat`, and symmetry sidecars
  when symmetry is enabled.
- PyATB: `pyatb_librpa_df/band_out` and `KS_eigenvector_*.dat`.
- NSCF: `running_nscf.log` and `eig.txt` or `eig_occ.txt`.
- Preprocess: `band_KS_*`, `band_vxc*`, and `band_kpath_info`.
- LibRPA: successful rank-0 log and `GW_band_spin_*`.

## QSGW Iteration Contract

For refreshed head-wing QSGW, one LibRPA outer step equals one PyATB refresh
opportunity.

Use:

```text
task = qsgw_band0
qsgw_checkpoint_every = 1
qsgw_export_hamiltonian_for_pyatb = t
qsgw_hr_export_full_mp_rgrid = t
qsgw_band0_unoccupied_keep = 10
qsgw_band0_cut_mode = 2
qsgw_band0_cut_shift_ha = 20.0
qsgw_band0_update_hartree = f
```

Iteration 1 uses `max_iter = 1`.

Iteration `i + 1` uses:

```text
qsgw_restart = t
qsgw_restart_dir = librpa.d/qsgw_checkpoints/
qsgw_restart_iteration = i
max_iter = i + 1
```

Between those calls, regenerate PyATB/head-wing inputs from
`hrs*_nao_qsgw_iter_<i>.csr`.

Use the shipped template:

- `templates/abacus-librpa-gw/template/run_qsgw_headwing_refresh_loop.sh`

The template requires a case-specific `qsgw_refresh_headwing_cmd`; this command
must consume the exported HR and update `pyatb_librpa_df/` without overwriting
root ABACUS source files.

## Reporting Contract

Every QSGW campaign report must include:

- route label
- executable branches and commits
- PP/NAO/ABFS provenance
- k-mesh, band path, `nbands`, shrink thresholds
- head-wing mode
- `qsgw_band0_unoccupied_keep`, `qsgw_band0_cut_mode`,
  `qsgw_band0_cut_shift_ha`, `qsgw_band0_update_hartree`
- per-iteration `Hamiltonian_gap`, plotted gap, wall time, and stop reason
