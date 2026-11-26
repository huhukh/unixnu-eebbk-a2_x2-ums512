# Build the Realme C21Y RMX3261 (Unisoc UMS512) boot image from a real UEFI
# firmware volume.
#
#   sh tools/build-bootimg.sh [FD] [OUT]
#
# Defaults:
#   FD  = uefi/build/SILICIUM_UEFI.fd   (produced by uefi/build-bbk-a2.sh)
#   OUT = dist/boot.img
#
# Environment:
#   UNIXNU_TREE  UniXNU core checkout (default: ../UniXNU next to this repo,
#                or $GITHUB_WORKSPACE/UniXNU in CI)
#   RAMDISK      the UniXNU payload FAT image (default: none).  The UMS512
#                cboot passes the ramdisk through /chosen as the initrd, which
#                BbkA2PayloadDxe publishes so UniXNU/DarwinBoot can read the
#                payload.
#   DTB          compiled device tree (default: build/realme-c21y-rmx3261.dtb)
#
# The image uses the stock UMS512 layout: raw BootShim+FD in the kernel field
# and the device tree in the Android header v2 dtb_size/dtb_addr fields.  This
# is what Unisoc cboot loads; do NOT use the gzip+appended-dtb layout of
# `./unixnu bootimg` on this device.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
FD=${1:-$ROOT/uefi/build/SILICIUM_UEFI.fd}
OUT=${2:-$ROOT/dist/boot.img}
UNIXNU_TREE=${UNIXNU_TREE:-$ROOT/../UniXNU}
DTB=${DTB:-$ROOT/build/realme-c21y-rmx3261.dtb}
RAMDISK=${RAMDISK:-none}

if [ ! -f "$FD" ]; then
    echo "missing firmware volume: $FD" >&2
    exit 1
fi
if [ ! -d "$UNIXNU_TREE/scripts/unixnu" ]; then
    echo "missing UniXNU core checkout: $UNIXNU_TREE" >&2
    exit 1
fi

mkdir -p "$ROOT/build" "$(dirname "$OUT")"

echo "== compile device tree"
dtc -I dts -O dtb \
    -i "$ROOT/soc/UniXNU-ums512-common/dts" \
    -o "$DTB" "$ROOT/dts/realme-c21y-rmx3261.dts"

echo "== pack boot image"
python3 "$ROOT/tools/pack-device-bootimg.py" \
    --unixnu "$UNIXNU_TREE" \
    --device "$ROOT" \
    --uefi "$ROOT/uefi" \
    --fd "$FD" \
    --dtb "$DTB" \
    --ramdisk "$RAMDISK" \
    -o "$OUT"

echo "== verify boot image"
python3 "$ROOT/tools/verify-bootimg.py" "$OUT"

sha256sum "$OUT" | tee "$OUT.sha256"
