# DF Periodic-Solid G0W0 Band Example

Use this reference when the user wants the default periodic-solid `FHI-aims + LibRPA` `g0w0_band` route staged on `df_iopcas_ghj`.

## Species Defaults

- `/data/home/df_iopcas_ghj/app/FHIaims-master/species_defaults/defaults_2020/intermediate_gw`

This is the validated example location for the default species family on `df`. Keep this as a worked example, not a universal hardcoded path for every host.

## Validated Executables

FHI-aims example:

- `/data/home/df_iopcas_ghj/app/FHIaims-master/build/aims.260331.scalapack.mpi.x`

LibRPA examples:

- `/data/home/df_iopcas_ghj/app/librpa/LibRPA_eigscreen_20260408-090222/build/chi0_main.exe`
- `/data/home/df_iopcas_ghj/app/librpa/LibRPA/build/chi0_main.exe`

Pick the active LibRPA binary intentionally. Do not assume every build tree is equivalent.

## Host Expectations

- stage two scripts by default:
  - `run_aims.sh`
  - `run_librpa.sh`
- keep `run_aims.sh` MPI-heavy
- keep `run_librpa.sh` OpenMP-heavy
- preserve ABACUS structure, `k_grid`, and band settings when the FHI-aims case is meant for cross-stack comparison

## Practical Notes

- keep host-specific executable paths in the case-local scripts, not in the main skill body
- if the user has both a trusted old FHI-aims case and an ABACUS comparison case, preserve:
  - executable-path style from the trusted FHI-aims case
  - structure and band comparability from the ABACUS case
- if `control.in` is auto-generated, source species blocks from `intermediate_gw` and then patch the global header to match the comparison target
