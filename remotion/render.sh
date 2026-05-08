#!/usr/bin/env bash
# Render the shotkit demo GIF for the README.
# Output: ../docs/images/demo.gif
# Target: under 8MB, 1280x720, 30fps, 8 seconds, looping.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

mkdir -p ../docs/images
mkdir -p public

# Copy the example preview into public/ so the composition iframe can load it.
cp ../skills/storyboard-architect/examples/30s-pain-proof-promise/preview.html public/preview.html

npx remotion render \
  ShotkitDemo \
  ../docs/images/demo.gif \
  --codec=gif \
  --width=1280 \
  --height=720 \
  --concurrency=4

echo ""
echo "Rendered to ../docs/images/demo.gif"
ls -lh ../docs/images/demo.gif
