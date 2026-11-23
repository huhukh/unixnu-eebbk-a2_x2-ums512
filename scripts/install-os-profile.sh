#!/usr/bin/env bash
# Install device-repository OS profiles into the UniXNU checkout for resolution/build.
set -euo pipefail
DEVICE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
UNIXNU=${1:?usage: scripts/install-os-profile.sh UNIXNU_CHECKOUT}
for profile in "$DEVICE"/os-profiles/*/; do
  name=$(basename "$profile")
  target="$UNIXNU/profiles/os/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "install-os-profile: refusing to replace existing directory: $target" >&2
    exit 1
  fi
  ln -sfn "${profile%/}" "$target"
  echo "$name -> $target"
done
