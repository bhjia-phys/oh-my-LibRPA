# ABACUS -> PyATB -> LibRPA G0W0/QSGW Band Workflow

Load this reference for periodic ABACUS-owned solid workflows that ask for
`g0w0_band`, `qsgw_band0`, head/wing correction, shrink, symmetry, or Si/MgO
benchmark reproduction.

If the source is the user-provided `paper_dataset_GW_pseudopotential+NAO.zip`
or the user asks for all paper benchmark materials, also load
`paper-dataset-material-workflow.md`. That reference maps the dataset material
directories to this stricter stage order and records which entries are
complete source bundles versus result-only references.

When the task is to execute or continue the workflow, also load
`abacus-g0w0-qsgw-golden-runbook.md`. It turns this reference into a concrete
step-by-step runbook and points to the refreshed-QSGW continuation template.

## Provenance Snapshot

Use these versions as the currently validated dongfang reference, recorded on
2026-05-20:

- ABACUS: `/data/home/df_iopcas_bhj/software-stack/src/abacus-old-libri`
  - branch: `codex/merge-ri-moment-gw-symmetry-old-libri`
  - commit: `f0a1e171160d023e07c342870b0a8ad82039ca41`
  - reason: current route still needs old LibRI-compatible ABACUS matrix outputs.
- LibRPA: `/data/home/df_iopcas_bhj/software-stack/src/LibRPA_codex`
  - branch: `codex/qsgw-band0-hartree-merge-20260517`
  - commit: `8476213f66c68efb43404713eacbd04966820f26`
  - commit title: `qsgw_band0: save head-wing refresh and Hartree merge`
- PyATB: `/data/home/df_iopcas_bhj/ai-runs/pyatb-bhjia-19661b4-private-20260516/site_nodeps`
  - required API: `get_velocity_matrix()` returns
    `eigenvalues, eigenvectors, velocity_matrix`.
- oh-my-LibRPA merge base: keep AroundPeking/upstream as primary. The bhjia
  fork has already been merged into upstream history; do not overwrite upstream
  workflow logic with stale local helper experiments.

Do not run SCF, NSCF, PyATB, or LibRPA workloads on a login node. Use `sbatch`.

## Strict Stage Order

For a periodic solid with head/wing and shrink, use this order:

1. Create a fresh run directory. Copy only source inputs and helper scripts.
2. Run ABACUS SCF.
3. Run PyATB on the full regular MP grid to create `pyatb_librpa_df/`.
4. Run ABACUS NSCF on the band path.
5. Run `preprocess_abacus_for_librpa_band.py`.
6. Run LibRPA `g0w0_band` or `qsgw_band0`.
7. For QSGW refresh iterations, regenerate the PyATB/head-wing input from the
   exported QSGW Hamiltonian before the next iteration.

Never copy generated files such as `OUT.ABACUS`, `band_out`, `coulomb_*`,
`Cs_*`, `librpa.d`, `LibRPA*.out`, or old `GW_band_spin_*` into a new run as
if they were source inputs.

## Two Valid Periodic Routes

Keep these routes distinct in reports and scripts:

- `paper_strict_full_bz_g0w0`: reproduce a published dataset case exactly.
  If the archived input used `symmetry -1`, keep the full-BZ route for that
  one reproduction. This may process all MP q-points, for example 512 q-points
  on an 8x8x8 grid.
- `production_symmetry_qsgw`: use `INPUT_scf: symmetry 1` and
  `INPUT_nscf: symmetry -1`, then let LibRPA consume the ABACUS symmetry
  sidecars. This is the validated route for `qsgw_band0`, head-wing refresh,
  shrink, and continued QSGW iterations.

Do not compare wall times across these routes as if they used the same q-grid.
For example, a strict MgO G0W0 run with 512 full-BZ q-points can take much
longer than a symmetry QSGW iteration using the 29 irreducible q-points from
the same 8x8x8 mesh.

## ABACUS Settings

Use the current ABACUS keyword names. Reject stale inputs containing
`exx_use_ewald`, `cs_inv_thr`, `exx_spencer_type`, or `out_bandgap`.

