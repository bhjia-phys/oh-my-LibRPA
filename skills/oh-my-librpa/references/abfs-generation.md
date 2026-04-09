# ABFS Generation

Use this reference when the user explicitly asks to generate or regenerate auxiliary basis files, or when the bundled library does not contain a matched PP / NAO / ABFS set for the requested route.

## Family lock

Treat pseudopotentials, numerical atomic orbitals, and auxiliary basis files as one locked family.

- Do not mix `Dojo-NC-SR` generated ABFS with `SG15` or other PP families.
- Do not mix `10au` GW orbitals with `7au`, `8au`, or `9au` auxiliary bases.
- Do not swap `TZDP` GW orbitals onto auxiliary bases that were generated from `DZP` inputs.
- The GW `STRU` must reuse the same `.orb` files that were used to generate the `.abfs` files.

## Default checkout on `df_iopcas_ghj`

Prefer the official `ABACUS-orbitals` checkout under:

- `/data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main`

If that checkout is missing, materialize it first:

- `scripts/ensure_abacus_orbitals_checkout.sh /data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main`

The default remote for that checkout is:

- `https://github.com/abacusmodeling/ABACUS-orbitals`

## `alpha-MnTe` matched route

For the `alpha-MnTe` GW shrink route requested by the user, lock the assets to `Dojo-NC-SR` and `10au` `TZDP`:

- `Mn` pseudopotential: `/data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main/Dojo-NC-SR/Pseudopotential/Mn.upf`
- `Te` pseudopotential: `/data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main/Dojo-NC-SR/Pseudopotential/Te.upf`
- `Mn` NAO: `/data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main/Dojo-NC-SR/Orbitals_v2.0/Mn_TZDP/Mn_gga_10au_100Ry_6s3p3d2f.orb`
- `Te` NAO: `/data/home/df_iopcas_ghj/basis_pp/ABACUS-orbitals-main/Dojo-NC-SR/Orbitals_v2.0/Te_TZDP/Te_gga_10au_100Ry_3s3p3d2f.orb`

Do not reuse the older `Mn_gga_8au_100Ry_4s2p2d1f.orb` / `Te_gga_7au_100Ry_2s2p2d1f.orb` pair for this route.

## Angular-momentum rule

When the active NAO contains `f`, the generated auxiliary basis must also keep nonzero `f` and `g`.

- If `tools/opt_abfs_bash` is used, keep `info["Nu"]` long enough that `exx_opt_orb_lmax = 4`.
- The minimal acceptable tail is nonzero `f` and nonzero `g`.
- Do not truncate the auxiliary basis request at `d` for this route.
- The skill helper `scripts/generate_gaussian_aux_orb.py` is the supported route for Gaussian high-`l` tails:
  - if the input `.orb` has no `f`, it appends `f + g`
  - if the input `.orb` already has `f` but no `g`, it appends `g` only

## Validation

Before treating a generated `.abfs` file as valid:

- confirm the `Element` header matches the target species
- confirm `Radius Cutoff(a.u.)` matches the paired `.orb`
- confirm `Number of Forbital-->` is nonzero when the paired `.orb` contains `f`
- confirm `Number of Gorbital-->` is nonzero when the paired `.orb` contains `f`
- confirm the GW `STRU` points to the same `.orb` family and cutoff that were used during ABFS generation

If any of these checks fail, reject the auxiliary basis and regenerate it instead of continuing to GW.
