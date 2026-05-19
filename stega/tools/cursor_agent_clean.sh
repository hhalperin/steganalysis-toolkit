#!/usr/bin/env bash
# Cursor Agent Headless - Watermark Removal Pipeline
# Requires: Cursor Pro, agent CLI installed, CURSOR_API_KEY set (or agent auth)
# Usage: ./stega/tools/cursor_agent_clean.sh <path_to_image>
#        ./stega/tools/cursor_agent_clean.sh assets/dirty/photo.jpg

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
IMAGE="${1:?Usage: $0 <image_path>}"

# Resolve image path
if [[ "$IMAGE" != /* ]]; then
    IMAGE="$PROJECT_ROOT/$IMAGE"
fi
[[ -f "$IMAGE" ]] || { echo "Image not found: $IMAGE"; exit 1; }
IMAGE="$(realpath "$IMAGE")"

# Build prompt from template
PROMPT_TEMPLATE="$SCRIPT_DIR/prompts/agentic_watermark_removal.txt"
TEMP_PROMPT=$(mktemp)
trap "rm -f $TEMP_PROMPT" EXIT
sed "s|{{IMAGE_PATH}}|$IMAGE|g" "$PROMPT_TEMPLATE" > "$TEMP_PROMPT"

cd "$PROJECT_ROOT"
echo "Running Cursor agent on: $IMAGE"
agent -p "$(cat "$TEMP_PROMPT")" --force --output-format text