For the symmetry+shrink lane:

- `INPUT_scf`
  - `calculation scf`
  - `symmetry 1`
  - `rpa 1`
  - `out_chg 1`
  - `out_mat_xc 1`
  - `out_mat_hs2 1`
  - `out_mat_r 1`
  - `exx_separate_loop 1`
  - `exx_pca_threshold 10`
  - `exx_singularity_correction massidda`
  - `exx_real_number 1`
  - `exx_cs_inv_thr 1e-5`
  - `shrink_abfs_pca_thr 1e-4`
  - `shrink_lu_inv_thr 1e-3`
- `INPUT_nscf`
  - `calculation nscf`
  - `symmetry -1`
  - `init_chg file`
  - `out_mat_xc 1`
  - `out_mat_hs 1`
  - `out_mat_hs2 1`
  - `out_wfc_lcao 1`

The symmetry sidecars must come from the same SCF that generated Coulomb and
shrink data:

- `irreducible_sector.txt`
- `symrot_R.txt`
- `symrot_k.txt`
- `symrot_abf_k.txt` when `use_shrink_abfs = t`

G0W0 paper reproduction cases may intentionally use a no-symmetry SCF if that
is how the published reference bundle was built. QSGW `qsgw_band0` with
head-wing refresh should use the symmetry+shrink lane above.

## PyATB Full-Grid Rule

For head/wing, `pyatb_librpa_df` must be generated on the full regular MP grid.
Do not feed IBZ k-points or star weights into PyATB.

Use the public-style `output_librpa.py` route based on:

- `mp_generator`
- `kpoints_in_different_process`
- `get_velocity_matrix`

The expected k-order is the public x-fast MP order, for example the first rows
on an 8x8x8 grid are `(0,0,0)`, `(1/8,0,0)`, `(2/8,0,0)`, ...

Do not replace this with an unvalidated hand-written full-BZ loop. That changes
the ordering contract consumed by LibRPA and can silently corrupt head/wing
comparisons.

## LibRPA G0W0 Preset

Use this baseline unless a reference bundle explicitly differs:

```text
task = g0w0_band
nfreq = 16
n_params_anacon = 16
option_dielect_func = 3
replace_w_head = t
use_scalapack_gw_wc = t
use_scalapack_ecrpa = t
parallel_routing = libri
vq_threshold = 0
sqrt_coulomb_threshold = 0
use_shrink_abfs = t
use_abacus_exx_symmetry = t
use_abacus_gw_symmetry = t
use_fullcoul_exx = t
use_pyatb = t
output_energy_qp = t
output_gw_sigc_mat_rf = f
libri_chi0_threshold_C = 1e-4
libri_chi0_threshold_G = 1e-5
libri_exx_threshold_V = 1e-1
libri_exx_threshold_C = 1e-4
libri_exx_threshold_D = 1e-4
libri_g0w0_threshold_C = 1e-5
libri_g0w0_threshold_G = 1e-5
libri_g0w0_threshold_Wc = 1e-6
output_dir = librpa.d/
```

## LibRPA QSGW Band0 Preset

