#!/bin/sh
#
# Build the BBK A2 / X2 / X2P (Unisoc UMS512) UEFI firmware and the boot shim
# that cboot can jump to.
#
#   sh build-bbk-a2.sh [DEBUG|RELEASE]
#
# Needs an EDK2 workspace as described in analysis/uefi/FEASIBILITY.md:
# mu_basecore, mu_plus, mu_oem_sample and UniXNU/uefi-sheng (only
# Silicon/Silicium is used) reachable through PACKAGES_PATH.  The environment
# comes from $BBK_A2_ENV, then $BBK_A2_DEPS/env.sh, then env-linux.sh next to
# this script.
#
# Output (in uefi-bbk-a2/build/):
#   SILICIUM_UEFI.fd     raw firmware volume, linked for FD_BASE (0x80800000)
#   BootShim.bin         the trampoline linked at 0x80080000
#   bbk-a2-uefi.bin      BootShim.bin + SILICIUM_UEFI.fd, the boot.img kernel
#                        field (the stock-layout packer wraps it in a v2 header)
#
# The boot image itself is produced by the workspace-level tooling
# (build/rebuild.sh -> ./unixnu bootimg / build/pack-device-bootimg.py) because
# the device tree and the Android header live outside this repository.
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
set -e


MODE=${1:-DEBUG}


FD_BASE=${BBK_A2_FD_BASE:-0x80800000}
FD_SIZE=${BBK_A2_FD_SIZE:-0x400000}
FD_BLOCKS=${BBK_A2_FD_BLOCKS:-0x400}
ROOT=`cd \`dirname $0\` && pwd`
OUT=$ROOT/build


# Extra flags for the shim: -DBBK_ARM_WATCHDOG, -DBBK_STAGE_COLORS,
