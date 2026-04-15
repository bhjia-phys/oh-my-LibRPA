# AITP Integration

This document describes how **oh-my-LibRPA** integrates with the
[AITP Research Protocol](https://github.com/AroundPeking/AITP-Research-Protocol).

---

## What AITP provides

AITP manages the **research lifecycle** — project setup, layer management
(L0–L4), gate enforcement, human interaction checkpoints, and contract
validation. AITP does **not** know anything about ABACUS, LibRPA, or
first-principles physics.

## What oh-my-LibRPA provides

oh-my-LibRPA provides the **domain knowledge** — which codes, which system
types, which operations, which invariants, and which error patterns apply to
ABACUS + LibRPA workflows.

## How they connect

AITP and oh-my-LibRPA communicate through **contract files on disk** inside a
shared project directory. There is no API, no function calls, no IPC.

```
AITP Core                              oh-my-LibRPA
   │                                       │
   │── "What domain is this?" ────────────>│
   │<── domain-manifest.json ──────────────│
   │                                       │
   │── "What derivation is needed?" ──────>│
   │<── equation list + references ────────│
   │                                       │
   │── "Classify this error" ────────────>│
   │<── error classification ─────────────│
```

The domain manifest (`domain-manifest.abacus-librpa.json`) is copied into the
project's `contracts/` directory during Phase P (project setup).

---

## AITP domain contracts

The following AITP contracts are defined for the ABACUS+LibRPA domain. Their
schemas live in the AITP repository under `schemas/`.

| Contract | Purpose |
| --- | --- |
| `computation-workflow` | Full computation chain definition (SCF→DF→NSCF→LibRPA) |
| `development-task` | Software feature development tracking |
| `calculation-debug` | Failure diagnosis and fix record |
| `compute-resource` | Compute server specification |
| `benchmark-report` | Benchmark results and verdict |

### Computation workflow stages

| Stage | Description | Key validation |
| --- | --- | --- |
| `scf` | Self-consistent field | `convergence_reached` |
| `df` | Density functional (Coulomb matrices) | `coulomb_matrices_exist` |
| `nscf` | Non-self-consistent field (GW only) | `band_structure_readable` |
| `librpa` | LibRPA post-processing | `gw_band_output_exists` or `rpa_converged` |
| `postprocess` | pyatb or custom post-processing | varies |

### Domain invariants

| Invariant | Description |
| --- | --- |
| `shrink_consistency` | ABFS_ORBITAL files match `use_shrink_abfs` in `librpa.in` |
| `same_libri` | ABACUS and LibRPA compiled against same LibRI version |
| `keyword_compat` | No deprecated ABACUS keywords in INPUT |
| `smoke_first` | Minimal test passed before full calculation |
| `toolchain_consistency` | Build and runtime environments match |

---

## Feature development playbook

When developing new features for ABACUS/LibRPA through AITP, the
9-phase playbook applies:

```
Phase P: Project Setup           →  Folder creation + AITP bootstrap
Phase 0: Feature Scoping         →  Bounded physics question
Phase 1: Theory & Derivation     →  LaTeX derivation, human-approved
         *** Gate G0 ***
Phase 2: Development Planning     →  development-task contract
Phase 3: Implementation           →  Code follows derivation
Phase 4: Build & Smoke Test       →  Compile, minimal test
Phase 5: Benchmark Campaign       →  Multiple systems, convergence
Phase 6: Debug Loop               →  Diagnose failures
Phase 7: Production Readiness     →  Merge + L2 promotion
```

**Core discipline**: derivation before code. Every physics function must
reference its equation from the approved LaTeX derivation.

See the full playbook at:
[AITP FEATURE_DEVELOPMENT_PLAYBOOK.md](https://github.com/AroundPeking/AITP-Research-Protocol/blob/main/research/knowledge-hub/FEATURE_DEVELOPMENT_PLAYBOOK.md)

---

## oh-my-LibRPA knowledge → AITP contract mapping

| oh-my-LibRPA concept | AITP contract field |
| --- | --- |
| System type classification (molecule/solid/2D) | `computation-workflow.system_type` |
| Input file consistency checks | `computation-workflow.basis_integrity` + invariants |
| Remote vs local execution routing | `computation-workflow.compute` + `compute-resource` |
| Workflow chaining (SCF→DF→NSCF→LibRPA) | `computation-workflow.stages` |
| Debugging expertise (stod errors, convergence) | `calculation-debug.error_classification` |
| Build configuration knowledge | `development-task.build_config` |
| Smoke test before expensive runs | `smoke_first` invariant |
| Server-specific toolchain paths | `compute-resource` contract |
| Route-aware templates | AITP `on_smoke_system` / `on_benchmark_systems` hooks |
| Rule cards (scene → symptom → fix) | AITP `on_error_classify` hook |

---

## Quick reference

- **AITP repository**: <https://github.com/AroundPeking/AITP-Research-Protocol>
- **Domain protocol**: [FIRST_PRINCIPLES_LANE_PROTOCOL.md](https://github.com/AroundPeking/AITP-Research-Protocol/blob/main/research/knowledge-hub/FIRST_PRINCIPLES_LANE_PROTOCOL.md)
- **Domain skill interface**: [DOMAIN_SKILL_INTERFACE_PROTOCOL.md](https://github.com/AroundPeking/AITP-Research-Protocol/blob/main/research/knowledge-hub/DOMAIN_SKILL_INTERFACE_PROTOCOL.md)
- **Feature development playbook**: [FEATURE_DEVELOPMENT_PLAYBOOK.md](https://github.com/AroundPeking/AITP-Research-Protocol/blob/main/research/knowledge-hub/FEATURE_DEVELOPMENT_PLAYBOOK.md)
- **Project structure convention**: [PROJECT_STRUCTURE_CONVENTION.md](https://github.com/AroundPeking/AITP-Research-Protocol/blob/main/research/knowledge-hub/PROJECT_STRUCTURE_CONVENTION.md)
