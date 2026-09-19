#!/usr/bin/env bash
# Extract evaluation frames from a render.
#   ./extract_frames.sh <render.mp4> <out_dir> [critical_frames.txt]
# Without a frame list, extracts 1 fps for browsing.
# With a list (one frame number per line — the 5 contact frames + 3 face-closest frames from
# the Sequencer timeline), extracts exactly those frames losslessly.
set -euo pipefail
in="$1"; out="$2"; list="${3:-}"
mkdir -p "$out"
if [[ -z "$list" ]]; then
  ffmpeg -loglevel error -i "$in" -vf fps=1 "$out/browse_%04d.png"
else
  while read -r f; do
    [[ -z "$f" ]] && continue
    ffmpeg -loglevel error -i "$in" -vf "select=eq(n\,$f)" -vframes 1 "$out/frame_$(printf '%05d' "$f").png"
  done < "$list"
fi
echo "wrote $(ls "$out" | wc -l | tr -d ' ') frames to $out"
