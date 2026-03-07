#!/usr/bin/env bash
set -euo pipefail

# oh-my-librpa installer (chat-first)
#
# Optional env vars:
# - OH_MY_LIBRPA_SOURCE: local source dir containing this repo
# - OH_MY_LIBRPA_REPO: git URL used when source dir is not present
# - OH_MY_LIBRPA_TARGET: openclaw|opencode|codex|all (default: all)
# - OH_MY_LIBRPA_LAYOUT: project|user (default: project)
# - OH_MY_LIBRPA_INSTALL_MODE: auto|copy|link (default: auto)
# - OH_MY_LIBRPA_PROJECT_ROOT: project root for project-local installs
# - OH_MY_LIBRPA_OPENCLAW_WORKSPACE: override OpenClaw workspace dir
# - OH_MY_LIBRPA_OPENCODE_HOME: override OpenCode home dir
# - OH_MY_LIBRPA_CODEX_HOME: override Codex home dir
# - OH_MY_LIBRPA_SKIP_RESTART=1: skip OpenClaw gateway restart
# - OH_MY_LIBRPA_SKIP_SELF_TEST=1: skip post-install self-test
# - OH_MY_LIBRPA_RESTART_MODE=auto|immediate|defer|skip (default: auto)

say() { printf "[oh-my-librpa] %s\n" "$*"; }
fail() { printf "[oh-my-librpa] ERROR: %s\n" "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  bash install.sh \
    [--target <openclaw|opencode|codex|all>] \
    [--layout <project|user>] \
    [--mode <auto|copy|link>] \
    [--project-root <path>] \
    [--source <path>] \
    [--restart-mode <auto|immediate|defer|skip>] \
    [--skip-self-test] \
    [--skip-restart]

Defaults:
  --target all
  --layout project
  --mode auto

Project layout targets:
  - OpenClaw -> <project>/.openclaw/workspace/
  - OpenCode -> <project>/.opencode/
  - Codex    -> <project>/.codex-home/

Notes:
  - Project layout prefers symlink installs when the source repository is local.
  - User layout preserves the previous OpenClaw-style install and also supports
    user-level OpenCode/Codex homes.
  - Core project skills are sourced only from `skills-core/`.
EOF
}

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

detect_openclaw_workspace_dir() {
  local workspace="${OH_MY_LIBRPA_OPENCLAW_WORKSPACE:-${OH_MY_LIBRPA_WORKSPACE:-}}"
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

replace_with_link() {
  local src="$1"
  local dest="$2"

  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  ln -s "$src" "$dest"
}

replace_with_copy() {
  local src="$1"
  local dest="$2"

  rm -rf "$dest"
  mkdir -p "$dest"
  copy_dir_contents "$src" "$dest"
}

install_component() {
  local src="$1"
  local dest="$2"

  if [[ "$install_mode" == "link" ]]; then
    replace_with_link "$src" "$dest"
  else
    replace_with_copy "$src" "$dest"
  fi
}

contains_target() {
  local needle="$1"
  local item
  for item in "${targets[@]}"; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

parse_targets() {
  local raw="$1"
  local normalized
  normalized="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"

  if [[ "$normalized" == "all" ]]; then
    targets=(openclaw opencode codex)
    return 0
  fi

  IFS=',' read -r -a targets <<< "$normalized"
  if [[ "${#targets[@]}" -eq 0 ]]; then
    fail "no install targets resolved from: $raw"
  fi

  local item
  for item in "${targets[@]}"; do
    case "$item" in
      openclaw|opencode|codex) ;;
      *) fail "unsupported target: $item" ;;
    esac
  done
}

