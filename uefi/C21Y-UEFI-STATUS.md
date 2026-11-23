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

C21Y-specific evidence now includes a read-only capture of the live FDT
exposed by the running Android kernel:
- Base DTB `/memory/reg`: 2 GiB at `0x80000000`.
- Live FDT `/memory/reg`: one range `0x80000000 + 0xfffff000`, ending at
  `0x17fffff000` exclusive (4 GiB minus 4 KiB).
- Live FDT v17, 283729 bytes; SHA-256
  `085ef7c0f9d2b7072466868ef1cd6456e1fcc77e23f058fea13449ccdbd62c83`.
- The live `/reserved-memory` includes board display reservations plus
  audio, CP, TEE/SML, ramoops, and debug ranges. Its entries differ from the
  raw base DTB in some places; see `docs/stock-firmware-audit.md`.
- Android previously reported DMA and Normal Linux zones beginning at
  `0x80000000` and `0x100000000`. The live FDT describes one large range,
  so the 4 GiB split is consistent with a Linux zone boundary and does not
  establish two physical DRAM banks.

The live FDT proves that the tree used by the running Android kernel contains
a memory-size change from the base DTB. This supports a boot-chain FDT fixup,
but does not identify the component that performed it; FDL2 strings alone do
not prove that FDL2 participates in the normal boot path.

Do not infer a UEFI memory map from the live `/memory/reg` alone. Firmware,
secure-world, modem/DSP, bootloader, and relocation ownership still need to be
reconciled with the exact UEFI handoff.

## Validation completed
The latest previously recorded EDK2 CI run compiled the firmware-volume scaffold and structurally validated the generated FV. That run predates this memory-map correction; a new CI run must pass before this revision is considered build-checked.

A successful EDK2 compile only proves the package can be compiled. It does not prove SEC/DXE executes on the phone or that XNU boots.

## Explicitly not bootable / not flashable
The following remain unknown:
- actual cboot kernel-field load address;
- x0/FDT handoff address (the running Android kernel's live FDT content is captured, but its handoff pointer/address is not);
- all usable DRAM banks and bootloader/secure-world/modem/DSP reservations;
- safe FD relocation window and stack/heap placement;
- UART settings at the firmware handoff.

The previous `0x80800000` FD base and `0x80480000` stack values remain unverified placeholders. Do not package or flash the scaffold.

## Next milestones
1. Establish the C21Y cboot handoff contract and identify which boot-chain stage performs the live FDT memory-size fixup.
2. Build a C21Y memory HOB/DXE heap layout from verified ranges only.
3. Add board-specific platform initialization and boot flow.
4. Build a controlled test payload and perform a non-destructive boot test only after the handoff and recovery path are understood.
5. Verify XNU kernel entry and early boot logs.
