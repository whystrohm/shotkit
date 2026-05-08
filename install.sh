#!/usr/bin/env bash
# shotkit. Install all four skills into ~/.claude/skills/
#
# Usage:
#   ./install.sh             # install to ~/.claude/skills/ (user scope)
#   ./install.sh --project   # install to ./.claude/skills/ (project scope)

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="${SCRIPT_DIR}/skills"

if [[ ! -d "${SKILLS_DIR}" ]]; then
  echo "skills/ directory not found at ${SKILLS_DIR}"
  echo "Are you running this from the shotkit repo root?"
  exit 1
fi

# Default: user-scope install
TARGET="${HOME}/.claude/skills"
SCOPE="user"

if [[ "${1:-}" == "--project" ]]; then
  TARGET="$(pwd)/.claude/skills"
  SCOPE="project"
fi

mkdir -p "${TARGET}"

SKILLS=(
  "storyboard-architect"
  "visual-prompt-forge"
  "visual-asset-critic"
  "storyboard-html-preview"
)

echo ""
echo "Installing shotkit"
echo "  scope:  ${SCOPE}"
echo "  target: ${TARGET}"
echo ""

for skill in "${SKILLS[@]}"; do
  src="${SKILLS_DIR}/${skill}"
  dst="${TARGET}/${skill}"

  if [[ ! -d "${src}" ]]; then
    echo "  [skip]    ${skill}: source missing"
    continue
  fi

  if [[ -d "${dst}" ]]; then
    echo "  [replace] ${skill}"
    rm -rf "${dst}"
  else
    echo "  [install] ${skill}"
  fi

  cp -R "${src}" "${dst}"
done

echo ""
echo "Done. Restart your Claude Code session to pick up the new skills."
echo ""
echo 'Try: "30-second founder explainer for your-brand. Pain-reframe-promise structure."'
echo ""
