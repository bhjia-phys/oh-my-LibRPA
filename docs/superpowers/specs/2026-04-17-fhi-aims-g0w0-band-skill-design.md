# FHI-Aims G0W0-Band Skill Design

## Context

The repository already has a stack-layer route for `FHI-aims -> LibRPA` QSGW-style workflows, centered on `skills/oh-my-librpa-fhi-aims-qsgw/`. That route is intentionally broad enough for case mirroring and staged QSGW campaigns, but it does not yet encode the stricter operational defaults the user wants for periodic `g0w0_band` work.

The user wants Codex to learn a reusable, chat-first workflow for `FHI-aims + LibRPA` periodic `g0w0_band` calculations without modifying the existing QSGW skill. The new workflow should reflect how these runs are actually used in practice: they are often paired with `ABACUS + LibRPA` calculations for direct comparison, so structure, k-grid, and band-path choices should stay aligned whenever both input families are available.

## Goal

Add a new dedicated skill for periodic-solid `FHI-aims + LibRPA` `g0w0_band` workflows, with strong defaults for two-stage submission, automatic `control.in` skeleton generation from `geometry.in`, and ABACUS-aligned setup when comparison inputs exist, while leaving the current QSGW skill unchanged.

## Scope

This design covers:

- one new stack-layer sibling skill dedicated to `FHI-aims + LibRPA` periodic `g0w0_band`
- one periodic-solid defaults reference file for that skill
- one `df`-based worked example reference file
- top-level routing updates in `skills/oh-my-librpa/SKILL.md`
- one new user-facing guide for the `g0w0_band` route

This design does not cover:

- changes to `skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`
- changes to QSGW task handling such as `qsgw_band`, `qsgw_band0`, `qsgw`, or `qsgwa`
- molecular workflows
- 2D workflows
- a full automated translator from every ABACUS keyword into FHI-aims syntax
- a code generator script for `control.in`, `run_aims.sh`, or `run_librpa.sh`

## Recommended Structure

Create this new skill tree:

- `skills/oh-my-librpa-fhi-aims-g0w0-band/SKILL.md`
- `skills/oh-my-librpa-fhi-aims-g0w0-band/references/periodic-solid-defaults.md`
- `skills/oh-my-librpa-fhi-aims-g0w0-band/references/df-periodic-solid-example.md`

Create this new guide:

- `docs/guide/fhi-aims-librpa-g0w0-band.md`

Modify this existing file:

- `skills/oh-my-librpa/SKILL.md`

Do not modify:

- `skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`

## Why a New Sibling Skill

The new behavior should not be folded into the existing QSGW skill.

Reasons:

- the user explicitly wants the QSGW skill left alone
- `g0w0_band` in practice needs a narrower, stronger default workflow than the broader QSGW route
- the periodic-solid `g0w0_band` route needs its own default rules for Slurm decomposition, `control.in` generation, and ABACUS alignment
- keeping `g0w0_band` separate reduces the chance that future Codex instances mix single-shot band workflows with self-consistent QSGW workflows

The result should be two parallel FHI-aims stack-layer routes:

- `skills/oh-my-librpa-fhi-aims-qsgw/` for QSGW-family tasks
- `skills/oh-my-librpa-fhi-aims-g0w0-band/` for periodic-solid `g0w0_band`

## Trigger Design

The new skill should trigger when the user clearly asks for:

- `FHI-aims + LibRPA`
- `g0w0_band`
- periodic solids
- staging or running a case from `control.in` and `geometry.in`
- preparing an FHI-aims-side comparison against an ABACUS case

The top-level router should prefer the new skill when:

- the user explicitly mentions `FHI-aims`
- the user explicitly mentions `g0w0_band`, `G0W0 band`, or an equivalent single-shot GW-band intent
- the bundle is FHI-aims-owned or the user explicitly says the run should be built with FHI-aims inputs

The router should continue sending QSGW-family tasks to the existing QSGW skill.

## Core Workflow Rules

The new skill should teach the following as hard defaults, not soft suggestions.

### 1. Two-stage job decomposition

The skill must treat `FHI-aims` and `LibRPA` as two separate Slurm jobs by default:

- `run_aims.sh`
- `run_librpa.sh`

The reasoning should be explicit:

- `FHI-aims` is treated as an MPI-parallel stage
- `LibRPA` is treated as an OpenMP-heavy stage with as many threads per rank as practical

The skill should reject the single-script pattern as the default workflow for this route.

### 2. Geometry conventions

For periodic solids:

- `geometry.in` uses Angstrom by default
- lattice and atomic positions should be represented directly in FHI-aims syntax
- both `atom` and `atom_frac` are allowed

The skill should teach that the physical structure should remain aligned with the upstream comparison case when one exists.

### 3. Automatic `control.in` skeleton generation

If the user provides `geometry.in` but not `control.in`, the skill should generate a periodic-solid `control.in` skeleton automatically.

That generated skeleton should:

- use `defaults_2020/intermediate_gw` species defaults as the baseline
- include periodic `g0w0_band`-appropriate settings
- leave room for user or reference-case overrides

The default worked example path should be recorded as:

- `/data/home/df_iopcas_ghj/app/FHIaims-master/species_defaults/defaults_2020/intermediate_gw`

