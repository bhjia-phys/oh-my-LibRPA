#!/usr/bin/env bash
set -euo pipefail

# oh-my-librpa updater
#
# Optional env vars:
# - OH_MY_LIBRPA_SOURCE: local repo to update from
# - OH_MY_LIBRPA_REPO: fallback git URL when no local source is known
# - OH_MY_LIBRPA_WORKSPACE: override OpenClaw workspace dir
# - OH_MY_LIBRPA_SKIP_RESTART=1: skip gateway restart during the refresh
# - OH_MY_LIBRPA_SKIP_SELF_TEST=1: skip post-update self-test
# - OH_MY_LIBRPA_RESTART_MODE=auto|immediate|defer|skip (default: auto)
# - OH_MY_LIBRPA_UPDATE_BRANCH=<branch>: branch to pull/clone

say() { printf "[oh-my-librpa:update] %s\n" "$*"; }
fail() { printf "[oh-my-librpa:update] ERROR: %s\n" "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  update.sh

Behavior:
  - Reuses the last install source when possible
  - Falls back to cloning the configured repository
  - Refreshes the workspace install by rerunning install.sh in update mode
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

command -v openclaw >/dev/null 2>&1 || fail "openclaw command not found. Install OpenClaw first."
command -v git >/dev/null 2>&1 || fail "git command not found. Update needs git access."

json_find_workspace() {
  local json_file="$1"

  [[ -f "$json_file" ]] || return 0

  if command -v python3 >/dev/null 2>&1; then
    python3 - "$json_file" <<'PY' 2>/dev/null || true
import json, sys
path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as handle:
        data = json.load(handle)
except Exception:
    print("")
    raise SystemExit

def find_workspace(node):
    if isinstance(node, dict):
        value = node.get("workspaceDir")
        if isinstance(value, str) and value:
            return value
        for child in node.values():
            result = find_workspace(child)
            if result:
                return result
    elif isinstance(node, list):
        for child in node:
            result = find_workspace(child)
            if result:
                return result
    return ""

print(find_workspace(data))
PY
    return 0
  fi

  if command -v node >/dev/null 2>&1; then
    node -e '
const fs = require("fs");
const path = process.argv[1];
function findWorkspace(node) {
  if (Array.isArray(node)) {
    for (const child of node) {
      const result = findWorkspace(child);
      if (result) return result;
    }
    return "";
  }
  if (node && typeof node === "object") {
    if (typeof node.workspaceDir === "string" && node.workspaceDir) return node.workspaceDir;
    for (const value of Object.values(node)) {
      const result = findWorkspace(value);
      if (result) return result;
    }
  }
  return "";
}
try {
  const raw = fs.readFileSync(path, "utf8");
  const data = JSON.parse(raw);
  process.stdout.write(findWorkspace(data));
} catch {
  process.stdout.write("");
}
' "$json_file" 2>/dev/null || true
  fi
}

detect_workspace_dir() {
  local workspace="${OH_MY_LIBRPA_WORKSPACE:-}"
  local config_path="${OPENCLAW_CONFIG_PATH:-$HOME/.openclaw/openclaw.json}"

  if [[ -n "$workspace" ]]; then
    printf '%s\n' "$workspace"
    return 0
  fi

  if [[ -n "${OPENCLAW_WORKSPACE:-}" ]]; then
    printf '%s\n' "$OPENCLAW_WORKSPACE"
    return 0
  fi

  if [[ -f "$config_path" ]]; then
    workspace="$(json_find_workspace "$config_path")"
    if [[ -n "$workspace" ]]; then
      printf '%s\n' "$workspace"
      return 0
    fi
  fi

  printf '%s\n' "$HOME/.openclaw/workspace"
}

workspace_dir="$(detect_workspace_dir)"
state_file="$workspace_dir/oh-my-librpa/install-state.env"

installed_source_dir=""
installed_repo_url=""
installed_branch=""
installed_commit=""
if [[ -f "$state_file" ]]; then
  # shellcheck disable=SC1090
  source "$state_file"
  installed_source_dir="${OH_MY_LIBRPA_INSTALL_SOURCE_DIR:-}"
  installed_repo_url="${OH_MY_LIBRPA_INSTALL_REPO_URL:-}"
  installed_branch="${OH_MY_LIBRPA_INSTALL_BRANCH:-}"
  installed_commit="${OH_MY_LIBRPA_INSTALL_COMMIT:-}"
fi

source_dir="${OH_MY_LIBRPA_SOURCE:-}"
if [[ -z "$source_dir" ]]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -d "$script_dir/skills" ]]; then
    source_dir="$script_dir"
  fi
