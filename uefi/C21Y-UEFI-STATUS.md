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
