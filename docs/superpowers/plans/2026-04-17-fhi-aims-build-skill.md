# FHI-Aims Build Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable `fhi-aims-build` skill, document the validated `df` recovery path, and wire the new skill into `oh-my-librpa` routing.

**Architecture:** Create one new skill tree with a compact main `SKILL.md` and a `df`-specific reference document, then make two minimal routing edits in the existing top-level and FHI-aims workflow skills. Verification is content-based: prove the old route was absent, then prove the new trigger and delegation text exists after the change.

**Tech Stack:** Markdown skill files, local repo routing docs, `rg`, `sed`

---

### Task 1: Capture the baseline failure state

**Files:**
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`

- [ ] **Step 1: Prove the top-level router does not yet mention FHI-aims build/install routing**

Run:

```bash
rg -n "install FHI-aims|compile FHI-aims|rebuild FHI-aims|fhi-aims-build" /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md
```

Expected: no matches.

- [ ] **Step 2: Prove the FHI-aims workflow skill does not yet delegate build requests**

Run:

```bash
rg -n "build|compile|rebuild|fhi-aims-build" /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md
```

Expected: no routing/delegation language for FHI-aims executable build work.

### Task 2: Add the new reusable skill

**Files:**
- Create: `/Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/SKILL.md`
- Create: `/Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/references/df-fhi-aims-build.md`

- [ ] **Step 1: Write the main skill**

The new `SKILL.md` must teach:

- how to distinguish a real git clone from a copied source snapshot
- how to diagnose missing vendored ELSI content
- how to compare MPI wrappers against cache flags
- how to detect stale compiler names and library paths
- how to apply the smallest repair before rerunning `cmake`

- [ ] **Step 2: Write the `df` reference**

The `df` reference must include:

- the evidence chain from the failed build
- the exact repaired cache choices
- the exact ELSI population step
- the final successful binary path

- [ ] **Step 3: Keep the skill general-first**

Verify that the main `SKILL.md` stays host-agnostic and that `df`-specific details live in the reference file rather than in the main trigger description.

### Task 3: Update routing

**Files:**
- Modify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md`
- Modify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`

- [ ] **Step 1: Update the top-level router**

Add a rule that routes FHI-aims install/configure/compile/rebuild/debug-build requests to `skills/fhi-aims-build/`.

- [ ] **Step 2: Update the FHI-aims workflow skill**

Add a short delegation rule stating that executable build/repair work belongs in `skills/fhi-aims-build/`, while the current skill remains focused on case preparation and execution.

### Task 4: Verify the new skill and routing text

**Files:**
- Verify: `/Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/SKILL.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/references/df-fhi-aims-build.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md`
- Verify: `/Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md`

- [ ] **Step 1: Prove the new trigger is present**

Run:

```bash
rg -n "fhi-aims-build|install FHI-aims|compile FHI-aims|rebuild FHI-aims" /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md /Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/SKILL.md
```

Expected: matches in all three files.

- [ ] **Step 2: Prove the `df` example records the validated fix**

Run:

```bash
rg -n "elsi_interface|mpiifort|icx|icpx|/data/app/intel/oneapi-2024.2/mkl/2024.2/lib|aims.260331.scalapack.mpi.x" /Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/references/df-fhi-aims-build.md
```

Expected: all recovery anchors are present.

- [ ] **Step 3: Commit**

```bash
git add /Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/SKILL.md /Users/ghj/code/oh-my-librpa/skills/fhi-aims-build/references/df-fhi-aims-build.md /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa/SKILL.md /Users/ghj/code/oh-my-librpa/skills/oh-my-librpa-fhi-aims-qsgw/SKILL.md /Users/ghj/code/oh-my-librpa/docs/superpowers/plans/2026-04-17-fhi-aims-build-skill.md
git commit -m "skills: add fhi-aims build workflow"
```
