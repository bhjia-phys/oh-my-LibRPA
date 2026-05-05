# FHI-Aims G0W0-Band Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new sibling skill for periodic-solid `FHI-aims + LibRPA` `g0w0_band` workflows, with default two-stage Slurm decomposition, automatic `control.in` skeleton guidance, and ABACUS-aligned setup rules, while leaving the existing QSGW skill untouched.

**Architecture:** Create a new `oh-my-librpa-fhi-aims-g0w0-band` skill tree with two focused reference documents, add one new user-facing guide, and update only the top-level router so `FHI-aims + g0w0_band` requests land in the new lane. Keep the existing `oh-my-librpa-fhi-aims-qsgw` skill unmodified and verify that the new routing text does not blur the task boundary.

**Tech Stack:** Markdown skill files, Markdown guides, `rg`, `sed`, `git`

---

### Task 1: Capture the baseline failure state

**Files:**
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`
- Verify: `/Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-qsgw.md`

- [ ] **Step 1: Prove the new sibling skill tree does not yet exist**

Run:

```bash
find /Users/ghj/code/oh-my-librpa/skills -maxdepth 2 -type d | sort | grep 'oh-my-librpa-fhi-aims-g0w0-band'
```

Expected: no output.

- [ ] **Step 2: Prove the new user guide does not yet exist**

Run:

```bash
test -f /Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md
```

Expected: non-zero exit status.

- [ ] **Step 3: Prove the top-level router does not yet mention the new `g0w0_band` route**

Run:

```bash
rg -n "oh-my-librpa-fhi-aims-g0w0-band|g0w0_band" /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md
```

Expected: no matches that route to a dedicated `g0w0_band` sibling skill.

- [ ] **Step 4: Prove the existing QSGW skill is currently the only FHI-aims case lane**

Run:

```bash
find /Users/ghj/code/oh-my-librpa/skills -maxdepth 2 -type d | sort | grep 'oh-my-librpa-fhi-aims'
```

Expected:

```text
/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw
```

### Task 2: Add the new `g0w0_band` skill tree

**Files:**
- Create: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md`
- Create: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md`
- Create: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md`

- [ ] **Step 1: Write the main skill**

Create `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md` with content shaped like:

```md
---
name: oh-my-librpa-fhi-aims-g0w0-band
description: Use when users ask for periodic-solid FHI-aims + LibRPA g0w0_band workflows, especially when they need a two-stage aims-and-LibRPA job layout, a control.in skeleton from geometry.in, or alignment to an ABACUS comparison case.
---

# oh-my-librpa-fhi-aims-g0w0-band

Treat this skill as the periodic-solid `FHI-aims + LibRPA` lane for `g0w0_band`.

If the request is about QSGW-family tasks such as `qsgw_band`, `qsgw_band0`, `qsgw`, or `qsgwa`, stop and hand the task to `skills/oh-my-librpa-fhi-aims-qsgw/`.

If the request is about building or repairing the executable itself, stop and hand the task to `skills/fhi-aims-build/`.

## Scope

- periodic solids only
- `g0w0_band` only
- `geometry.in` and `control.in` intake
- two-stage Slurm submission

## Hard Defaults

- `FHI-aims` runs as the MPI-heavy stage
- `LibRPA` runs as the OpenMP-heavy stage
- default workflow uses two separate scripts:
  - `run_aims.sh`
  - `run_librpa.sh`
- do not default to a single script that chains both stages
- `geometry.in` uses Angstrom by default
- both `atom` and `atom_frac` are allowed

## Intake States

- `geometry.in + control.in`
- `geometry.in` only
- trusted old reference case
- ABACUS comparison case present

## Required Reads

- read `references/periodic-solid-defaults.md`
- if the host is `df_iopcas_ghj`, also read `references/df-periodic-solid-example.md`

## Core Workflow

1. Confirm the case is periodic-solid `g0w0_band`.
2. If `control.in` is missing, generate a skeleton from `geometry.in` and the active element list.
3. If ABACUS comparison inputs exist, align:
   - structure
   - `k_grid`
   - band path
   - band-point counts
4. Stage two job scripts:
   - `run_aims.sh` for the MPI-heavy aims stage
   - `run_librpa.sh` for the OpenMP-heavy LibRPA stage
5. Stop before submission when the user asks for staging only.
```

- [ ] **Step 2: Write the periodic-solid defaults reference**

Create `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md` covering:

```md
# Periodic-Solid Defaults for FHI-Aims + LibRPA G0W0 Band

## Geometry

- `geometry.in` is interpreted in Angstrom
- periodic solids use `lattice_vector`
- atomic coordinates may use `atom` or `atom_frac`

## Species Defaults

- default family: `defaults_2020/intermediate_gw`
- generate the species blocks from the active element list when `control.in` is absent

## ABACUS Alignment

When an ABACUS comparison case exists, preserve:

- lattice and atomic structure
- `k_grid`
- band path
- number of points on each band segment

## Slurm Decomposition

- `run_aims.sh` is MPI-heavy and low-OMP
- `run_librpa.sh` is low-MPI and high-OMP
- do not treat a single combined script as the default workflow

## Minimal Control Header Expectations

- periodic solid settings
- a `g0w0_band`-appropriate global header
- room for reference-case overrides
```

