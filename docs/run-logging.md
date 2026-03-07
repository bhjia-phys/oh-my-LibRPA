# Run Logging

`oh-my-LibRPA` writes two Markdown logs for each run:

1. one in the active run directory as `run-report.md`
2. one archived under the active platform root as `librpa/oh-my-librpa/<timestamp>-<mode>.md`

## Default Archive Roots

The default archive root follows the installed platform root automatically:

- `OpenClaw`: `.openclaw/workspace/librpa/oh-my-librpa/`
- `OpenCode`: `.opencode/librpa/oh-my-librpa/`
- `Codex`: `.codex-home/librpa/oh-my-librpa/`

You can still override it explicitly with `OH_MY_LIBRPA_ARCHIVE_ROOT` or `--archive-root`.

## Example Paths

Typical archived reports:

- `.openclaw/workspace/librpa/oh-my-librpa/2026-03-06-2235-gw.md`
- `.opencode/librpa/oh-my-librpa/2026-03-06-2235-rpa.md`
- `.codex-home/librpa/oh-my-librpa/2026-03-06-2235-debug.md`

## Why Two Logs

The run-local copy keeps the report next to the working files.

The archived copy gives the agent a stable place to summarize progress and resume later without depending on the original run directory.

## Script Surface

Use `scripts/report_stage.sh` to append verified stage updates.

Key behavior:

- creates `run-report.md` when missing
- creates the archived copy when missing
- appends a stage block after each verified stage
- prints a short chat-ready summary to stdout

## Recommendation

Keep the default platform-relative archive root unless you already have a stronger project convention.
