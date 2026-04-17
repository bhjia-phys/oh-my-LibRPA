# FHI-Aims Build Skill Design

## Context

The `oh-my-librpa` skill set currently has a top-level router and an FHI-aims workflow skill for QSGW/G0W0 case preparation and execution, but it does not yet have a reusable skill dedicated to installing, configuring, or rebuilding FHI-aims itself. Recent work on `df_iopcas_ghj` showed that the missing build layer is not just about running `cmake` and `make`: it also requires structured diagnosis of missing submodules, empty vendored dependency directories, compiler-wrapper mismatches, and stale cache paths.

The user wants that operational knowledge abstracted into the `oh-my-librpa` skill system as a generally reusable build skill, while keeping the `df` server recovery as a concrete validated example.

## Goal

Add a new reusable skill that teaches Codex how to diagnose and repair FHI-aims build/install failures across hosts, then integrate that skill into the existing `oh-my-librpa` routing so that FHI-aims compilation requests no longer fall through to ad hoc chat reasoning.

## Scope

This design covers:

- a new skill dedicated to FHI-aims build and install work
- one host-specific reference document for `df_iopcas_ghj`
- top-level routing updates in `oh-my-librpa`
- FHI-aims workflow routing updates in `oh-my-librpa-fhi-aims-qsgw`

This design does not cover:

- automated build scripts
- generalized package installation for every dependency on every host
- case preparation or QSGW workflow content already handled by `oh-my-librpa-fhi-aims-qsgw`

## Recommended Structure

Create this new skill tree:

- `skills/fhi-aims-build/SKILL.md`
- `skills/fhi-aims-build/references/df-fhi-aims-build.md`

Modify these existing files:

- `skills/oh-my-librpa/SKILL.md`
- `skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`

## Why a Separate Skill

The build/install workflow should not be merged into `oh-my-librpa-fhi-aims-qsgw`.

Reasons:

- build/install tasks have a different trigger than case-preparation tasks
- build/debug logic for compilers, submodules, and MKL paths is reusable beyond QSGW workflows
- mixing build recovery into the case router would make the FHI-aims workflow skill harder to scan and easier to misuse

The dedicated skill should become the standard place for:

- `cmake` configure failures
- `make` failures
- missing FHI-aims vendored dependencies such as ELSI
- compiler-wrapper and cache mismatches
- host-specific toolchain examples

## Skill Trigger Design

The new skill should trigger when the user asks to:

- install FHI-aims
- compile FHI-aims
- rebuild FHI-aims
- configure FHI-aims with `cmake`
- fix a FHI-aims build error
- stage or repair a host-specific FHI-aims toolchain

The description should stay in trigger language only. It must not summarize the workflow steps in the YAML description.

## Main Skill Content Plan

The main `SKILL.md` should be compact and decision-oriented.

It should cover these phases:

### 1. Identify the build layout

The skill must first determine:

- whether the source tree is a real git clone or just a copied source snapshot
- whether the build uses vendored dependencies or external packages
- whether the reported failure is at configure time or compile/link time

### 2. Check vendored dependency integrity

For FHI-aims vendored builds, the skill should explicitly check:

- whether `external_libraries/elsi_interface/CMakeLists.txt` exists
- whether `.gitmodules` exists without a matching `.git` directory
- whether a dependency directory is present but empty

The skill must teach that `GIT_SUBMODULE=ON` is not enough when the source tree is not a true git worktree.

### 3. Check compiler-wrapper consistency

The skill should teach a structured compiler probe:

- locate `mpif90`, `mpiifort`, `mpiifx`, `ifort`, `ifx`, `icx`, `icpx`, `gcc`, and `gfortran`
- inspect `mpif90 -show`
- compare the wrapper target with the flags stored in the cache file

This is essential because an MPI wrapper may resolve to GNU while the cache still contains Intel-specific flags.

### 4. Check cache-path validity

The skill should teach that old cache files often encode stale paths for:

- MKL
- Intel classic compilers such as `icc` and `icpc`
- external ELSI roots

The expected behavior is to verify those paths before rerunning `cmake`.

### 5. Apply the smallest repair

The skill should prefer the smallest working repair:

- populate a missing vendored dependency
- point the build to an external dependency if it already exists
- update compiler entries in the cache to match the active toolchain
- replace invalid library paths with current verified ones

### 6. Reconfigure from a clean build state

The skill should recommend:

- removing `CMakeCache.txt` and `CMakeFiles/`
- rerunning `cmake`
- only then rerunning `make`

### 7. Report the first real blocker

The skill should emphasize reporting:

- the true root cause
- the concrete repair that was applied
- the first subsequent failure if the build still does not complete

## DF Reference Content

The `references/df-fhi-aims-build.md` file should document the validated `df_iopcas_ghj` example, including the exact evidence chain:

- the source tree at `/data/home/df_iopcas_ghj/app/FHIaims-master` was not a real git repository
- `.gitmodules` existed but `.git` did not
- `external_libraries/elsi_interface/` was an empty directory
- `GIT_SUBMODULE=ON` therefore could never initialize ELSI automatically
- `mpif90` resolved to `gfortran`
- Intel-specific flags in `initial_cache.example.cmake` therefore failed immediately
- `icc` and `icpc` were stale compiler names on that host
- `/opt/intel/mkl/lib/intel64` was a stale MKL path

The reference should then record the verified fix:

- clone `https://gitlab.com/elsi_project/elsi_interface.git` into `external_libraries/elsi_interface`
- switch the cache to `mpiifort`, `icx`, and `icpx`
- remove `-ip` from `icx` and `icpx` flags
- switch `LIB_PATHS` to `/data/app/intel/oneapi-2024.2/mkl/2024.2/lib`
- clean the build cache
- rerun `cmake -C initial_cache.example.cmake ..`
- rerun `make -j4`

The reference should also record the final validated binary path:

- `/data/home/df_iopcas_ghj/app/FHIaims-master/build/aims.260331.scalapack.mpi.x`

## Top-Level Router Changes

`skills/oh-my-librpa/SKILL.md` should gain an explicit route rule for FHI-aims build/install work.

It should say, in effect:

- if the user asks to install, configure, compile, rebuild, or debug a FHI-aims build itself, route to `skills/fhi-aims-build/`
- do this before falling back to the FHI-aims case workflow skill

This avoids confusing build work with case-level QSGW work.

## FHI-Aims Workflow Skill Changes

`skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md` should remain focused on case routing and execution.

It should gain a short delegation rule:

- if the user’s request is about building or repairing the FHI-aims executable rather than preparing or running a case, hand off to `skills/fhi-aims-build/`

## Style Constraints

The new build skill should be:

- general first
- host-specific only in references
- concise and scan-friendly
- operational rather than tutorial-like
- explicit about evidence gathering before repair

## Success Criteria

The design is successful if, after implementation:

- a future Codex instance can recognize FHI-aims build/install requests as distinct from QSGW case requests
- the new skill teaches a stable root-cause workflow for vendored dependency and compiler-cache failures
- the `df` incident can be reproduced from the reference document without relying on chat history
- the existing `oh-my-librpa` routing stays readable and focused
