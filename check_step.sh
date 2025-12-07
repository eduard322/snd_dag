#!/usr/bin/env bash
# check_step.sh <step_name> <output_file> <pre_skip_code>

step="$1"
outfile="$2"
pre_skip_code="$3"

echo "[PRE] Checking ${step} → ${outfile}"

if [ -s "$outfile" ]; then
  echo "[PRE] Output exists, skipping ${step}"
  exit "${pre_skip_code}"
fi

echo "[PRE] Output missing, running ${step}"
exit 0
