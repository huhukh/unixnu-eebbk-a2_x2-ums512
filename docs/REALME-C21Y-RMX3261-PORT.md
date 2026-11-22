# Realme C21Y RMX3261 porting notes

## Scope and status

This is a research note for a separate Realme C21Y board port. It does not change the existing EEBBK A2/X2 target and does not claim that a C21Y firmware image is ready to flash. A host-side build of UniXNU/EDK2 is not evidence that the image can boot on the phone.

## Target identity

- Product: Realme C21Y, model RMX3261
- Board/hardware ID reported by the owner: `S19610AA1`
- SoC family: Unisoc UMS512 / SharkL5Pro, T610 family
- Android base reported: Android 11, firmware `RMX3261_11_A.119`
- Linux kernel source: Android 4.14.193
- Active slot reported: `_a`
- Architecture: ARM64

Public device-tree references identify the C21Y board family as `ums512_1h10`. This differs from this repository's current EEBBK A2 target, `ums512_1h190`. Shared SoC facts can guide the port, but board-specific values must not be copied from EEBBK.

## Public Realme references

- `serzhbsv/android_device_realme_RMX3261`, branch `android-11`: TWRP device configuration. Its `BoardConfig.mk` reports platform `ums512`, board `ums512_1h10`, Android boot header v2, page size 2048, kernel base `0x00000000`, ramdisk offset `0x05400000`, tags offset `0x100`, and a prebuilt kernel/DTB setup. Its README lists a 720x1600 display and RMX3261/RMX3262/RMX3263 family support.
- `realme-kernel-opensource/realme_C21Y-AndroidR-kernel-source`, branch `master`: Linux 4.14.193 source. Relevant references include `arch/arm64/boot/dts/sprd/ums512.dtsi`, `arch/arm64/boot/dts/sprd/ums512-1h10-overlay.dts`, `arch/arm64/boot/dts/sprd/S19610AA1-overlay.dts`, and `sprd-reserved-memory/ums512-1h10.cfg`.
- `twrpdtgen/android_device_realme_RMX3261`: public TWRP device-tree reference.
- `depesh1977/Realme-C21Y-RMX3261`: public device/recovery reference.

The Linux board overlays contain useful leads for the 720x1600 panel/touch path, GPIOs, PMIC/charger, WLAN, camera and reserved regions. They are Linux DT overlays, not a ready-made UniXNU ADT or EDK2 memory map. Their values must be checked against the exact phone firmware/DTB and variant before being used in a boot path.

## Boot-image observations (not yet independently verified from attached artifacts)

The owner reports that a public/stock RMX3261 A.119 `boot.img` has Android boot header v2, page size 2048, kernel address `0x8000`, ramdisk address `0x5400000`, kernel size 21,585,936 bytes and a gzip ramdisk. A separate report mentions a zero-sized `vendor_boot` ramdisk. These are currently user-provided observations; the actual slot-A `boot_a` and `dtbo_a` binaries have not been supplied for direct inspection.

There is an unresolved size discrepancy: the partition listing reports `boot_a` size `0x400000` (4 MiB), while the reported boot image/kernel is much larger. Do not rely on that size as a verified partition capacity until the extraction tool's size units and output are checked. The `dtbo_a` size was reported as `0x800000` (8 MiB), but its table entries have not been dumped here.

## What must be resolved before claiming a device build

1. Inspect the exact RMX3261 slot-A boot image and DTBO, including all DTB/overlay entries, compatible strings, DRAM banks, reserved-memory regions and chosen/initrd properties.
2. Verify the Realme bootloader handoff experimentally or from reliable firmware evidence: entry address, argument registers/FDT address, MMU/cache state, UART and framebuffer state. EEBBK cboot assumptions in `uefi/BootShim` and its UEFI platform cannot be presumed to apply.
3. Create a distinct C21Y DTS/ADT and EDK2 board package/memory map. Do not overwrite `dts/bbk-a2.dts` or reuse the EEBBK `MemoryMapLib.c` values as C21Y values.
4. Check the actual RAM size and every secure/modem/DSP/display carveout from the C21Y DTB/bootloader. The C21Y has 4 GB RAM according to the owner, whereas the EEBBK board has a different memory map.
5. Confirm the boot image format, partition capacity and safe boot/recovery method. No flashing or repartitioning should be attempted during initial bring-up.
6. Start with a conservative serial/debug milestone and host-side DTB/ADT checks. Display, eMMC, input, Wi-Fi, GPU, audio, charging and power management each require separate porting and hardware validation; the Linux drivers cannot be linked directly into XNU.

## Current conclusion

The public sources establish that RMX3261 is a plausible same-SoC-family porting target and provide substantial Linux board data. They do not establish that the existing EEBBK firmware, memory map, storage driver, or boot image is usable on RMX3261. This note intentionally records the evidence and blockers rather than presenting an unverified image as build-ready.