- [ ] **Step 3: Write the `df` worked example**

Create `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md` with the validated host-specific anchors:

```md
# DF Periodic-Solid G0W0 Band Example

Use this reference when the user wants the default periodic-solid `FHI-aims + LibRPA` route staged on `df_iopcas_ghj`.

## Species Defaults

- `/data/home/df_iopcas_ghj/app/FHIaims-master/species_defaults/defaults_2020/intermediate_gw`

## Host Notes

- keep host-specific executable paths here, not in the main skill body
- stage two scripts by default:
  - `run_aims.sh`
  - `run_librpa.sh`

## Operational Expectation

- aims stage: MPI-heavy
- LibRPA stage: OpenMP-heavy
- align to ABACUS structure and band settings when comparison inputs exist
```

- [ ] **Step 4: Verify the new skill tree exists**

Run:

```bash
find /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band -maxdepth 3 -type f | sort
```

Expected:

```text
/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md
/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md
/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md
```

### Task 3: Add the new user guide

**Files:**
- Create: `/Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md`

- [ ] **Step 1: Write the new route guide**

Create `/Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md` with sections like:

```md
# FHI-Aims + LibRPA G0W0-Band Guide

## Scope

- periodic solids only
- `g0w0_band` only
- separate from the QSGW route

## Core Defaults

- two-script workflow:
  - `run_aims.sh`
  - `run_librpa.sh`
- aims is MPI-heavy
- LibRPA is OpenMP-heavy

## Geometry and Control Inputs

- `geometry.in` is the periodic-solid structure file in Angstrom
- use `atom` or `atom_frac`
- if `control.in` is missing, generate a skeleton from `geometry.in`
- default species family: `defaults_2020/intermediate_gw`

## ABACUS Comparison Rule

When comparing against an ABACUS case, keep:

- structure
- `k_grid`
- band path
- band-point counts

## Boundaries

- use the QSGW route for `qsgw_band`, `qsgw_band0`, `qsgw`, and `qsgwa`
- use the build skill when the request is about compiling FHI-aims itself
```

- [ ] **Step 2: Verify the guide is discoverable**

Run:

```bash
test -f /Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md && sed -n '1,120p' /Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md
```

Expected: the new guide exists and clearly separates `g0w0_band` from the QSGW route.

### Task 4: Update the top-level router

**Files:**
- Modify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md`

- [ ] **Step 1: Add route-selection language for the new `g0w0_band` sibling**

Update the top-level router so it distinguishes:

```md
- strong `FHI-aims -> LibRPA` markers: `control.in`, FHI-aims user intent, or explicit tasks such as `g0w0_band`, `qsgw_band`, `qsgw_band0`, `qsgw`, `qsgwa`
...
5. If the user asks for `FHI-aims + LibRPA` periodic `g0w0_band`, route through `skills/oh-my-librpa-fhi-aims-g0w0-band/`.
6. If strong FHI-aims markers are present and the task is QSGW-family, route through `skills/oh-my-librpa-fhi-aims-qsgw/`.
```

Add a matching bullet under `Routing rules`:

```md
- User explicitly asks for `FHI-aims + LibRPA` periodic `g0w0_band` -> route to `skills/oh-my-librpa-fhi-aims-g0w0-band/`
```

- [ ] **Step 2: Verify the existing QSGW route remains present**

Run:

```bash
rg -n "oh-my-librpa-fhi-aims-g0w0-band|oh-my-librpa-fhi-aims-qsgw|g0w0_band|qsgw_band" /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md
```

Expected: matches for both sibling routes, with `g0w0_band` and QSGW-family tasks clearly separated.

### Task 5: Verify the boundary and document the outcome

**Files:**
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md`
- Verify: `/Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md`
- Verify untouched: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`

- [ ] **Step 1: Prove the new route contains the required operational anchors**

Run:

```bash
rg -n "run_aims\\.sh|run_librpa\\.sh|Angstrom|atom_frac|intermediate_gw|ABACUS|k_grid|band path|OpenMP|MPI" \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md \
  /Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md
```

Expected: all core defaults appear across the new files.

- [ ] **Step 2: Prove the old QSGW skill stayed untouched**

Run:

```bash
git diff -- /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md
```

Expected: no output.

- [ ] **Step 3: Stage and commit only the new route work**

Run:

```bash
git add \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md \
  /Users/ghj/code/oh-my-librpa/docs/guide/fhi-aims-librpa-g0w0-band.md \
  /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md \
  /Users/ghj/code/oh-my-librpa/docs/superpowers/plans/2026-04-17-fhi-aims-g0w0-band-skill.md
git commit -m "skills: add FHI-aims g0w0-band route"
```