resolve_target_root() {
  local target="$1"
  case "$target" in
    openclaw)
      if [[ "$layout" == "project" ]]; then
        printf '%s\n' "${OH_MY_LIBRPA_OPENCLAW_WORKSPACE:-${OH_MY_LIBRPA_WORKSPACE:-$project_root/.openclaw/workspace}}"
      else
        detect_openclaw_workspace_dir
      fi
      ;;
    opencode)
      if [[ "$layout" == "project" ]]; then
        printf '%s\n' "${OH_MY_LIBRPA_OPENCODE_HOME:-$project_root/.opencode}"
      else
        printf '%s\n' "${OH_MY_LIBRPA_OPENCODE_HOME:-${OPENCODE_HOME:-$HOME/.opencode}}"
      fi
      ;;
    codex)
      if [[ "$layout" == "project" ]]; then
        printf '%s\n' "${OH_MY_LIBRPA_CODEX_HOME:-$project_root/.codex-home}"
      else
        printf '%s\n' "${OH_MY_LIBRPA_CODEX_HOME:-${CODEX_HOME:-$HOME/.codex}}"
      fi
      ;;
    *)
      fail "unsupported target for root resolution: $target"
      ;;
  esac
}

print_target_hint() {
  local target="$1"
  local root="$2"
  case "$target" in
    openclaw)
      say "[openclaw] files ready under $root"
      if [[ "$layout" == "project" ]]; then
        say "[openclaw] launch with OPENCLAW_WORKSPACE=$root"
      fi
      ;;
    opencode)
      say "[opencode] files ready under $root"
      say "[opencode] repo-local skills are under $root/skills"
      ;;
    codex)
      say "[codex] files ready under $root"
      say "[codex] launch with CODEX_HOME=$root"
      ;;
  esac
}

