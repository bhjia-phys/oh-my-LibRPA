# Run Logging

Every compute or debug task should produce two outputs:

1. a short user-facing progress update after each stage
2. two durable Markdown run logs saved outside the repository:
   - one in the active run directory as `run-report.md`
   - one archived under `~/.openclaw/workspace/librpa/oh-my-librpa/`

The repository should keep only the logging rules and templates. Runtime logs must not be written into the `oh-my-LibRPA` git tree.

## File Naming

Use one report per task in both locations:

- `<run_dir>/run-report.md`
- `~/.openclaw/workspace/librpa/oh-my-librpa/<timestamp>-gw.md`
- `~/.openclaw/workspace/librpa/oh-my-librpa/<timestamp>-rpa.md`
- `~/.openclaw/workspace/librpa/oh-my-librpa/<timestamp>-debug.md`

Example:

- `/path/to/calc/run-report.md`
- `~/.openclaw/workspace/librpa/oh-my-librpa/2026-03-06-2235-gw.md`

## Minimum Required Content

Each Markdown run log should record:

- task type
- compute location
- working directory
- input file bundle
- key parameters
- per-stage timestamps
- per-stage status: `success`, `running`, or `failed`
- key output files
- final result
- next suggested action

## Hook + Script Pattern

Use hook timing and a shared reporting script together:

1. verify the stage result first
2. call `scripts/report_stage.sh`
3. send the script stdout to the user as the stage summary

For a full GW execution path, use `scripts/run_gw_workflow.sh` as the execution-layer runner. It executes each stage, verifies the outputs immediately, and then calls `report_stage.sh`.

This keeps orchestration and deterministic reporting separate.

The script should run on the OpenClaw host, not inside the remote compute job.

## User-Facing Update Format

After each stage update, send the user a short summary with exactly these three parts:

- `what was done`
- `what was observed`
- `what is next`

Do not dump the entire Markdown file into chat unless the user explicitly asks for it.

## Recommended Stage Names

For GW:

- `scf`
- `pyatb`
- `nscf`
- `preprocess`
- `librpa`

For RPA:

- `scf`
- `librpa`

For debug:

- `intake`
- `stage-identification`
- `root-cause`
- `repair-plan`
- `validation`

## Status Convention

Use the same simple convention everywhere:

- `success`: stage reached its completion markers
- `running`: stage has not finished but its output is still progressing
- `failed`: stage is neither complete nor still progressing

## Example Commands

Single stage reporting:

```bash
scripts/report_stage.sh \
  --run-id 2026-03-06-2307 \
  --mode gw \
  --stage scf \
  --status success \
  --run-dir /path/to/calc \
  --task-label Bi2Se3-dojov4-fr \
  --compute-location server \
  --system-type solid \
  --task g0w0_band \
  --nfreq 16 \
  --use-soc 1 \
  --nbands 512 \
  --kpt "8 8 8" \
  --kpt-nscf "user-provided" \
  --what-done "Validated ABACUS SCF outputs." \
  --what-observed "running_scf.log contains Finish Time and the charge-density restart file exists." \
  --next-step "Run pyatb."
```

Full GW runner:

```bash
scripts/run_gw_workflow.sh \
  --run-id 2026-03-06-2307 \
  --run-dir /path/to/calc \
  --compute-location server \
  --ssh-target ks_ghj_3 \
  --task-label Bi2Se3-dojov4-fr \
  --system-type solid \
  --task g0w0_band \
  --nfreq 16 \
  --use-soc 1 \
  --nbands 512 \
  --kpt "8 8 8" \
  --kpt-nscf "user-provided" \
  --scf-cmd "bash run_scf.sh" \
  --pyatb-cmd "python3 get_diel.py" \
  --nscf-cmd "bash run_nscf.sh" \
  --preprocess-cmd "python3 preprocess_abacus_for_librpa_band.py" \
  --librpa-cmd "mpirun -np 16 librpa"
```
