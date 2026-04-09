# Debug Route

Use this reference after `oh-my-librpa` has already classified the task as debugging.

Locate the failing stage first. Avoid broad blind modifications.

## Diagnosis order

1. Identify the failing stage: `SCF`, `DF/pyatb`, `NSCF`, or `LibRPA`
2. Check whether inputs were mixed from different workflow chains
3. Check stale-output contamination from previous runs
4. Check deprecated or renamed ABACUS input keywords copied from older cases
5. Check missing or conflicting threshold parameters
6. Check spin/SOC mismatches and `nbands` / basis-size mismatches

## Fast routing hints

- parse/read errors such as `stod` -> check formatting and stale files first
- `ModuleNotFoundError: No module named 'output_librpa'` -> cloned periodic GW case is missing part of the helper quartet; restore `output_librpa.py` together with `perform.sh` / `get_diel.py`
- `THE PARAMETER NAME ... IS INCORRECT!` -> run the compatibility audit first; suspect stale keys such as `exx_use_ewald`, `cs_inv_thr`, `exx_spencer_type`, or `out_bandgap`
- abnormal result jumps -> check `nbands` against basis-size conventions first
- absurd GW shifts or huge negative gaps -> check shrink synchronization first; this is a workflow invariant on every host, and a shrink-generated ABACUS bundle must not be reused with `librpa.in: use_shrink_abfs = f`
- missing generated files -> check whether the route expects that stage at all before calling it a failure
- server-only failures -> verify runtime profile, launcher, `python3`, and PATH assumptions
- empty or nearly empty Slurm logs on `df` -> suspect batch bootstrap failure (`.bashrc`, conda hooks, `setvars.sh`) before suspecting ABACUS
- symmetry-on `coulomb_*` q-count mismatch -> for `ABACUS` with `rpa=1` and `symmetry=1`, `coulomb_mat_*` and `coulomb_cut_*` may be written on IBZ q points only; use `OUT.ABACUS/KPT.info` to map IBZ representatives to full-q indices before comparing to `symmetry=-1`

## Output format

Report each diagnosis in this structure:

- `symptom`
- `most_likely_root_cause`
- `minimal_fix_action`
- `validation_action`
- `next_step`

Keep the proposed fix as small as possible. Prefer one targeted repair followed by one cheap validation.
