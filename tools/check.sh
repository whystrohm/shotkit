#!/usr/bin/env bash
# Run every shotkit check. This is what CI calls, so a green local run means a green PR.
#
# Usage:
#   ./tools/check.sh                         # from a repo clone
#   ~/.claude/shotkit-tools/check.sh         # after ./install.sh, from any folder
#   ./tools/check.sh --quiet                 # only print failures and the summary
#
# It finds its own folder, so it runs the same from a clone and from an install. In a
# clone the packs are in brand-packs/; after an install they are in shotkit-brand-packs/
# next to shotkit-tools/.
#
# Requires: pip install pyyaml jsonschema

set -uo pipefail

TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$TOOLS")"
if [[ "$(basename "$TOOLS")" == "shotkit-tools" ]]; then
  PACKS="${ROOT}/shotkit-brand-packs"
else
  PACKS="${ROOT}/brand-packs"
fi
cd "$ROOT" || exit 1

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

# Preflight the two dependencies. Without this, a missing package turns one actionable
# line into fourteen identical failures and you have to read all of them to find out.
missing=""
"$PYTHON" -c 'import yaml' 2>/dev/null || missing="pyyaml"
"$PYTHON" -c 'import jsonschema' 2>/dev/null || missing="${missing:+$missing }jsonschema"
if [[ -n "$missing" ]]; then
  echo "Missing Python package(s): ${missing}" >&2
  echo >&2
  echo "  ${PYTHON} -m pip install ${missing}" >&2
  echo >&2
  echo "Then re-run ${TOOLS}/check.sh" >&2
  exit 1
fi

# Structure and schemas, scoped to the five shotkit skills
run "skills: selftest"               "$TOOLS/validate_skills.py" --selftest
run "skills: frontmatter"            "$TOOLS/validate_skills.py"
run "schemas: selftest"              "$TOOLS/validate_schemas.py" --selftest
run "schemas: are valid schemas"     "$TOOLS/validate_schemas.py"

# Capability matrix, including prose parity with the adapter files
run "capabilities: selftest"         "$TOOLS/validate_capabilities.py" --selftest
run "capabilities: matrix"           "$TOOLS/validate_capabilities.py"

# Brand-locks: packs allow templates, snapshots do not
run "brand-lock: selftest"           "$TOOLS/validate_brand_lock.py" --selftest
run "brand-lock: packs"              "$TOOLS/validate_brand_lock.py" \
  "$PACKS/_template.md" \
  "$PACKS/examples/saas-clean.md" \
  skills/brand-lock-extractor/examples/brand-lock.md
run "brand-lock: flagship pack"      "$TOOLS/validate_brand_lock.py" --require-configured \
  "$PACKS/whystrohm.md"
run "brand-lock: snapshots"          "$TOOLS/validate_brand_lock.py" --snapshots

# Storyboard instances, the rules JSON Schema cannot express
run "shots: selftest"                "$TOOLS/validate_shots.py" --selftest
run "shots: bundled examples"        "$TOOLS/validate_shots.py" --examples
run "shots: worked run"              "$TOOLS/validate_shots.py" \
  skills/visual-asset-critic/examples/worked-run

# Prompt files: the forge's hard rules, including verbatim series_lock anchors
run "prompts: selftest"              "$TOOLS/validate_prompts.py" --selftest
run "prompts: worked run"            "$TOOLS/validate_prompts.py" --examples

# Critique gate
run "critique: selftest"             "$TOOLS/validate_critique.py" --selftest
run "critique: fixtures"             "$TOOLS/validate_critique.py" --examples

# Provenance chain
run "provenance: selftest"           "$TOOLS/validate_provenance.py" --selftest
run "provenance: worked run"         "$TOOLS/validate_provenance.py" --examples --require-accept

# Shared contracts with the other WhyStrohm skills (skipped after an install)
run "contracts: selftest"            "$TOOLS/validate_contracts.py" --selftest
run "contracts: schemas and examples" "$TOOLS/validate_contracts.py"

# Tools that ship as part of the workflow
run "preview renderer: selftest"     "$TOOLS/shots-to-html.py" --selftest
run "prompt helper: selftest"        "$TOOLS/copy-prompt.py" --selftest

echo "─────────────────────────────────────────"
echo "${PASSED} passed, ${FAILED} failed"
if ((FAILED)); then
  printf 'failed: %s\n' "${FAILED_NAMES[@]}"
  exit 1
fi
exit 0
