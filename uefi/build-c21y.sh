#!/bin/sh
#
# Compile the Realme C21Y EDK2 platform scaffold.
# This produces an FV only; it is NOT a boot.img and is NOT flashable.
#
# Required:
#   C21Y_ENV=/path/to/edk2-env.sh
#   C21Y_FD_BASE=... (must be measured from C21Y cboot before any device use)
# Optional:
#   C21Y_FD_SIZE=0x400000
#   C21Y_FD_BLOCKS=0x400
#   C21Y_BUILD_MODE=DEBUG|RELEASE
#
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODE=${C21Y_BUILD_MODE:-DEBUG}
: "${C21Y_ENV:?Set C21Y_ENV to a prepared EDK2 environment script}"
: "${C21Y_FD_BASE:?Set C21Y_FD_BASE only after measuring C21Y cboot relocation address}"

case "$MODE" in DEBUG|RELEASE) ;; *) echo "MODE must be DEBUG or RELEASE" >&2; exit 2;; esac
case "$C21Y_FD_BASE" in 0x[0-9a-fA-F]*|[0-9]*) ;; *) echo "Invalid C21Y_FD_BASE" >&2; exit 2;; esac

export BBK_A2_REPO="$ROOT"
export BBK_A2_DEPS=${C21Y_DEPS:-$HOME/c21y-uefi}
unset BBK_A2_UNIXNU || true
. "$C21Y_ENV"

OUT="$ROOT/build-c21y"
BUILD_DIR="${WORKSPACE}/Build/c21yPkg/${MODE}_CLANGDWARF"
mkdir -p "$OUT"

echo "== Compiling C21Y EDK2 scaffold (not bootable) =="
build -a AARCH64 -t CLANGDWARF -b "$MODE" -p c21yPkg/c21y.dsc -n "${C21Y_JOBS:-2}" \
  -D FD_BASE="$C21Y_FD_BASE" \
  -D FD_SIZE="${C21Y_FD_SIZE:-0x400000}" \
  -D FD_BLOCKS="${C21Y_FD_BLOCKS:-0x400}"

FD="$BUILD_DIR/FV/SILICIUM_UEFI.fd"
test -s "$FD"
cp "$FD" "$OUT/realme-c21y-uefi-scaffold.fd"
printf '%s\n' "Built: $OUT/realme-c21y-uefi-scaffold.fd" \
  "WARNING: compile success does not validate cboot handoff, memory map, or boot safety." \
  "DO NOT package or flash this scaffold."
