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

## Next milestone
Add a C21Y-specific build target and static validation, then resolve handoff
addresses from stock bootloader evidence before enabling a hardware boot test.
