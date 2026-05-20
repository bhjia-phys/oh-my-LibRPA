# OML Content Map

This page explains what `oh-my-LibRPA` contains and which layer should be
changed for each kind of improvement.

`oh-my-LibRPA` is not a replacement for ABACUS, PyATB, LibRPA, or FHI-aims.
It is a workflow and knowledge layer around those codes: it routes natural
language requests, validates case bundles, materializes inputs, runs staged
jobs, and records what happened.

## Layer Map

| Layer | Path | Primary reader | Purpose |
| --- | --- | --- | --- |
| Human overview | `README.md`, `docs/guide/` | humans and agents | Explain capabilities, installation, validated workflows, and current benchmark status. |
| Chat router | `skills/oh-my-librpa/SKILL.md` | agents | Classify the user's files and intent, then choose the correct stack and workflow route. |
| Stack skills | `skills/oh-my-librpa-*`, `skills/abacus-librpa-*`, `skills/fhi-aims-*` | agents | Keep ABACUS, FHI-aims, GW, RPA, debug, and build workflows separated. |
| Workflow references | `skills/oh-my-librpa/references/` | agents | Encode detailed stage order, benchmark provenance, route-specific settings, and known failure modes. |
| Rule cards | `rules/cards/` and `skills/oh-my-librpa/rules/cards/` | agents | Small scene-specific rules for recurring decisions, checks, and fixes. |
| Executable helpers | `scripts/` and `skills/oh-my-librpa/scripts/` | humans and agents | Preflight, consistency checks, server profiles, staged workflow runners, and reporting helpers. |
| Templates | `templates/` and `skills/oh-my-librpa/templates/` | humans and agents | Input skeletons and plotting helpers used to materialize reproducible cases. |
| Basis assets | `skills/oh-my-librpa/assets/abacus_abfs_nao_pp_gw/` | agents | Curated ABACUS PP/NAO/ABFS bundles for GW and paper-dataset reproduction. |
| Registry | `registry/` and `skills/oh-my-librpa/registry/` | agents and tools | Machine-readable domain metadata, compatibility matrix, and host profile examples. |
| Examples | `examples/` | humans and agents | Concrete walkthroughs and expected artifacts. |
| Historical data | `data/`, `docs/phase-0-history.md`, older plans/specs | maintainers | Prior inventories, design notes, and development history. |

## Installed Layout

`install.sh` copies two kinds of content:

- `skills/` goes to the assistant skill directory so the agent can load
  `SKILL.md` entry points directly.
- `rules/`, `templates/`, `references/`, `docs/`, `scripts/`, `registry/`,
  and `examples/` go to the `oh-my-librpa` workspace asset directory.

The duplicated `rules/` and `templates/` copies are intentional: they make the
same operational material available both as skill-local context and as
workspace assets. When changing shared templates or rule cards, update both
copies together.

## Main Scientific Routes

| Route | Use when | Canonical reference |
| --- | --- | --- |
| Molecular GW | Isolated molecule, no periodic band path | `skills/oh-my-librpa/references/gw-route.md` |
| Periodic G0W0 | Solid GW band structure | `skills/oh-my-librpa/references/gw-route.md` |
| Periodic symmetry GW | Solid GW with ABACUS symmetry sidecars | `skills/oh-my-librpa/references/gw-route.md` |
| ABACUS G0W0/QSGW | Si/MgO/public-style ABACUS -> PyATB -> LibRPA workflow | `skills/oh-my-librpa/references/abacus-g0w0-qsgw-workflow.md` |
| Paper dataset materials | User-provided `paper_dataset_GW_pseudopotential+NAO.zip` materials | `skills/oh-my-librpa/references/paper-dataset-material-workflow.md` |
| RPA | Correlation-energy or response workflow | `skills/oh-my-librpa/references/rpa-route.md` |
| Debug | Existing logs, failures, mismatched outputs | `skills/oh-my-librpa/references/debug-route.md` |
| FHI-aims QSGW/G0W0 | FHI-aims-owned cases | `docs/guide/fhi-aims-librpa-qsgw.md` and stack-specific skills |

## Current ABACUS QSGW Invariants

For the validated ABACUS -> PyATB -> LibRPA QSGW route:

- ABACUS owns SCF/NSCF source files and generated matrix outputs.
- PyATB owns full regular MP-grid velocity/eigenvector data for head/wing.
- LibRPA owns `g0w0_band` or `qsgw_band0` execution and checkpoints.
- Exact paper G0W0 reproduction and production symmetry QSGW are distinct
  routes; do not merge their timing or q-point counts without saying so.
- `qsgw_band0_unoccupied_keep`, `qsgw_band0_cut_mode`,
  `qsgw_band0_cut_shift_ha`, and `qsgw_band0_update_hartree` must be explicit.
- Head-wing-refresh QSGW should run one outer iteration at a time:
  checkpoint -> HR export -> PyATB/head-wing refresh -> LibRPA restart.
- Occupied bands must be inferred from the current material, not hard-coded
  from Si.

## Maintenance Rules

- Put user-facing explanations in `docs/guide/`.
- Put agent-only operational details in `skills/oh-my-librpa/references/`.
- Put short reusable decision rules in `rules/cards/`.
- Put executable checks in `scripts/`, then cover them in `scripts/self_test.sh`.
- Keep root `templates/` and skill-local `skills/oh-my-librpa/templates/`
  synchronized.
- Keep validated code commits, branch names, k-meshes, basis/pseudopotential
  provenance, and benchmark numbers in the route reference, not only in chat.
