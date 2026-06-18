#!/usr/bin/env bash
# shotkit. Install all four skills into ~/.claude/skills/
#
# Usage:
#   ./install.sh                # install to ~/.claude/skills/ (user scope)
#   ./install.sh --project      # install to ./.claude/skills/ (project scope)
#   ./install.sh --dry-run      # show what would happen, change nothing
#   ./install.sh --force        # overwrite existing skills without prompting
#   ./install.sh --uninstall    # remove the four shotkit skills
#   ./install.sh --help         # show this help

set -euo pipefail

usage() {
  sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="${SCRIPT_DIR}/skills"

SCOPE="user"
TARGET="${HOME}/.claude/skills"
DRY_RUN=0
FORCE=0
UNINSTALL=0

for arg in "$@"; do
  case "$arg" in
    --project)        SCOPE="project"; TARGET="$(pwd)/.claude/skills" ;;
    --dry-run)        DRY_RUN=1 ;;
    --force)          FORCE=1 ;;
    --uninstall)      UNINSTALL=1 ;;
    -h|--help)        usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; echo "Try: ./install.sh --help" >&2; exit 2 ;;
  esac
done

SKILLS=(
  "storyboard-architect"
  "visual-prompt-forge"
  "visual-asset-critic"
  "storyboard-html-preview"
)

# Execute a command, or print it (quoted) under --dry-run. No eval; args stay
# a real argv array, so paths with spaces are safe.
run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '  [dry-run]'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}

if [[ "$UNINSTALL" == "1" ]]; then
  echo ""
  echo "Uninstalling shotkit from ${TARGET}"
  for skill in "${SKILLS[@]}"; do
    dst="${TARGET}/${skill}"
    if [[ -d "${dst}" ]]; then echo "  [remove]  ${skill}"; run rm -rf "${dst}"
    else echo "  [skip]    ${skill}: not installed"; fi
  done
  echo ""
  echo "Done."
  exit 0
fi

if [[ ! -d "${SKILLS_DIR}" ]]; then
  echo "skills/ directory not found at ${SKILLS_DIR}" >&2
  echo "Are you running this from the shotkit repo root?" >&2
  exit 1
fi

echo ""
echo "Installing shotkit"
echo "  scope:  ${SCOPE}"
echo "  target: ${TARGET}"
[[ "$DRY_RUN" == "1" ]] && echo "  mode:   dry-run (no changes)"
echo ""

run mkdir -p "${TARGET}"

for skill in "${SKILLS[@]}"; do
  src="${SKILLS_DIR}/${skill}"
  dst="${TARGET}/${skill}"

  if [[ ! -d "${src}" ]]; then
    echo "  [skip]    ${skill}: source missing"
    continue
  fi

  if [[ -d "${dst}" ]]; then
    if [[ "$FORCE" != "1" && "$DRY_RUN" != "1" ]]; then
      read -r -p "  ${skill} already exists. Overwrite? [y/N] " reply
      if [[ ! "$reply" =~ ^[Yy]$ ]]; then echo "  [skip]    ${skill}"; continue; fi
    fi
    echo "  [replace] ${skill}"
    run rm -rf "${dst}"
  else
    echo "  [install] ${skill}"
  fi

  run cp -R "${src}" "${dst}"
done

echo ""
echo "Done. Restart your Claude Code session to pick up the new skills."
echo ""
echo 'Try: "30-second founder explainer for your-brand. Pain-reframe-promise structure."'
echo ""