install_target() {
  local target="$1"
  local root skills_target assets_target dir skill_dir

  root="$(resolve_target_root "$target")"
  [[ -n "$root" ]] || fail "could not determine install root for $target"

  skills_target="$root/skills"
  assets_target="$root/oh-my-librpa"

  say "Installing [$target] skills into $skills_target"
  mkdir -p "$skills_target"
  for skill_dir in "$source_dir"/skills-core/*; do
    [[ -d "$skill_dir" ]] || continue
    install_component "$skill_dir" "$skills_target/$(basename "$skill_dir")"
  done

  say "Installing [$target] shared assets into $assets_target"
  mkdir -p "$assets_target"
  for dir in rules templates references docs scripts registry examples data; do
    if [[ -d "$source_dir/$dir" ]]; then
      install_component "$source_dir/$dir" "$assets_target/$dir"
    fi
  done

  if [[ -d "$assets_target/scripts" ]]; then
    find "$assets_target/scripts" -type f -name '*.sh' -exec chmod +x {} +
  fi

  if [[ "${OH_MY_LIBRPA_SKIP_SELF_TEST:-0}" != "1" ]]; then
    say "Running [$target] post-install self-test"
    "$assets_target/scripts/self_test.sh" \
      --target "$target" \
      --skills-root "$skills_target" \
      --installed-root "$assets_target" || fail "post-install self-test failed for $target"
  fi

  installed_roots+=("$target:$root")
}

source_dir="${OH_MY_LIBRPA_SOURCE:-}"
script_dir=""
source_is_ephemeral=0

if [[ -z "$source_dir" ]]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -d "$script_dir/skills-core" ]]; then
    source_dir="$script_dir"
  fi
fi

target_raw="${OH_MY_LIBRPA_TARGET:-all}"
layout="${OH_MY_LIBRPA_LAYOUT:-project}"
install_mode="${OH_MY_LIBRPA_INSTALL_MODE:-auto}"
project_root="${OH_MY_LIBRPA_PROJECT_ROOT:-}"
restart_mode="${OH_MY_LIBRPA_RESTART_MODE:-auto}"

tmp_dir=""
cleanup() {
  if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
    rm -rf "$tmp_dir"
  fi
}
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) target_raw="$2"; shift 2 ;;
    --layout) layout="$2"; shift 2 ;;
    --mode) install_mode="$2"; shift 2 ;;
    --project-root) project_root="$2"; shift 2 ;;
    --source) source_dir="$2"; shift 2 ;;
    --restart-mode) restart_mode="$2"; shift 2 ;;
    --skip-self-test) export OH_MY_LIBRPA_SKIP_SELF_TEST=1; shift ;;
    --skip-restart) export OH_MY_LIBRPA_SKIP_RESTART=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$layout" in
  project|user) ;;
  *) fail "unsupported layout: $layout" ;;
esac

case "$install_mode" in
  auto|copy|link) ;;
  *) fail "unsupported install mode: $install_mode" ;;
esac

if [[ -z "$source_dir" ]]; then
  repo_url="${OH_MY_LIBRPA_REPO:-https://github.com/bhjia-phys/oh-my-LibRPA.git}"
  tmp_dir="$(mktemp -d)"
  say "Cloning $repo_url"
  git clone --depth 1 "$repo_url" "$tmp_dir/repo" >/dev/null 2>&1 || fail "failed to clone $repo_url"
  source_dir="$tmp_dir/repo"
  source_is_ephemeral=1
fi

[[ -d "$source_dir/skills-core" ]] || fail "skills-core directory not found in source: $source_dir"

if [[ -d "$source_dir/scripts" ]]; then
  find "$source_dir/scripts" -type f -name '*.sh' -exec chmod +x {} +
fi

if [[ -z "$project_root" ]]; then
  if [[ "$layout" == "project" ]]; then
    if [[ "$source_is_ephemeral" -eq 1 ]]; then
      project_root="$(pwd)"
    else
      project_root="$source_dir"
    fi
  else
    project_root="$(pwd)"
  fi
fi
project_root="$(cd "$project_root" && pwd)"

parse_targets "$target_raw"

if [[ "$install_mode" == "auto" ]]; then
  if [[ "$layout" == "project" && "$source_is_ephemeral" -eq 0 ]]; then
    install_mode="link"
  else
    install_mode="copy"
  fi
fi

if [[ "$install_mode" == "copy" ]]; then
  copy_tool="$(detect_copy_tool)"
  if [[ "$copy_tool" == "cp" ]]; then
    say "rsync not available; using cp -R for installation copy steps"
  fi
fi

installed_roots=()
for target in "${targets[@]}"; do
  install_target "$target"
done

if [[ "${OH_MY_LIBRPA_SKIP_RESTART:-0}" == "1" ]]; then
  restart_mode="skip"
fi

case "$restart_mode" in
  auto)
    if contains_target openclaw && [[ "$layout" == "user" ]]; then
      if [[ "${OPENCLAW_SERVICE_KIND:-}" == "gateway" || "${OPENCLAW_SHELL:-}" == "exec" ]]; then
        restart_mode="defer"
      else
        restart_mode="immediate"
      fi
    else
      restart_mode="skip"
    fi
    ;;
  immediate|defer|skip) ;;
  *) fail "unsupported OH_MY_LIBRPA_RESTART_MODE: $restart_mode" ;;
esac

if contains_target openclaw && [[ "$layout" == "user" ]]; then
  if [[ "$restart_mode" == "immediate" ]]; then
    if command -v openclaw >/dev/null 2>&1; then
      say "Restarting OpenClaw gateway"
      if ! openclaw gateway restart >/dev/null 2>&1; then
        say "Gateway restart failed; trying start"
        openclaw gateway start >/dev/null 2>&1 || fail "gateway restart/start failed"
      fi
    else
      say "OpenClaw CLI not found; skipping gateway restart."
    fi
  elif [[ "$restart_mode" == "defer" ]]; then
    say "Deferring gateway restart to avoid interrupting the current OpenClaw conversation."
    say "Run 'openclaw gateway restart' after this chat to activate the new install."
  else
    say "Skipping OpenClaw gateway restart."
  fi
fi

say "Install complete."
say "Installed targets: ${target_raw}"
say "Layout: $layout"
say "Mode: $install_mode"

for item in "${installed_roots[@]}"; do
  target="${item%%:*}"
  root="${item#*:}"
  print_target_hint "$target" "$root"
done

say "Now just chat naturally, e.g.:"
say "  Help me run GW for GaAs with a conservative setup first."
