# Bundled PP / NAO / ABFS Library

Read this reference when a case needs pseudopotentials, NAO basis files, or auxiliary basis files and the user has not already provided a complete authoritative bundle.

## Asset location

Use the bundled library under:

- `assets/abacus_abfs_nao_pp_gw/`

Start from:

- `assets/abacus_abfs_nao_pp_gw/README.md`

That README records tested system-level combinations and also helps infer element-wise preferred PP-family choices.

## Selection rule

Choose assets in this order:

1. If the target system is an exact tested match in the README, use that system-level combination directly.
2. Otherwise, resolve files element by element from the library directories.
3. When choosing element by element, prefer a family choice that is internally consistent across the system when possible.
4. If a mixed-family setup is necessary, explain why and call out the risk explicitly.
5. Treat the bundled library as a practical GW-oriented starting point, not a proof of global optimality.
6. If any required element is missing from the library, stop and ask the user to provide the missing PP / NAO / ABFS files. Do not silently substitute another element setup.
7. PP / NAO / ABFS must be matched as a corresponding set. Do not mix them arbitrarily across unrelated PP families, because the basis and auxiliary basis are generated for the chosen pseudopotential.
8. SOC pseudopotentials are not yet bundled in this library. If a SOC case needs PP assets that are not present yet, ask the user to upload the corresponding files.
9. If SOC is enabled, SOC pseudopotentials are mandatory. Do not run a SOC case with non-SOC pseudopotentials.
10. If the user explicitly requests a specific PP family, orbital cutoff, or orbital tier and the bundled library does not already contain that exact matched set, switch to `references/abfs-generation.md` instead of substituting an approximate library match.

## What to pull from the library

For each element, identify one corresponding set:

- pseudopotential: `*.upf`
- NAO basis: `*.orb`
- auxiliary basis: `*.abfs`

Treat these three file types as linked assets rather than independent pick-and-mix choices.

Interpret the library as an element-indexed asset store with optional system-level shortcuts from the README.

When shrink is enabled and the library contains the needed `.abfs`, use those filenames directly for `ABFS_ORBITAL` entries.

If a required element is not covered by the library, ask the user for the missing files instead of inventing a fallback.

## `df_iopcas_ghj` fallback for matched regeneration

When the user wants a regenerated matched set on `df_iopcas_ghj`, prefer the official `ABACUS-orbitals` checkout:

- checkout root: `/data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main`
- helper: `scripts/ensure_abacus_orbitals_checkout.sh /data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main`

For the current `alpha-MnTe` route, the requested matched set is:

- PP family: `Dojo-NC-SR`
- orbital cutoff: `10au`
- orbital tier: `TZDP`
- `Mn`: `Mn_gga_10au_100Ry_6s3p3d2f.orb`
- `Te`: `Te_gga_10au_100Ry_3s3p3d2f.orb`

Do not substitute the older `8au/7au` `DZP` orbitals for this route.

## Reporting requirement

When selecting files from this library, tell the user:

- which family was chosen
- whether the match was exact or approximate
- what risk the choice introduces, if any
- what low-cost validation should be done next