Start from the G0W0 preset and replace the task block with:

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
output_dir = librpa.d/
```

For restart:

```text
qsgw_restart = t
qsgw_restart_dir = librpa.d/qsgw_checkpoints/
qsgw_restart_iteration = <last completed iteration>
```

Use `qsgw_band0_update_hartree = f` for the current ABACUS benchmark route
unless the test explicitly studies Hartree updates. Hartree-update support is
present in the validated LibRPA branch, but the Si/MgO head-wing-refresh
benchmarks keep it disabled to preserve the legacy comparison.

For head-wing refresh, do not ask one LibRPA call to run all QSGW iterations
without refreshing PyATB data. Run one outer iteration at a time:

1. Let LibRPA finish iteration `i` and write
   `librpa.d/qsgw_checkpoints/iter_<i>/H0_GW_spin_...bin`.
2. Use the exported `hrs*_nao_qsgw_iter_<i>.csr` files to regenerate the
   full-MP-grid PyATB/head-wing inputs.
3. Launch the next LibRPA call with `qsgw_restart = t`,
   `qsgw_restart_iteration = i`, and `max_iter = i + 1`.
4. Stop when the log reports `Converged after N iterations`, or when the
   campaign cap is reached. Use 20 iterations as the current conservative cap
   for MgO-style convergence tests unless the user asks for a different limit.

Use `templates/abacus-librpa-gw/template/run_qsgw_headwing_refresh_loop.sh`
as the generic continuation skeleton. It still requires a material-specific
`qsgw_refresh_headwing_cmd` because HR -> PyATB refresh commands can differ by
host and helper-script layout.

The checkpoint binaries and the HR exports have different roles:

- `H0_GW_spin_...bin` under `librpa.d/qsgw_checkpoints/` is the restart state
  on the active LibRPA k-grid.
- `hrs*_nao_qsgw_iter_*.csr` is the real-space Hamiltonian export used to
  rebuild PyATB/head-wing data for the next outer iteration.

The `qsgw_band0` Hamiltonian cut is material independent in form:

- `N0` is counted from eigenvalues below the Fermi level at each k/spin.
- All occupied states are retained.
- The first `qsgw_band0_unoccupied_keep` unoccupied states are retained.
- `qsgw_band0_cut_mode = 0`: do not apply this active-window cut.
- `qsgw_band0_cut_mode = 1`: outside the active window, zero off-diagonal
  H0_GW elements and reset diagonal elements to the KS diagonal.
- `qsgw_band0_cut_mode = 2`: outside the active window, zero off-diagonal
  H0_GW elements and reset diagonal elements to the KS diagonal plus
  `qsgw_band0_cut_shift_ha`.

For Si, `N0 = 4`, so the production default retains all 4 occupied bands plus
10 unoccupied bands.

This Si value is only an example. For every other material, infer `N0` from
the Fermi level or occupations in the active run. MgO has 8 occupied bands in
the current band-path QSGW output, so a Si-specific `N0 = 4` postprocessor
gives a false many-eV gap.

## Head/Wing Branches

Use these branch labels consistently:

- `head_wing_refresh`: `replace_w_head = t`, `option_dielect_func = 3`, and
  PyATB/head-wing input is refreshed from the QSGW Hamiltonian between
  iterations.
- `head_wing_frozen`: `replace_w_head = t`, `option_dielect_func = 3`, but the
  initial head+wing input is kept fixed after the first step.
- `head_only_then_frozen`: `replace_w_head = t`, `option_dielect_func = 4`, and
  only the first-step head correction is used for the frozen comparison.

When comparing branches, keep PP/NAO/ABFS, k-mesh, band path, thresholds,
`nbands`, shrink, symmetry sidecars, and plotting logic identical.

## Verified Si Reference

Use these assets for the public-style Si benchmark:

- `Si_ONCV_PBE-1.0.upf`
- `Si_gga_8au_100Ry_3s3p2d.orb`
- `Si_3s3p2d1f1g_pca1e-6.abfs`
- basis: TZDP-like `3s3p2d`, 44 NAO functions per Si atom
- primitive cell: 2 Si atoms, 88 total NAO functions
- lattice constant: `5.431 Angstrom`
- default SCF grid for the validated production route: `8 8 8`

Validated paper-path G0W0 data from the 2026-05-17 k888 run:

- KS indirect path gap: `0.56060 eV`
- G0W0 indirect path gap: `1.09289 eV`
- QSGW `qsgw_band0` iteration 1 path gap: `1.23721 eV`

Validated Si QSGW iteration-10 gaps:

| k mesh | head_wing_refresh | head_wing_frozen | head_only_then_frozen |
| --- | ---: | ---: | ---: |
| 4x4x4 | 1.094080 eV | 1.217810 eV | 1.199720 eV |
| 6x6x6 | 1.146240 eV | 1.224700 eV | 1.205940 eV |
| 8x8x8 | 1.139710 eV | 1.188490 eV | 1.175850 eV |

At k888, `head_wing_refresh` was stable by iterations 8-10 to below
0.01 meV in the extracted path gap.

## Verified MgO Reference

Use the user-provided paper-strict MgO assets as the primary MgO benchmark:

- `Mg_ONCV_PBE-1.0.upf`
- `Mg_gga_8au_100Ry_6s3p2d.orb`
- `Mg_6s3p2d1f1g_pca1e-6.abfs`
- `O_ONCV_PBE-1.0.upf`
- `O_gga_8au_100Ry_3s3p2d.orb`
- `O_3s3p2d1f1g_pca1e-6.abfs`
- `nbands = 47`
- `ecutwfc = 120`
- SCF k-mesh: `8 8 8`
- band path: `G-K-L-U-W-W2-X` with 20 segments and final 1-point endpoint
- current ABACUS keyword: `exx_singularity_correction massidda`

The strict full-BZ MgO G0W0 reproduction completed on 2026-05-20:

- run root:
  `/data/home/df_iopcas_bhj/ai-runs/mgo-paper-strict-g0w0-thr1e-3-current-abacus-20260519-141827`
- job: `1820593`
- DFT gap: `4.7199201 eV`
- EXX gap: `14.7097813 eV`
- G0W0 gap: `7.1921789 eV`
- reference paper-dataset gap: `7.1921781 eV`
- delta from reference: `8.0e-7 eV`

MgO QSGW uses the same production symmetry+shrink+head-wing-refresh route as
Si, with the Mg/O 8au paper-strict PP/NAO/ABFS bundle. The active run root is:

- `/data/home/df_iopcas_bhj/ai-runs/mgo-qsgw-band0-paper-k888-headwing-iter1-scf-sym1-20260520-115919`

Validated partial MgO QSGW data as of 2026-05-20:

| route | iteration | gap |
| --- | ---: | ---: |
| KS/PBE band-path baseline | 0 | 4.719920 eV |
| strict full-BZ G0W0 baseline | 0 | 7.192179 eV |
| production `qsgw_band0` head-wing refresh | 1 | 7.793630 eV |
| production `qsgw_band0` head-wing refresh | 2 | 8.208060 eV |

The continuation job submitted to iteration 20 is `1829520`. Treat later MgO
iterations as pending until the run logs and extracted gaps have been checked.

Do not use a gap extractor that assumes Si's four occupied bands for this MgO
output. Use `band_out`/occupation columns and infer the occupied manifold.

## Minimal Validation Before Submission

Before `sbatch`, verify:

- `INPUT_scf`, `INPUT_nscf`, `KPT_scf`, `KPT_nscf`, `STRU`, and `librpa.in`
  are from the same source bundle.
- `nbands` equals the ABACUS basis count and is identical in SCF and NSCF.
- `STRU` contains matched `NUMERICAL_ORBITAL` and `ABFS_ORBITAL` entries.
- `librpa.in: use_shrink_abfs` matches the ABACUS shrink artifacts.
- Symmetry sidecars are present when LibRPA symmetry flags are enabled.
- `get_diel.py`, `output_librpa.py`, `perform.sh`, and
  `preprocess_abacus_for_librpa_band.py` are a matched helper quartet.
- `paper_strict_full_bz_g0w0` and `production_symmetry_qsgw` are not mixed in
  the same staged run unless the report explicitly labels the route change.
- QSGW runs explicitly record `qsgw_band0_unoccupied_keep`,
  `qsgw_band0_cut_mode`, `qsgw_band0_cut_shift_ha`, and
  `qsgw_band0_update_hartree`.
- QSGW head-wing-refresh continuation uses the previous iteration's HR export
  to regenerate PyATB data before the next LibRPA restart.
- Gap extraction and plotting infer the occupied manifold from the current
  material instead of using a hard-coded Si occupied-band count. Accept both
  binary occupations such as `2.0/0.0` and weighted positive occupations such
  as MgO's `0.113.../0.0`.
