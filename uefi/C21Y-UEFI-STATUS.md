# Realme C21Y UEFI port status

## What exists
- Separate EDK2 platform package: `Platforms/Unisoc/c21yPkg`.
- Separate C21Y memory-map library, currently **fail-closed and empty**. It advertises no RAM to UEFI because the C21Y live FDT, firmware-owned ranges, and relocation window are not established.
- Separate C21Y boot configuration and build script.
- UMS512 SoC-wide GIC/timer/UART definitions reused from the shared UMS512 package.
- CI performs an EDK2 firmware-volume compile for the C21Y scaffold.

## Memory-map correction (2026-11-22)
The previous C21Y `MemoryMapLib.c` contained several carve-out addresses copied from the EEBBK A2 / X2 / X2P (`ums512_1h190`) map. They are not verified C21Y (`ums512_1h10`) reservations and have been removed.

The library now returns a null descriptor pointer and a descriptor count of zero. This is intentionally non-functional: it prevents the UEFI allocator from treating guessed ranges as safe RAM. It may cause memory initialization to stop or fail if executed; that is preferable to silently allocating over modem, secure-world, framebuffer, or firmware-owned memory. The package is still a compile scaffold, not a bootable firmware.

C21Y-specific stock evidence currently confirms:
- Base DTB memory node: 2 GiB at `0x80000000`.
- Android runtime zoneinfo: a second populated region starts at `0x100000000`, with almost 2 GiB spanned.
- DTBO reservations include logo buffer, Face ID, framebuffer, and writeback regions.
- The bootloader appears to perform dynamic FDT/memory fixups, but the final live FDT and exact UEFI handoff have not been captured.

Do not infer a UEFI memory map from the raw base DTB, Android zones, or EEBBK carve-outs alone.

## Validation completed
The latest previously recorded EDK2 CI run compiled the firmware-volume scaffold and structurally validated the generated FV. That run predates this memory-map correction; a new CI run must pass before this revision is considered build-checked.

A successful EDK2 compile only proves the package can be compiled. It does not prove SEC/DXE executes on the phone or that XNU boots.

## Explicitly not bootable / not flashable
The following remain unknown:
- actual cboot kernel-field load address;
- x0/FDT handoff address and live merged FDT;
- all usable DRAM banks and bootloader/secure-world/modem/DSP reservations;
- safe FD relocation window and stack/heap placement;
- UART settings at the firmware handoff.

The previous `0x80800000` FD base and `0x80480000` stack values remain unverified placeholders. Do not package or flash the scaffold.

## Next milestones
1. Establish the C21Y cboot handoff contract from stock firmware evidence.
2. Build a C21Y memory HOB/DXE heap layout from verified ranges only.
3. Add board-specific platform initialization and boot flow.
4. Build a controlled test payload and perform a non-destructive boot test only after the handoff and recovery path are understood.
5. Verify XNU kernel entry and early boot logs.
