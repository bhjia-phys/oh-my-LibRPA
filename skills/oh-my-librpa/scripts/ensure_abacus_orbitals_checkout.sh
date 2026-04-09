#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ensure_abacus_orbitals_checkout.sh <target_dir> [repo_url]

Behavior:
  - Clones the official ABACUS-orbitals repository into <target_dir> when it is missing
  - Reuses an existing git checkout without modifying it
EOF
}

target_dir="${1:-}"
repo_url="${2:-https://github.com/abacusmodeling/ABACUS-orbitals}"

if [[ -z "$target_dir" || "$target_dir" == "-h" || "$target_dir" == "--help" ]]; then
  usage
  [[ -z "$target_dir" ]] && exit 2 || exit 0
fi

if [[ -d "$target_dir/.git" ]]; then
  echo "EXISTS: $target_dir"
  exit 0
fi

if [[ -e "$target_dir" && ! -d "$target_dir/.git" ]]; then
  echo "Refusing to overwrite non-git path: $target_dir" >&2
  exit 1
fi

mkdir -p "$(dirname "$target_dir")"
git clone --depth 1 "$repo_url" "$target_dir"
echo "CLONED: $target_dir"
