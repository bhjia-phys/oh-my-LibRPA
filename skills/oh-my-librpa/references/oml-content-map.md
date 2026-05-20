# OML Content Map for Agents

Load this reference when the user asks what OML contains, how to navigate it,
or how to optimize its structure.

## What OML Contains

- `README.md` and `docs/guide/`: human-facing installation, overview, and
  validated workflow guides.
- `skills/oh-my-librpa/SKILL.md`: the top-level chat router.
- `skills/oh-my-librpa-*`, `skills/abacus-librpa-*`, and `skills/fhi-aims-*`:
  stack- and task-specific skills.
- `skills/oh-my-librpa/references/`: detailed agent workflow contracts.
- `rules/cards/`: compact reusable decision rules and success criteria.
- `scripts/`: executable preflight, consistency, staging, and reporting tools.
- `templates/`: reusable ABACUS/LibRPA inputs and plotting helpers.
- `skills/oh-my-librpa/assets/abacus_abfs_nao_pp_gw/`: curated PP/NAO/ABFS
  assets for ABACUS GW and paper-dataset workflows.
- `registry/`: compatibility matrix, domain metadata, and host profiles.
- `examples/`: concrete run walkthroughs.
- `data/` and historical docs: previous inventories and development history.

## Optimization Boundary

Use this rule when improving OML:

- Routing changes go in `SKILL.md`.
- Scientific route contracts go in `references/*.md`.
- User-readable explanations go in `docs/guide/*.md`.
- Reusable checks go in `scripts/` and must be covered by `self_test.sh`.
- Input skeletons go in `templates/`.
- Short recurring judgment rules go in `rules/cards/`.
- PP/NAO/ABFS selections go in `assets/` plus
  `references/pp-nao-abfs-library.md`.

Do not hide validated benchmark settings only in chat. Record them in the
relevant route reference.

## Current High-Value Routes

- ABACUS public-style G0W0/QSGW:
  `references/abacus-g0w0-qsgw-workflow.md`.
- Paper dataset material workflow:
  `references/paper-dataset-material-workflow.md`.
- General ABACUS GW/RPA/debug:
  `references/gw-route.md`, `references/rpa-route.md`,
  `references/debug-route.md`.
- FHI-aims owned cases:
  route to the FHI-aims stack skills and human guides.