The skill should not treat that literal path as the only valid location on every host. It should be an example of the default family, not a universal hardcoded install path.

### 4. ABACUS comparison alignment

Because these calculations are often compared directly to `ABACUS + LibRPA`, the skill should default to alignment when ABACUS-side inputs exist.

The alignment targets should be:

- lattice and atomic structure
- `k_grid`
- band path
- number of points on each band segment

The skill should prefer preserving comparability over inventing a new band path or k-grid when ABACUS reference inputs already define them.

### 5. Fresh-run discipline

The default execution order should be:

- prepare or validate `geometry.in`
- prepare or validate `control.in`
- run `FHI-aims`
- run `LibRPA`

The skill should keep the case-stage language operational:

- what was reused from a reference
- what was auto-generated
- what was aligned to ABACUS
- what still needs user confirmation before submission

## Main Skill Content Plan

The new `SKILL.md` should stay compact and decision-oriented.

It should cover these phases:

### 1. Route confirmation

The skill must confirm all of the following before proceeding:

- upstream family is `FHI-aims + LibRPA`
- task is `g0w0_band`
- system class is periodic solid

If those conditions are not met, the skill should hand off instead of stretching scope.

### 2. Intake logic

The skill should classify the case into one of these entry states:

- `geometry.in + control.in` already provided
- `geometry.in` only
- reference case path provided
- ABACUS comparison case also provided

### 3. `control.in` generation rules

The skill should teach how to build a minimal periodic-solid `control.in` skeleton from:

- a periodic structure
- the element list
- `intermediate_gw` species defaults
- a `g0w0_band`-appropriate global-header block

The generated file should include the expected global settings family, while keeping detailed physics overrides open to future extension.

### 4. Slurm decomposition rules

The skill should define the default shapes of the two scripts:

- `run_aims.sh`: MPI-dense, low OpenMP
- `run_librpa.sh`: low MPI, high OpenMP

The skill should explain why these two stages should not be merged by default.

### 5. Reference-case mirroring

If the user provides a trusted old case, the skill should preserve:

- executable-path style
- Slurm partition style
- resource style
- directory layout

but it should still enforce the new route’s two-stage structure when the old case is ambiguous or bundled differently.

## Periodic-Solid Reference Content

`references/periodic-solid-defaults.md` should document the route’s default operational rules, including:

- how to interpret `geometry.in` for periodic solids
- the allowed use of `atom` and `atom_frac`
- the expectation that units are Angstrom
- how to source species defaults from `defaults_2020/intermediate_gw`
- the minimum required global-header content for a periodic `g0w0_band` `control.in`
- the rule that `run_aims.sh` and `run_librpa.sh` are separate by default
- the MPI-heavy versus OpenMP-heavy division between the two stages
- the rule that ABACUS comparison inputs win when there is a conflict in band path or k-grid choices

## DF Worked Example Content

`references/df-periodic-solid-example.md` should document a validated host-specific example for this route.

It should record:

- the validated `intermediate_gw` species-default family location on `df`
- one or more validated `FHI-aims` executable paths when available
- one or more validated `LibRPA` executable paths when available
- the expected two-script submission pattern on that host
- any host-specific cautions that matter for the periodic-solid `g0w0_band` route

This reference should stay example-based, not universal. Host-specific paths belong here, not in the main skill body.

## Top-Level Router Changes

`skills/oh-my-librpa/SKILL.md` should gain explicit routing for the new sibling skill.

The intended behavior is:

- if the user asks for `FHI-aims + LibRPA` periodic `g0w0_band`, route to `skills/oh-my-librpa-fhi-aims-g0w0-band/`
- if the user asks for QSGW-family tasks, keep routing to `skills/oh-my-librpa-fhi-aims-qsgw/`
- if the request is about building or repairing the executable itself, keep routing to `skills/fhi-aims-build/`

This should preserve the current stack split while making the `g0w0_band` lane explicit.

## New User Guide

Add a new guide file:

- `docs/guide/fhi-aims-librpa-g0w0-band.md`

This guide should explain:

- when the new route applies
- how it differs from the QSGW route
- the two-stage job rule
- the periodic-solid `geometry.in` conventions
- the default `control.in` generation behavior
- the ABACUS-comparison alignment rule

The existing QSGW guide should not be repurposed to carry this route’s details.

## Style Constraints

The new skill should be:

- narrow in scope
- explicit about its hard defaults
- operational instead of tutorial-like
- comparison-aware when ABACUS inputs exist
- host-agnostic in the main body
- host-specific only in the worked example reference

## Success Criteria

The design is successful if, after implementation:

- a future Codex instance can recognize `FHI-aims + LibRPA` periodic `g0w0_band` as a route distinct from the QSGW route
- the existing QSGW skill remains untouched
- the new route defaults to two separate Slurm jobs for `FHI-aims` and `LibRPA`
- the new route can generate a usable periodic-solid `control.in` skeleton from `geometry.in` alone
- ABACUS comparison inputs automatically guide the FHI-aims-side `geometry`, `k_grid`, and band-path choices
- host-specific path examples remain isolated to reference documents rather than leaking into the main skill body
