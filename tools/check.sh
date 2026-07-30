#!/usr/bin/env bash
# Run every shotkit check. This is what CI calls, so a green local run means a green PR.
#
# Usage:
#   ./tools/check.sh            # run everything, report a summary
#   ./tools/check.sh --quiet    # only print failures and the summary
#
# Requires: pip install pyyaml jsonschema

set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

PYTHON="${PYTHON:-python3}"
QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

PASSED=0
FAILED=0
FAILED_NAMES=()

run() {
  local label="$1"
  shift
  local output
  if output=$("$PYTHON" "$@" 2>&1); then
    PASSED=$((PASSED + 1))
    if [[ "$QUIET" == "0" ]]; then
      echo "PASS  ${label}"
      sed 's/^/      /' <<<"$output"
      echo
    else
      echo "PASS  ${label}"
    fi
  else
    FAILED=$((FAILED + 1))
    FAILED_NAMES+=("$label")
    echo "FAIL  ${label}"
    sed 's/^/      /' <<<"$output"
    echo
  fi
}

echo "shotkit checks, using $("$PYTHON" --version 2>&1)"
echo

# Structure and schemas
run "skills: frontmatter"            tools/validate_skills.py
run "schemas: are valid schemas"     tools/validate_schemas.py

# Capability matrix, including prose parity with the adapter files
run "capabilities: selftest"         tools/validate_capabilities.py --selftest
run "capabilities: matrix"           tools/validate_capabilities.py

# Brand-locks: packs allow templates, snapshots do not
run "brand-lock: selftest"           tools/validate_brand_lock.py --selftest
run "brand-lock: packs"              tools/validate_brand_lock.py \
  brand-packs/_template.md \
  brand-packs/whystrohm.md \
  brand-packs/examples/saas-clean.md \
  skills/brand-lock-extractor/examples/brand-lock.md
run "brand-lock: snapshots"          tools/validate_brand_lock.py --snapshots

# Storyboard instances, the rules JSON Schema cannot express
run "shots: selftest"                tools/validate_shots.py --selftest
run "shots: bundled examples"        tools/validate_shots.py --examples
run "shots: worked run"              tools/validate_shots.py \
  skills/visual-asset-critic/examples/worked-run

# Critique gate
run "critique: selftest"             tools/validate_critique.py --selftest
run "critique: fixtures"             tools/validate_critique.py --examples

# Provenance chain
run "provenance: selftest"           tools/validate_provenance.py --selftest
run "provenance: worked run"         tools/validate_provenance.py --examples --require-accept

# Tools that ship as part of the workflow
run "preview renderer: selftest"     tools/shots-to-html.py --selftest
run "prompt helper: selftest"        tools/copy-prompt.py --selftest

echo "─────────────────────────────────────────"
echo "${PASSED} passed, ${FAILED} failed"
if ((FAILED)); then
  printf 'failed: %s\n' "${FAILED_NAMES[@]}"
  exit 1
fi
exit 0
