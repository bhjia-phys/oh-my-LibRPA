#!/usr/bin/env bash
set -euo pipefail

# oh-my-librpa installer (chat-first)
#
# Optional env vars:
# - OH_MY_LIBRPA_SOURCE: local source dir containing this repo
# - OH_MY_LIBRPA_REPO: git URL used when source dir is not present
# - OH_MY_LIBRPA_WORKSPACE: override OpenClaw workspace dir
# - OH_MY_LIBRPA_SKIP_RESTART=1: skip gateway restart
# - OH_MY_LIBRPA_SKIP_SELF_TEST=1: skip post-install self-test
# - OH_MY_LIBRPA_RESTART_MODE=auto|immediate|defer|skip (default: auto)

say() { printf "[oh-my-librpa] %s\n" "$*"; }
fail() { printf "[oh-my-librpa] ERROR: %s\n" "$*" >&2; exit 1; }

command -v openclaw >/dev/null 2>&1 || fail "openclaw command not found. Install OpenClaw first."

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

detect_copy_tool() {
  if command -v rsync >/dev/null 2>&1 && rsync --version >/dev/null 2>&1; then
    printf '%s\n' 'rsync'
    return 0
  fi

  if command -v cp >/dev/null 2>&1; then
    printf '%s\n' 'cp'
    return 0
  fi

  fail "neither rsync nor cp is available for installation copy steps"
}

copy_dir_contents() {
  local src="$1"
  local dest="$2"

  mkdir -p "$dest"

  if [[ "$copy_tool" == "rsync" ]]; then
    rsync -a "$src/" "$dest/"
    return 0
  fi

  cp -R "$src/." "$dest/"
}

source_dir="${OH_MY_LIBRPA_SOURCE:-}"
if [[ -z "$source_dir" ]]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -d "$script_dir/skills" ]]; then
    source_dir="$script_dir"
  fi
fi

tmp_dir=""
cleanup() {
  if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
    rm -rf "$tmp_dir"
  fi
}
trap cleanup EXIT

if [[ -z "$source_dir" ]]; then
  repo_url="${OH_MY_LIBRPA_REPO:-https://github.com/AroundPeking/oh-my-LibRPA.git}"
  tmp_dir="$(mktemp -d)"
  say "Cloning $repo_url"
  git clone --depth 1 "$repo_url" "$tmp_dir/repo" >/dev/null 2>&1 || fail "failed to clone $repo_url"
  source_dir="$tmp_dir/repo"
fi

[[ -d "$source_dir/skills" ]] || fail "skills directory not found in source: $source_dir"

workspace_dir="$(detect_workspace_dir)"
[[ -n "$workspace_dir" ]] || fail "could not determine OpenClaw workspace"

copy_tool="$(detect_copy_tool)"
if [[ "$copy_tool" == "cp" ]]; then
  say "rsync not available; using cp -R for installation copy steps"
fi

skills_target="$workspace_dir/skills"
assets_target="$workspace_dir/oh-my-librpa"

say "Installing skills into $skills_target"
copy_dir_contents "$source_dir/skills" "$skills_target"

say "Installing rulebook assets into $assets_target"
mkdir -p "$assets_target"
for dir in rules templates references docs scripts registry examples; do
  if [[ -d "$source_dir/$dir" ]]; then
    copy_dir_contents "$source_dir/$dir" "$assets_target/$dir"
  fi
done

find "$assets_target/scripts" -type f -name '*.sh' -exec chmod +x {} +

if [[ "${OH_MY_LIBRPA_SKIP_SELF_TEST:-0}" != "1" ]]; then
  say "Running post-install self-test"
  "$assets_target/scripts/self_test.sh" --workspace "$workspace_dir" --installed-root "$assets_target" || fail "post-install self-test failed"
fi

restart_mode="${OH_MY_LIBRPA_RESTART_MODE:-auto}"
if [[ "${OH_MY_LIBRPA_SKIP_RESTART:-0}" == "1" ]]; then
  restart_mode="skip"
fi

case "$restart_mode" in
  auto)
    if [[ "${OPENCLAW_SERVICE_KIND:-}" == "gateway" || "${OPENCLAW_SHELL:-}" == "exec" ]]; then
      restart_mode="defer"
    else
      restart_mode="immediate"
    fi
    ;;
  immediate|defer|skip)
    ;;
  *)
    fail "unsupported OH_MY_LIBRPA_RESTART_MODE: $restart_mode"
    ;;
esac

if [[ "$restart_mode" == "immediate" ]]; then
  say "Restarting OpenClaw gateway"
  if ! openclaw gateway restart >/dev/null 2>&1; then
    say "Gateway restart failed; trying start"
    openclaw gateway start >/dev/null 2>&1 || fail "gateway restart/start failed"
  fi
elif [[ "$restart_mode" == "defer" ]]; then
  say "Deferring gateway restart to avoid interrupting the current OpenClaw conversation."
  say "Run 'openclaw gateway restart' after this chat to activate the new install."
else
  say "Skipping gateway restart."
fi

say "Install complete."
say "Now just chat naturally, e.g.:"
say "  Help me run GW for GaAs with a conservative setup first."
