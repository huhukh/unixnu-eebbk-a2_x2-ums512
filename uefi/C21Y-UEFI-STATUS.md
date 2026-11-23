# Realme C21Y UEFI port status

## What exists
- Separate EDK2 platform package: `Platforms/Unisoc/c21yPkg`.
- Separate C21Y memory-map library, currently **fail-closed and empty**. It advertises no RAM to UEFI because the live FDT alone does not establish firmware-owned ranges, the FD relocation window, or safe stack/heap placement.
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

Static AArch64 disassembly of the stock `u-boot-sign.bin` traces the
normal U-Boot image-preparation path through a fixup group that calls code
which finds `/memory` and writes `reg` using the global RAM-size value.
The U-Boot and FDL2 DHTB code payloads are byte-identical, but this does not
mean the FDL2 download stage executes in normal boot. A separate code body
reads a magic and size-count fields from `0x82000000`, consistent with
chipram DDR metadata; its exact ABI and init-table invocation remain unproven.

The captured live FDT's `/memory/reg` matches this fixup mechanism. The
mechanism is now evidenced in the U-Boot image; exact FD/stack/heap placement,
firmware ownership, and a safe UEFI map are still unresolved.

Do not infer a UEFI memory map from the live `/memory/reg` alone. Firmware,
secure-world, modem/DSP, bootloader, and relocation ownership still need to be
reconciled with the exact UEFI handoff.

## Platform integration audit

The C21Y DSC/FDF are still a compile scaffold:
- `PcdCPUCoresStackBase=0x80480000` and size `0x40000` remain unverified.
- `C21Y_FD_BASE` is required from measurement; no safe value is established.
- The FDF does not include GOP, SDHCI/eMMC DXE, UniXNU.efi, or DarwinBoot.
- Shared UMS512 PCDs provide GICv3 and timer settings; their runtime operation
  and PSCI CPU-on behavior are not qualified on C21Y.
- `SprdDebugSerialPortLib` assumes inherited UART setup and contains an
  A2-specific 1200x1920 framebuffer path at `0x9e000000`; C21Y's live tree
  instead lists the panel framebuffer at `0xfd708000`. This is not a
  validated C21Y display/log path.
- The shared GOP driver targets the A2/X2 1200x1920 panel and is absent from
  the C21Y FV. The C21Y panel is 720x1600 and needs its own measured GOP data.

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

The C21Y DSC still sets `PcdCPUCoresStackBase` to `0x80480000`; this is unverified. The shared UMS512 header also contains `FD_BASE=0x80800000`, while the C21Y build script requires an externally measured `C21Y_FD_BASE`. Do not treat either address as validated or package/flash the scaffold.

## Next milestones
1. Trace how the chipram size metadata is initialized, then establish the exact C21Y cboot load and FDT handoff contract.
2. Build a C21Y memory HOB/DXE heap layout from verified ranges only.
3. Add board-specific platform initialization and boot flow.
4. Build a controlled test payload and perform a non-destructive boot test only after the handoff and recovery path are understood.
5. Verify XNU kernel entry and early boot logs.
