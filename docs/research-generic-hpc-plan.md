# Data Source Research Plan: generic HPC `~/gw`

## Current Status

- Direct connection to the target login node may fail before VPN / bastion / routing is ready.
- Jump-host access may also fail until the site network path is confirmed.

## Minimal Collection Tasks (when connected)

1. Case inventory
   - Directory tree at depth 2-3
   - Group by system/task type (GW/RPA/EXX)

2. Input parameter sampling
   - `INPUT_scf`, `INPUT_nscf`, `librpa.in`
   - Distribution of key parameters (`nbands`, `nfreq`, `use_shrink_abfs`)

3. Failure-case index
   - Extract common log error keywords (for example `stod`)

4. Rule-card generation
   - Derive rule cards from real cases, each linked to source paths

## Collection Outputs

- `data/gw-index.tsv`
- `data/param-snapshots/*.txt`
- `rules/cards/*.yml` (derived from real cases)

## Quick Command (when connected)

```bash
bash scripts/collect_gw_inventory.sh hpc-login ~/gw
```
