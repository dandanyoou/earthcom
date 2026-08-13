#!/usr/bin/env bash
# Downloads the generated Higgsfield images into ./images/ with stable names.
# Run from inside this folder:  bash download-assets.sh

set -euo pipefail

BASE="https://d8j0ntlcm91z4.cloudfront.net/user_3Hrbb0QfKUgpzK5pR3NsdS8YF2n"
DEST="$(cd "$(dirname "$0")" && pwd)/images"
mkdir -p "$DEST"

fetch () {
  local name="$1" remote="$2"
  if [ -s "$DEST/$name" ]; then
    echo "skip  $name (already here)"
    return
  fi
  echo "get   $name"
  if ! curl -fsSL --retry 2 -o "$DEST/$name" "$BASE/$remote"; then
    echo "FAIL  $name — link may have expired; re-download it from the chat instead" >&2
    rm -f "$DEST/$name"
  fi
}

fetch earth.png      "hf_20260813_144526_7993e0ac-e2c6-44b6-a51d-5c85d2eeebfc.png"
fetch village-kr.png "hf_20260813_144733_45a0844d-229f-4835-8920-4e711cbd604d.png"
fetch village-us.png "hf_20260813_145410_bd5f58fa-de11-447e-a8ee-23aa27a27767.png"
fetch village-de.png "hf_20260813_145410_dca9238a-4e80-483b-b00f-1e69214990ba.png"
fetch village-vn.png "hf_20260813_145518_07b70baf-d8f2-4a1e-9141-e0963cd67d9f.png"
fetch village-br.png "hf_20260813_145519_f59f7828-8fe6-4a05-8e21-7ac2daccc817.png"
fetch village-in.png "hf_20260813_145519_c72f0308-3932-48cb-a134-0a5a0051f2c1.png"

echo
echo "done -> $DEST"
ls -lh "$DEST"
echo
echo "next: open index.html"
