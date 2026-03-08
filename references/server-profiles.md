# Server Profiles

Use host profiles to make remote batch jobs deterministic.

## Files

- Registry entries live under `registry/host-profiles/*.env`
- Materialized runtime blocks live inside the case directory:
  - `env.sh`
  - `.oh-my-librpa-host-profile.env`
  - optional `probe_batch.sh`

## Why

Remote batch jobs must not assume that:

- `~/.bashrc` is loaded
- `python == python3`
- `python3` is in `PATH`
- `srun` is the correct launcher just because Slurm exists

## Expected profile fields

- `OH_MY_LIBRPA_SERVER_NAME`
- `OH_MY_LIBRPA_PYTHON3_EXEC`
- `OH_MY_LIBRPA_ABACUS_EXEC`
- `OH_MY_LIBRPA_LIBRPA_EXEC`
- `OH_MY_LIBRPA_MPI_LAUNCHER`
- `OH_MY_LIBRPA_MPI_LAUNCHER_CMD`
- `OH_MY_LIBRPA_ENV_SOURCES`
- `OH_MY_LIBRPA_MODULE_LOADS`
- `OH_MY_LIBRPA_PATH_PREPEND`
- `OH_MY_LIBRPA_LD_LIBRARY_PATH_PREPEND`

## Workflow

1. Select a profile or ask the user for one.
2. Run `scripts/materialize_server_profile.sh --case-dir <case_dir> --profile <name-or-path>`.
3. If batch behavior is uncertain, run `scripts/materialize_batch_probe.sh --case-dir <case_dir> --profile <name-or-path>`.
4. Source `env.sh` from `run_abacus.sh` and helper scripts.
5. Record the resolved runtime config in the run directory.
