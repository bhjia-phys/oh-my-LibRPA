# Debug Route

Use this reference after `oh-my-librpa` has already classified the task as debugging.

Locate the failing stage first. Avoid broad blind modifications.

## Diagnosis order

1. Identify the failing stage: `SCF`, `DF/pyatb`, `NSCF`, or `LibRPA`
2. Check whether inputs were mixed from different workflow chains
3. Check stale-output contamination from previous runs
4. Check missing or conflicting threshold parameters
5. Check spin/SOC mismatches and `nbands` / basis-size mismatches

## Fast routing hints

- parse/read errors such as `stod` -> check formatting and stale files first
- abnormal result jumps -> check `nbands` against basis-size conventions first
- missing generated files -> check whether the route expects that stage at all before calling it a failure
- server-only failures -> verify runtime profile, launcher, `python3`, and PATH assumptions

## Output format

Report each diagnosis in this structure:

- `symptom`
- `most_likely_root_cause`
- `minimal_fix_action`
- `validation_action`
- `next_step`

Keep the proposed fix as small as possible. Prefer one targeted repair followed by one cheap validation.