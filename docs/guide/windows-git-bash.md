# Windows + Git Bash Guide

Use this guide when installing or updating `oh-my-LibRPA` on Windows.

## Rule Zero

- Do **not** use `WSL`
- Do **not** use plain `cmd.exe`
- Prefer **Git Bash** as the shell

## For Humans

If you are asking an AI to handle setup on Windows, give it this one-line prompt:

```text
On Windows, use Git Bash instead of WSL, and follow: https://raw.githubusercontent.com/AroundPeking/oh-my-LibRPA/main/docs/guide/windows-git-bash.md
```

## For LLM Agents

You are working on Windows.

Requirements:

- Use **Git Bash**, not `WSL`
- Keep the install inside the OpenClaw workspace
- If workspace detection is uncertain, explicitly set:

```bash
OH_MY_LIBRPA_WORKSPACE="$HOME/.openclaw/workspace"
```

## Install

If the repository is already present locally:

```bash
cd ~/code/oh-my-librpa
OH_MY_LIBRPA_WORKSPACE="$HOME/.openclaw/workspace" bash install.sh
```

If you want a remote one-shot install:

```bash
curl -fsSL https://raw.githubusercontent.com/AroundPeking/oh-my-LibRPA/main/install.sh | bash
```

If workspace detection is uncertain, prefer cloning first and then running:

```bash
git clone https://github.com/AroundPeking/oh-my-LibRPA.git
cd oh-my-LibRPA
OH_MY_LIBRPA_WORKSPACE="$HOME/.openclaw/workspace" bash install.sh
```

## Update

After the first install, do not repeat the full install flow unless repairing a broken setup.

Use the in-place updater:

```bash
~/.openclaw/workspace/oh-my-librpa/update.sh
```

If the local updater is missing:

```bash
curl -fsSL https://raw.githubusercontent.com/AroundPeking/oh-my-LibRPA/main/update.sh | bash
```

## What to Report Back

After install or update, report:

1. actual workspace path
2. whether self-test passed
3. whether gateway restart was deferred, skipped, or completed
4. old commit -> new commit if available during update
