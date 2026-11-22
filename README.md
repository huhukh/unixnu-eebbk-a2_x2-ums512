# UniXNU Realme C21Y RMX3261 port

Experimental device port for Realme C21Y (RMX3261/RMX3263), Unisoc T610 / UMS512.

This repository started from the EEBBK A2/X2 UMS512 bring-up. Only SoC-level
code that is genuinely shared may be reused. EEBBK board-specific UEFI, memory
map, framebuffer, SDHCI and peripheral settings are not valid C21Y defaults.

## Current milestone

- C21Y board metadata and defconfig are selected.
- Shared UMS512 CPU/GIC/timer definitions are used as a starting point.
- Device-tree file is intentionally conservative and host-build oriented.
- GitHub Actions checks configuration resolution and DTS compilation.
- C21Y UEFI handoff, memory map, storage, display, input, power, network and
audio are not yet hardware-qualified.

**Do not flash artifacts from this branch yet.** A successful host build or DTS
compile is not evidence that the phone can boot UniXNU. Obtain and decode the
exact stock RMX3261 DTB and boot-chain handoff details first.

A first-pass audit of the supplied stock boot/DTB/DTBO files is recorded in
[`docs/stock-firmware-audit.md`](docs/stock-firmware-audit.md). The board ID
matches, but the effective DRAM map remains unresolved.
