# Realme C21Y UEFI port status

## What exists
- Separate EDK2 platform package: `Platforms/Unisoc/c21yPkg`.
- Separate memory-map library, with only stock-DTB-confirmed reserved ranges.
- Separate C21Y boot configuration file.
- UMS512 SoC-wide GIC/timer/UART definitions are reused from the shared UMS512 package.

## Explicitly not bootable yet
This is a platform **scaffold**, not a flashable UEFI image. The vendor DTB shows
a 2-GiB bank at 0x80000000, but Android runtime zoneinfo indicates additional
memory above 4 GiB. The live cboot handoff FDT has not been captured. The
following must be measured before enabling DXE allocations or packaging a boot
image: actual kernel-field load address, x0/FDT handoff address, available RAM
banks, cboot-owned regions, safe FD relocation window, and UART baud at handoff.

The 0x80800000 FD base and 0x80480000 stack values are inherited candidates,
not validated C21Y facts. They are placeholders and must not be used for
flashing. No BBK A2 memory map, display, eMMC, or watchdog-reset driver is
included.

## Validation completed

The repository CI workflow has passed these checks on the C21Y branch:
- C21Y repository/configuration resolution through the UniXNU build driver.
- Static audit of the C21Y UEFI scaffold.
- Shell syntax validation of `uefi/build-c21y.sh`.
- Compilation and decompilation of the C21Y Device Tree.
- Build-check artifact upload.

This is **not** an EDK2 firmware build. No `SILICIUM_UEFI.fd` has been produced or tested, and no hardware boot has been attempted.

## Next milestones

1. Prepare and pin the exact EDK2/Mu/Silicium dependency revisions used by the existing UMS512 platform.
2. Run a real C21Y EDK2 compile in CI; fix DSC/FDF/package integration errors without borrowing BBK A2 board addresses.
3. Capture/derive the C21Y cboot handoff contract: kernel load address, x0/FDT, actual usable RAM banks, bootloader reservations, safe FD relocation window, and UART baud at handoff.
4. Only after those values are independently verified, add a boot-payload build and a controlled hardware test.

Until then, this scaffold must not be packaged or flashed.
