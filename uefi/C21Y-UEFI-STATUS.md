# Realme C21Y UEFI port status

## What exists
- Separate EDK2 platform package: `Platforms/Unisoc/c21yPkg`.
- Separate memory-map library, limited to stock-DTB-confirmed reserved ranges.
- Separate C21Y boot configuration and build script.
- UMS512 SoC-wide GIC/timer/UART definitions reused from the shared UMS512 package.
- CI performs a real EDK2 firmware-volume compile for the C21Y DSC.

## Validation completed
Latest GitHub Actions run: [#50 - fe2ed950](https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45004636483) completed successfully on 2026-11-22.
- Linux C21Y configuration and DTS job: success.
- EDK2 C21Y firmware-volume compile (scaffold) job: success.
- Artifacts uploaded: `realme-c21y-edk2-scaffold` and `realme-c21y-build-check`.

The downloaded 4-MiB FD artifact was inspected offline:
- Firmware Volume signature `_FVH` is present.
- Declared FV length matches the 4,194,304-byte file.
- FV header checksum is valid.
- Block map is 1,024 blocks x 4 KiB.
- Five FFS files were structurally located; strings identify SEC and the RamManagerDxe, DtPlatformDxe, and ResetSystemRuntimeDxe modules.

This validates that CI produced a structurally recognizable EDK2 firmware volume. It does NOT prove that firmware executes on the phone, that DXE memory allocation succeeds, that FD placement is safe, or that XNU boots.

## Additional stock-device evidence (ADB, 2026-11-22)
- `ro.product.device=RMX3261`, `ro.boot.hardware=S19610AA1`, `ro.hardware=S19610AA1`.
- `ro.boot.auto.chipid=UMS512-AC`, `ro.boot.auto.efuse=T610`, and `ro.boot.hw_id=19610_1_10_PVT`.
- `ro.boot.ddrsize=4096M`; `ro.boot.ddrsize.range=[4096,5120)`. This corroborates a 4-GiB DRAM configuration.
- `ro.boot.board_id=S19610BA1` and `ro.boot.product.hardware.sku=S19610BA1`, while the silicon/hardware identity remains `S19610AA1`. Keep these identifiers distinct; do not replace the DT compatible based only on the product SKU.
- `ro.boot.boot_devices=soc/soc:ap-apb/71400000.sdio`; this is Android's reported boot-device path, not proof of the bootloader's UEFI handoff.
- `ro.boot.flash.locked=0`, `ro.boot.vbmeta.device_state=unlocked`, and `ro.boot.verifiedbootstate=orange`.
- Unprivileged ADB cannot read `/proc/iomem` or `/proc/cmdline` (permission denied).
- `/proc/zoneinfo` reports two 524,288-page zones: DMA starts PFN 524288 (0x80000000) and Normal starts PFN 1048576 (0x100000000). This is consistent with two 2-GiB banks and approximately 4 GiB total DRAM. It is runtime Linux allocator evidence, not a substitute for cboot's live FDT.

## Android partition layout observed via unprivileged ADB (2026-11-22)
- The device exposes its named partitions at `/dev/block/by-name`; `/dev/block/bootdevice/by-name` does not exist on this build.
- A/B boot-related partitions: `boot_a/b` = `mmcblk0p40/p41`; `vendor_boot_a/b` = `p42/p43`; `dtb_a/b` = `p44/p45`; `dtbo_a/b` = `p46/p47`; `uboot_a/b` = `p8/p9`.
- Other relevant partitions include `vbmeta_a/b` = `p54/p55`, `misc` = `p3`, and `super` = `p48`.
- The reported active slot property is `_a` (`ro.boot.slot_suffix`). The symlink listing is read-only metadata and does not establish which partition was actually consumed at each boot stage.
- No partition has been read or modified by this audit. Do not write to these block devices.

- Attempts to read `/sys/class/block/mmcblk0pN/size` for boot-related partitions via unprivileged ADB returned `Permission denied`; partition capacities remain unknown. Do not infer sizes from partition numbering or symlink targets.

## Fastboot partition capacities (read-only, 2026-11-22)
Fastboot `getvar partition-size` returned byte counts:
- `boot_a`: 67,108,864 bytes (64 MiB).
- `vendor_boot_a`: 104,857,600 bytes (100 MiB).
- `dtb_a`: 8,388,608 bytes (8 MiB).
- `dtbo_a`: 8,388,608 bytes (8 MiB).
- `uboot_a`: 1,048,576 bytes (1 MiB).
These are partition capacities, not actual image sizes. Only slot A capacities were queried. No writes were performed.

- Fastboot queries for `current-slot`, `product`, `unlocked`, `secure`, and `max-download-size` returned empty values (no value after the colon). Treat these variables as unsupported/not exposed by this bootloader interface; do not infer their values from the empty response. Android properties separately report slot suffix `_a` and unlocked state.

- `fastboot getvar all` returned only an empty `all:` field, with no variable list. The standard Fastboot variable interface is therefore not providing useful inventory on this device/build; this does not imply that all Fastboot commands are unsupported.

## Explicitly not bootable / not flashable yet
This remains a platform scaffold, not a tested boot image. The vendor DTB describes a 2-GiB bank at 0x80000000, while Android runtime zoneinfo indicates additional memory above 4 GiB. The live cboot handoff FDT has not been captured.

The current memory map is intentionally incomplete. The SEC code contains a diagnostic string for failure to locate a DXE heap region; this is a reminder that the memory HOB/heap handoff must be validated, not evidence that DXE has successfully run on C21Y.

The following must be established before building a usable boot payload: actual kernel-field load address, x0/FDT handoff address, all usable RAM banks, cboot-owned reservations, safe FD relocation window, and UART baud at handoff.

The 0x80800000 FD base and 0x80480000 stack values remain unverified placeholders and must not be used for flashing. No BBK A2 memory map, display, eMMC, or watchdog-reset driver is included.

## Next milestones
1. Establish the C21Y cboot handoff contract from read-only stock-device evidence: kernel load address, x0/FDT, usable RAM banks, reserved regions, FD relocation window, and UART settings.
2. Implement and audit the C21Y memory HOB/DXE heap layout using only verified memory ranges; then rebuild and inspect the FV.
3. Add the required board-specific platform initialization and boot flow.
4. Build a controlled test payload and perform a non-destructive boot test only after the handoff and recovery path are understood.
5. Verify XNU kernel entry and early boot logs. A successful EDK2 compile alone is not evidence that XNU boots.

Until these checks are complete, do not package or flash the scaffold.


## Stock SPL/U-Boot binary string audit (read-only, 2026-11-22)
The extracted stock firmware binaries in the SPD DLFiles directory were scanned for printable strings. This is static string evidence only; it does not reveal function implementations or runtime values.

- `u-boot-sign.bin` identifies itself as `U-Boot 2015.07-gd0ac2f1-dirty (Apr 22 2024)` for `SHARKL5PRO`.
- SPL strings identify `SHARKL5pro ddr init`, `ddr init pass!!!`, DRAM discrete/eMCP status, and an automatic CS1-detection path. These are compiled messages, not proof of the live rank/channel configuration.
- U-Boot contains strings for `fdt_fixup_ddr_size`, `scan_memory_region`, `fixup_memory_addr`, and `fdt_fixup_memory_region`.
- Related diagnostics mention `mem_cs`, `mem_cs0_sz`, CS0/CS1 DDR-training reservations, and updates to `/memory` `reg` address and size. It also has format strings for `androidboot.ddrsize=%lldM` and `androidboot.ddrsize.range=%s`.
- U-Boot strings include `earlycon=sprd_serial,0x70100000,115200n8`, `console=ttyS1`, and `bootcmd=cboot normal`. Treat these as stock boot-path clues; the actual serial handoff settings and FDT contents still need runtime confirmation.
- The embedded environment string `bootargs=mem=512M ... console=ttyS0` is not the effective Android RAM size or confirmed active kernel command line. Do not copy `mem=512M` into the C21Y UEFI configuration.
- Attempts to read `/proc/device-tree/memory/reg` and `/sys/firmware/devicetree/base/memory/reg` via unprivileged ADB returned `Permission denied`. The attempted host-side output file was empty; no live FDT bytes were obtained.

Interpretation: stock U-Boot appears to dynamically fix up the FDT memory node and reserve platform memory before entering the Android boot flow. This strengthens the requirement to obtain the final cboot handoff FDT/memory map rather than treating the packaged base DTB as the final map. Static strings alone do not establish bank boundaries, reservation addresses, FDT address, or UEFI/XNU handoff values.
