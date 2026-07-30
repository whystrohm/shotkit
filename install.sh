#!/usr/bin/env bash
# shotkit. Install all five skills, plus the tools they reference, into ~/.claude/
# Help text lives in usage() below, not in this comment block, so the two cannot drift.

set -euo pipefail

usage() {
  cat <<'EOF'
shotkit. Install all five skills, plus the tools they reference, into ~/.claude/

The skills cite tools/validate_critique.py, tools/validate_shots.py, and
tools/copy-prompt.py in their workflows. Installing the skills without those tools
leaves every one of those paths unresolvable, so both go in together.

Usage:
  ./install.sh                # install to ~/.claude/ (user scope)
  ./install.sh --project      # install to ./.claude/ (project scope)
  ./install.sh --skills-only  # skip the tools, skills only
  ./install.sh --dry-run      # show what would happen, change nothing
  ./install.sh --force        # overwrite existing skills without prompting
  ./install.sh --uninstall    # remove the five shotkit skills and the tools
  ./install.sh --help         # show this help

The validators need two packages: pip install pyyaml jsonschema
EOF
}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="${SCRIPT_DIR}/skills"
TOOLS_DIR="${SCRIPT_DIR}/tools"

SCOPE="user"
ROOT="${HOME}/.claude"
DRY_RUN=0
FORCE=0
UNINSTALL=0
SKILLS_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --project)        SCOPE="project"; ROOT="$(pwd)/.claude" ;;
    --skills-only)    SKILLS_ONLY=1 ;;
    --dry-run)        DRY_RUN=1 ;;
    --force)          FORCE=1 ;;
    --uninstall)      UNINSTALL=1 ;;
    -h|--help)        usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; echo "Try: ./install.sh --help" >&2; exit 2 ;;
  esac
done

TARGET="${ROOT}/skills"
TOOLS_TARGET="${ROOT}/shotkit-tools"

SKILLS=(
  "brand-lock-extractor"
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

# Copy a directory without dragging along editor and Finder droppings. cp -R took
# .DS_Store with it, which then ended up inside every .skill zip.
copy_tree() {
  local src="$1" dst="$2"
  if command -v rsync >/dev/null 2>&1; then
    run rsync -a \
      --exclude '.DS_Store' --exclude 'Thumbs.db' \
      --exclude '__pycache__' --exclude '*.pyc' \
      "${src}/" "${dst}/"
  else
    run cp -R "${src}" "${dst}"
    if [[ "$DRY_RUN" != "1" ]]; then
      find "${dst}" \( -name '.DS_Store' -o -name 'Thumbs.db' -o -name '*.pyc' \) -delete
      find "${dst}" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    fi
  fi
}

if [[ "$UNINSTALL" == "1" ]]; then
  echo ""
  echo "Uninstalling shotkit from ${ROOT}"
  for skill in "${SKILLS[@]}"; do
    dst="${TARGET}/${skill}"
    if [[ -d "${dst}" ]]; then echo "  [remove]  ${skill}"; run rm -rf "${dst}"
    else echo "  [skip]    ${skill}: not installed"; fi
  done
  if [[ -d "${TOOLS_TARGET}" ]]; then
    echo "  [remove]  shotkit-tools"
    run rm -rf "${TOOLS_TARGET}"
  else
    echo "  [skip]    shotkit-tools: not installed"
  fi
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
echo "  skills: ${TARGET}"
[[ "$SKILLS_ONLY" == "1" ]] || echo "  tools:  ${TOOLS_TARGET}"
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

  copy_tree "${src}" "${dst}"
done

if [[ "$SKILLS_ONLY" != "1" ]]; then
  if [[ ! -d "${TOOLS_DIR}" ]]; then
    echo "  [skip]    tools: source missing"
  else
    if [[ -d "${TOOLS_TARGET}" ]]; then
      echo "  [replace] shotkit-tools"
      run rm -rf "${TOOLS_TARGET}"
    else
      echo "  [install] shotkit-tools"
    fi
    copy_tree "${TOOLS_DIR}" "${TOOLS_TARGET}"
  fi
fi

echo ""
echo "Done. Restart your Claude Code session to pick up the new skills."
if [[ "$SKILLS_ONLY" != "1" ]]; then
  echo ""
  echo "The validators need two packages:"
  echo "  pip install pyyaml jsonschema"
  echo ""
  echo "Then, from a project's output directory:"
  echo "  python ${TOOLS_TARGET}/validate_shots.py output/"
  echo "  python ${TOOLS_TARGET}/validate_provenance.py output/ --require-accept"
fi
echo ""
echo 'Try: "30-second founder explainer for your-brand. Pain-reframe-promise structure."'
echo ""
