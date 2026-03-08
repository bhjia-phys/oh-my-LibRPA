#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  materialize_gw_template.sh \
    --case-dir <path> \
    --system-type <molecule|solid|2D> \
    [--needs-nscf <auto|true|false>] \
    [--needs-pyatb <auto|true|false>] \
    [--use-shrink-abfs <auto|true|false>]

Behavior:
  - Materializes a GW case directory from the installed template assets
  - Hard-selects the dedicated molecular short-route template when the route is:
      molecule + no NSCF + no pyatb + no shrink
  - Falls back to the generic periodic GW baseline otherwise
  - Writes the selected route to .oh-my-librpa-route.env inside the case dir

Safety:
  - The case directory must be new or empty
  - The script never overwrites a non-empty directory
EOF
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

normalize_bool() {
  local raw="${1:-auto}"
  case "$(lower "$raw")" in
    auto|"") printf '%s\n' auto ;;
    true|t|1|yes|y) printf '%s\n' true ;;
    false|f|0|no|n) printf '%s\n' false ;;
    *) fail "unsupported boolean value: $raw" ;;
  esac
}

require_empty_case_dir() {
  local dir="$1"

  if [[ -e "$dir" && ! -d "$dir" ]]; then
    fail "case path exists and is not a directory: $dir"
  fi

  mkdir -p "$dir"

  if find "$dir" -mindepth 1 -print -quit | grep -q .; then
    fail "case directory must be empty: $dir"
  fi
}

copy_dir_contents() {
  local src="$1"
  local dest="$2"

  mkdir -p "$dest"
  cp -R "$src/." "$dest/"
}

overlay_route_files() {
  local route_dir="$1"
  local case_dir="$2"

  while IFS= read -r src; do
    local rel="${src#$route_dir/}"
    local dest_rel="$rel"
    if [[ "$dest_rel" == *.template ]]; then
      dest_rel="${dest_rel%.template}"
    fi

    local dest="$case_dir/$dest_rel"
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"

    if [[ "$dest" == *.sh ]]; then
      chmod +x "$dest"
    fi
  done < <(find "$route_dir" -type f | sort)
}

case_dir=""
system_type=""
needs_nscf="auto"
needs_pyatb="auto"
use_shrink_abfs="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case-dir) case_dir="$2"; shift 2 ;;
    --system-type) system_type="$2"; shift 2 ;;
    --needs-nscf) needs_nscf="$2"; shift 2 ;;
    --needs-pyatb) needs_pyatb="$2"; shift 2 ;;
    --use-shrink-abfs) use_shrink_abfs="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -n "$case_dir" ]] || fail "missing required argument: --case-dir"
[[ -n "$system_type" ]] || fail "missing required argument: --system-type"

system_type_raw="$system_type"
case "$(lower "$system_type")" in
  molecule) system_type="molecule" ;;
  solid) system_type="solid" ;;
  2d) system_type="2D" ;;
  *) fail "unsupported system type: $system_type_raw" ;;
esac

needs_nscf="$(normalize_bool "$needs_nscf")"
needs_pyatb="$(normalize_bool "$needs_pyatb")"
use_shrink_abfs="$(normalize_bool "$use_shrink_abfs")"

if [[ "$system_type" == "molecule" ]]; then
  [[ "$needs_nscf" == auto ]] && needs_nscf=false
  [[ "$needs_pyatb" == auto ]] && needs_pyatb=false
  [[ "$use_shrink_abfs" == auto ]] && use_shrink_abfs=false
else
  [[ "$needs_nscf" == auto ]] && needs_nscf=true
  [[ "$needs_pyatb" == auto ]] && needs_pyatb=true
  [[ "$use_shrink_abfs" == auto ]] && use_shrink_abfs=true
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
installed_root="$(cd "$script_dir/.." && pwd)"
templates_root="$installed_root/templates/abacus-librpa-gw"
base_template="$templates_root/template"

[[ -d "$base_template" ]] || fail "base GW template directory not found: $base_template"

route_id="gw-generic-periodic-baseline"
reference_template="$base_template"
route_note="Materialized the generic periodic GW baseline."
route_dir=""

if [[ "$system_type" == "molecule" && "$needs_nscf" == false && "$needs_pyatb" == false && "$use_shrink_abfs" == false ]]; then
  route_id="molecule-gw-no-nscf-no-pyatb-no-shrink"
  route_dir="$templates_root/routes/$route_id"
  [[ -d "$route_dir" ]] || fail "dedicated molecular GW route template not found: $route_dir"
  reference_template="$route_dir"
  route_note="Materialized the dedicated molecular GW short route."
fi

require_empty_case_dir "$case_dir"
copy_dir_contents "$base_template" "$case_dir"

if [[ -n "$route_dir" ]]; then
  overlay_route_files "$route_dir" "$case_dir"
fi

if [[ "$route_id" == "molecule-gw-no-nscf-no-pyatb-no-shrink" ]]; then
  rm -f \
    "$case_dir/INPUT_nscf" \
    "$case_dir/KPT_nscf" \
    "$case_dir/get_diel.py" \
    "$case_dir/perform.sh" \
    "$case_dir/preprocess_abacus_for_librpa_band.py"

  if [[ -f "$case_dir/INPUT_scf" ]]; then
    cp "$case_dir/INPUT_scf" "$case_dir/INPUT"
  fi
  if [[ -f "$case_dir/KPT_scf" ]]; then
    cp "$case_dir/KPT_scf" "$case_dir/KPT"
  fi
fi

metadata_file="$case_dir/.oh-my-librpa-route.env"
workflow_helper_bundle='get_diel.py;perform.sh;preprocess_abacus_for_librpa_band.py;run_abacus.sh;output_librpa.py;plot_gw_band_paper.py'
{
  printf 'OH_MY_LIBRPA_MODE=%q\n' 'gw'
  printf 'OH_MY_LIBRPA_ROUTE_ID=%q\n' "$route_id"
  printf 'OH_MY_LIBRPA_SYSTEM_TYPE=%q\n' "$system_type"
  printf 'OH_MY_LIBRPA_NEEDS_NSCF=%q\n' "$needs_nscf"
  printf 'OH_MY_LIBRPA_NEEDS_PYATB=%q\n' "$needs_pyatb"
  printf 'OH_MY_LIBRPA_USE_SHRINK_ABFS=%q\n' "$use_shrink_abfs"
  printf 'OH_MY_LIBRPA_REFERENCE_TEMPLATE=%q\n' "$reference_template"
  printf 'OH_MY_LIBRPA_WORKFLOW_HELPER_BUNDLE=%q\n' "$workflow_helper_bundle"
  printf 'OH_MY_LIBRPA_ROUTE_NOTE=%q\n' "$route_note"
} > "$metadata_file"

cat <<EOF
ROUTE_ID=$route_id
SYSTEM_TYPE=$system_type
NEEDS_NSCF=$needs_nscf
NEEDS_PYATB=$needs_pyatb
USE_SHRINK_ABFS=$use_shrink_abfs
REFERENCE_TEMPLATE=$reference_template
CASE_DIR=$case_dir
NOTE=$route_note
EOF
