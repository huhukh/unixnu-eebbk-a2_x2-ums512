# Realme C21Y UEFI port status

## What exists
- Separate EDK2 platform package: `Platforms/Unisoc/c21yPkg`.
- Separate memory-map library, limited to stock-DTB-confirmed reserved ranges.
- Separate C21Y boot configuration and build script.
- UMS512 SoC-wide GIC/timer/UART definitions reused from the shared UMS512 package.
- CI now performs a real EDK2 firmware-volume compile for the C21Y DSC.

## Validation completed
Latest GitHub Actions run: [#50 - fe2ed950](https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45004636483) completed successfully on 2026-11-22.
- Linux C21Y configuration and DTS job: success.
- EDK2 C21Y firmware-volume compile (scaffold) job: success.
- Artifacts uploaded: `realme-c21y-edk2-scaffold` and `realme-c21y-build-check`.

This confirms the current C21Y EDK2 package compiles in CI. It does NOT confirm that the firmware runs on the phone, that the FD placement is safe, or that XNU boots.

## Explicitly not bootable / not flashable yet
This remains a platform scaffold, not a tested boot image. The vendor DTB describes a 2-GiB bank at 0x80000000, while Android runtime zoneinfo indicates additional memory above 4 GiB. The live cboot handoff FDT has not been captured.

The following must be established before building a usable boot payload: actual kernel-field load address, x0/FDT handoff address, all usable RAM banks, cboot-owned reservations, safe FD relocation window, and UART baud at handoff.

The 0x80800000 FD base and 0x80480000 stack values remain unverified placeholders and must not be used for flashing. No BBK A2 memory map, display, eMMC, or watchdog-reset driver is included.

## Next milestones
1. Inspect the successful EDK2 output and validate the generated firmware-volume layout and artifact contents.
2. Establish the C21Y cboot handoff contract from read-only stock-device evidence: kernel load address, x0/FDT, usable RAM banks, reserved regions, FD relocation window, and UART settings.
3. Replace placeholder memory/stack/FD values only with independently verified C21Y values; add required board-specific platform drivers and boot flow.
4. Build a controlled test payload and perform a non-destructive boot test only after the handoff and recovery path are understood.
5. Verify XNU kernel entry and early boot logs. A successful EDK2 compile alone is not evidence that XNU boots.

Until these checks are complete, do not package or flash the scaffold.