fi
if [[ -z "$source_dir" && -n "$installed_source_dir" && -d "$installed_source_dir/.git" ]]; then
  source_dir="$installed_source_dir"
fi

repo_url="${OH_MY_LIBRPA_REPO:-}"
if [[ -z "$repo_url" && -n "$installed_repo_url" ]]; then
  repo_url="$installed_repo_url"
fi
if [[ -z "$repo_url" ]]; then
  repo_url="https://github.com/AroundPeking/oh-my-LibRPA.git"
fi

update_branch="${OH_MY_LIBRPA_UPDATE_BRANCH:-}"
if [[ -z "$update_branch" && -n "$installed_branch" ]]; then
  update_branch="$installed_branch"
fi

tmp_dir=""
cleanup() {
  if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
    rm -rf "$tmp_dir"
  fi
}
trap cleanup EXIT

if [[ -n "$source_dir" && -d "$source_dir/.git" ]]; then
  say "Updating local repository at $source_dir"
  git -C "$source_dir" fetch --tags origin >/dev/null 2>&1 || fail "failed to fetch updates from origin"

  if [[ -z "$update_branch" ]]; then
    update_branch="$(git -C "$source_dir" branch --show-current 2>/dev/null || true)"
  fi

  if [[ -n "$update_branch" ]]; then
    git -C "$source_dir" pull --ff-only origin "$update_branch" >/dev/null 2>&1 || fail "failed to pull origin/$update_branch"
  else
    git -C "$source_dir" pull --ff-only >/dev/null 2>&1 || fail "failed to pull the current branch"
  fi
else
  tmp_dir="$(mktemp -d)"
  say "Cloning latest oh-my-LibRPA into a temporary directory"
  if [[ -n "$update_branch" ]]; then
    git clone --depth 1 --branch "$update_branch" "$repo_url" "$tmp_dir/repo" >/dev/null 2>&1 || fail "failed to clone $repo_url ($update_branch)"
  else
    git clone --depth 1 "$repo_url" "$tmp_dir/repo" >/dev/null 2>&1 || fail "failed to clone $repo_url"
  fi
  source_dir="$tmp_dir/repo"
fi

[[ -f "$source_dir/install.sh" ]] || fail "install.sh not found in update source: $source_dir"

before_commit="$installed_commit"
after_commit=""
if [[ -d "$source_dir/.git" ]]; then
  after_commit="$(git -C "$source_dir" rev-parse --short HEAD 2>/dev/null || true)"
fi

say "Refreshing workspace install at $workspace_dir"
OH_MY_LIBRPA_SOURCE="$source_dir" \
OH_MY_LIBRPA_WORKSPACE="$workspace_dir" \
OH_MY_LIBRPA_SKIP_RESTART="${OH_MY_LIBRPA_SKIP_RESTART:-0}" \
OH_MY_LIBRPA_SKIP_SELF_TEST="${OH_MY_LIBRPA_SKIP_SELF_TEST:-0}" \
OH_MY_LIBRPA_RESTART_MODE="${OH_MY_LIBRPA_RESTART_MODE:-auto}" \
OH_MY_LIBRPA_INSTALL_MODE=update \
bash "$source_dir/install.sh"

if [[ -n "$before_commit" && -n "$after_commit" ]]; then
  say "Update complete: $before_commit -> $after_commit"
elif [[ -n "$after_commit" ]]; then
  say "Update complete at commit $after_commit"
else
  say "Update complete."
fi
