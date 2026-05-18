#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  check_slurm_resources.sh <run_script> \
    [--target-partition <name>] \
    [--target-nodes <count>] \
    [--expected-ntasks-per-node <count>] \
    [--node-cores <count>] \
    [--node-memory-mb <MB>]

Behavior:
  - Checks Slurm directives in a run script against resource facts from the target server/partition.
  - The caller must provide node facts from the current server, for example from `sinfo` or `scontrol show node`.
  - When `--expected-ntasks-per-node 1` and `--node-cores` are provided, `--cpus-per-task` must use the full node core count.
  - When `--node-memory-mb` is provided, `--mem` must request the full per-node memory in MB.

Example:
  # If df partition 9242 currently reports 96 cores and 380000 MB per node:
  check_slurm_resources.sh run_abacus.sh --target-partition 9242 --target-nodes 4 \
    --expected-ntasks-per-node 1 --node-cores 96 --node-memory-mb 380000
EOF
}

note_pass() {
  echo "PASS: $*"
  pass_count=$((pass_count + 1))
}

note_warn() {
  echo "WARN: $*"
  warn_count=$((warn_count + 1))
}

note_fail() {
  echo "FAIL: $*" >&2
  fail_count=$((fail_count + 1))
}

trim() {
  printf '%s' "$1" | awk '{ gsub(/^[ \t]+|[ \t]+$/, "", $0); print }'
}

normalize_mem_mb() {
  local raw="$1"
  raw="$(trim "$raw")"
  raw="${raw%[cCnN]}"
  case "$raw" in
    *[Gg])
      awk -v value="${raw%[Gg]}" 'BEGIN { printf "%.0f\n", value * 1024 }'
      ;;
    *[Mm])
      awk -v value="${raw%[Mm]}" 'BEGIN { printf "%.0f\n", value }'
      ;;
    *[Kk])
      awk -v value="${raw%[Kk]}" 'BEGIN { printf "%.0f\n", value / 1024 }'
      ;;
    *)
      printf '%s\n' "$raw"
      ;;
  esac
}

extract_sbatch_value() {
  local file="$1"
  local long_key="$2"
  local short_key="${3:-}"

  awk -v long_key="$long_key" -v short_key="$short_key" '
    /^[[:space:]]*#SBATCH([[:space:]]|$)/ {
      line = $0
      sub(/^[[:space:]]*#SBATCH[[:space:]]+/, "", line)
      n = split(line, parts, /[[:space:]]+/)
      for (i = 1; i <= n; i++) {
        token = parts[i]
        if (token == long_key && i < n) {
          print parts[i + 1]
        } else if (index(token, long_key "=") == 1) {
          value = token
          sub("^" long_key "=", "", value)
          print value
        } else if (short_key != "" && token == short_key && i < n) {
          print parts[i + 1]
        } else if (short_key != "" && index(token, short_key) == 1 && length(token) > length(short_key)) {
          value = token
          sub("^" short_key, "", value)
          print value
        }
      }
    }
  ' "$file" | tail -n 1
}

run_script=""
target_partition=""
target_nodes=""
expected_ntasks_per_node="1"
node_cores=""
node_memory_mb=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-partition) target_partition="$2"; shift 2 ;;
    --target-nodes) target_nodes="$2"; shift 2 ;;
    --expected-ntasks-per-node) expected_ntasks_per_node="$2"; shift 2 ;;
    --node-cores) node_cores="$2"; shift 2 ;;
    --node-memory-mb) node_memory_mb="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --*)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -z "$run_script" ]]; then
        run_script="$1"
        shift
      else
        echo "Unexpected positional argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$run_script" ]]; then
  usage >&2
  exit 2
fi
[[ -f "$run_script" ]] || { echo "Missing run script: $run_script" >&2; exit 1; }

pass_count=0
warn_count=0
fail_count=0

partition="$(trim "$(extract_sbatch_value "$run_script" "--partition" "-p")")"
nodes="$(trim "$(extract_sbatch_value "$run_script" "--nodes" "-N")")"
ntasks_per_node="$(trim "$(extract_sbatch_value "$run_script" "--ntasks-per-node")")"
cpus_per_task="$(trim "$(extract_sbatch_value "$run_script" "--cpus-per-task" "-c")")"
mem_raw="$(trim "$(extract_sbatch_value "$run_script" "--mem")")"
mem_mb=""
if [[ -n "$mem_raw" ]]; then
  mem_mb="$(normalize_mem_mb "$mem_raw")"
fi

echo "INFO: run_script=$run_script"
echo "INFO: partition=${partition:-unknown} nodes=${nodes:-unknown} ntasks_per_node=${ntasks_per_node:-unknown} cpus_per_task=${cpus_per_task:-unknown} mem=${mem_raw:-unknown}"

if [[ -n "$target_partition" ]]; then
  if [[ "$partition" == "$target_partition" ]]; then
    note_pass "partition matches target server partition: $target_partition"
  else
    note_fail "partition mismatch: script=${partition:-missing} target=$target_partition"
  fi
elif [[ -n "$partition" ]]; then
  note_warn "partition is set to $partition, but no target partition was provided for validation"
else
  note_warn "no partition directive found"
fi

if [[ -n "$target_nodes" ]]; then
  if [[ "$nodes" == "$target_nodes" ]]; then
    note_pass "node count matches requested allocation: $target_nodes"
  else
    note_fail "node count mismatch: script=${nodes:-missing} target=$target_nodes"
  fi
fi

if [[ -n "$expected_ntasks_per_node" ]]; then
  if [[ "$ntasks_per_node" == "$expected_ntasks_per_node" ]]; then
    note_pass "ntasks-per-node matches expected layout: $expected_ntasks_per_node"
  else
    note_fail "ntasks-per-node mismatch: script=${ntasks_per_node:-missing} expected=$expected_ntasks_per_node"
  fi
fi

if [[ -n "$node_cores" ]]; then
  if [[ -z "$cpus_per_task" ]]; then
    note_fail "missing --cpus-per-task; target node reports $node_cores cores"
  elif [[ "$cpus_per_task" == "$node_cores" ]]; then
    note_pass "cpus-per-task uses the full target node core count: $node_cores"
  else
    note_fail "cpus-per-task underfills target node: script=$cpus_per_task target=$node_cores"
  fi
else
  note_warn "target node core count not provided; cannot verify full-core use"
fi

if [[ -n "$node_memory_mb" ]]; then
  if [[ -z "$mem_raw" ]]; then
    note_fail "missing --mem; target node reports ${node_memory_mb} MB"
  elif [[ "$mem_raw" == "0" ]]; then
    note_fail "--mem=0 is not an explicit full-node memory request; use the target node RealMemory value"
  elif [[ "$mem_mb" == "$node_memory_mb" ]]; then
    note_pass "memory request uses the full target node memory: ${node_memory_mb} MB"
  else
    note_fail "memory request mismatch: script=${mem_mb:-missing} MB target=${node_memory_mb} MB"
  fi
else
  note_warn "target node memory not provided; cannot verify full-memory request"
fi

if grep -Eq 'OMP_NUM_THREADS=.*SLURM_CPUS_PER_TASK|omp_threads=.*SLURM_CPUS_PER_TASK' "$run_script"; then
  note_pass "OpenMP thread count is tied to SLURM_CPUS_PER_TASK"
else
  note_fail "OMP_NUM_THREADS should be tied to SLURM_CPUS_PER_TASK for full-node 1-rank/node jobs"
fi

echo "SUMMARY: pass=$pass_count warn=$warn_count fail=$fail_count"
if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi
echo "DONE: Slurm resource checks passed"
