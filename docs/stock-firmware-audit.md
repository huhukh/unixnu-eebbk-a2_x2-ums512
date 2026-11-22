# Stock firmware audit — Realme C21Y RMX3261

Date: 2026-11-22

This document records observations from the user's stock `boot.img`,
`stock_boot_dtb.dtb`, and `dtbo.img`. It is an audit, not a bootability
claim. No firmware image was modified or flashed.

## Verified image layout

- `boot.img` is an Android boot image, header version 2, page size 2048.
- Its header reports a DTB payload size of 152721 bytes.
- The payload at the computed DTB offset is a one-entry Android DT table
  (`0xd7b7ab1e`), containing one FDT blob of 152657 bytes.
- That embedded FDT matches the first 152657 bytes of the supplied
  `stock_boot_dtb.dtb`; the supplied file has 64 trailing zero-padding bytes.
- The separate `dtbo.img` is an Android DT table with one entry:
  payload size 54899 bytes, payload offset 64.

## Board identity

The sole overlay in `dtbo.img` identifies itself as:

- model: `Unisoc UMS512 1H10 board`
- compatible: `sprd,S19610AA1`
- sc-id: `ums512 1h10 1000`

The device's previously collected hardware ID is `S19610AA1`. This is a
strong board-identity match for the Realme C21Y unit under investigation.

## Base DTB observations

- SoC model: `Unisoc UMS512 SoC`
- SoC compatible: `sprd,ums512`
- UART node at `0x70100000` is enabled; the chosen stdout path points to it.
- Boot arguments include `earlycon=sprd_serial,0x70100000,115200n8` and
  `console=ttyS1,115200n8`.
- The base tree has one node with `device_type = "memory"`:
  `reg = <0x0 0x80000000 0x0 0x80000000>`, i.e. a 2 GiB range beginning at
  physical address 0x80000000.
- The base tree also contains a reserved-memory entry at
  `0x100000000` (4 GiB boundary).

## Board overlay observations

The overlay has fixups against symbols in the base DTB and multiple fragments.
It adds board-specific nodes and settings for, among other things, GPIO/pinctrl,
thermal zones, camera sensors, audio codec, charger, NFC, touch, Wi-Fi and
display-panel alternatives.

The overlay's reserved-memory fragment adds these regions:

| Region | Address | Size |
|---|---:|---:|
| Logo buffer | 0x9e000000 | 0x9e4000 |
| Face ID | 0xefaae000 | 0x500000 |
| Framebuffer | 0xfd708000 | 0x1e5a000 |
| Writeback | 0xff562000 | 0xa1e000 |

The overlay does not contain a memory-node update that explains a larger DRAM
map.

## Runtime memory-map evidence (ADB, 2026-11-22)

The user collected `/proc/zoneinfo` from the running stock Android kernel.
It reports two populated zones with distinct physical PFN ranges (4 KiB pages):

| Zone | start_pfn | spanned pages | Physical start | Span | present pages |
|---|---:|---:|---:|---:|---:|
| DMA | 524288 | 524288 | 0x80000000 (2 GiB) | 2 GiB | 524272 |
| Normal | 1048576 | 524287 | 0x100000000 (4 GiB) | almost 2 GiB | 524287 |

This is strong runtime evidence for two adjacent RAM banks: approximately
2 GiB at 0x80000000 followed immediately by approximately 2 GiB at
0x100000000. Together they span approximately 4 GiB from 0x80000000 through
0x17fffffff, subject to the small holes/reservations indicated by `present`.

`MemTotal` is 3,875,088 kB. Summing the populated zone `managed` counts
(462801 + 505971 pages) gives 968772 pages, approximately 3.69 GiB, consistent
with the userspace report after firmware/kernel reservations.

This resolves the apparent 2 GiB vs 3.7 GiB discrepancy at the level of the
running kernel's zone layout: the base DTB memory node describes the first
bank, while the running kernel also manages a second bank beginning at 4 GiB.
The mechanism by which the second bank is supplied (bootloader memory fixup,
platform code, or another handoff path) is still unverified. `/proc/cmdline`,
`/proc/buddyinfo`, and kernel log access were denied or unavailable in this
ADB session. Do not encode a guessed contiguous memory range; inspect the
actual boot handoff and UniXNU memory discovery path before final DTS changes.

## Safety and next work

- Do not flash the minimal DTS output or any experimental WDT loader.
- The overlay has external and local phandle fixups. A proper merged tree must
  be produced with a real DT overlay implementation (for example
  `fdtoverlay`) before treating the combined hardware description as final.
- Current GitHub Actions success validates configuration resolution and DTS
  compilation only. It does not validate a complete kernel, UEFI handoff,
  storage, display, input, power management, or bootability.


## UniXNU firmware memory-map audit

The repository's existing EDK2 memory map is implemented in
`uefi/Platforms/Unisoc/bbkA2Pkg/Library/MemoryMapLib/MemoryMapLib.c`.
It is explicitly for the EEBBK A2 / X2 / X2P board (`ums512_1h190`), not
the C21Y (`ums512_1h10`). It hard-codes that board's BootShim, UEFI FD,
stacks, SEC/DXE heaps, FDT, initrd, modem/TEE/audio carve-outs, display buffer,
and peripheral MMIO regions. Its addresses and assumptions must not be copied
into a C21Y package.

The C21Y branch does not yet contain a C21Y-specific EDK2 platform package or
`MemoryMapLib`. The current C21Y DTS is intentionally a host-build skeleton,
and the current successful GitHub Actions job does not build or run UEFI.

The UniXNU device-tree documentation describes a single enabled memory node
for a contiguous DRAM range, while its payload/DarwinBoot handoff separately
supports excluded ranges for gaps between DRAM banks and firmware-owned
memory. The Android runtime PFN evidence suggests the two C21Y banks are
adjacent, but this alone does not identify the exact UEFI usable/reserved map.
Before creating a C21Y `MemoryMapLib`, we still need to establish the actual
bootloader load addresses, firmware handoff address, initrd location, and
every reserved region from the merged stock FDT and vendor boot chain.

### Immediate implementation constraints

- Keep the C21Y DTS memory node unchanged until the merged DTB and runtime
  handoff are reconciled.
- Do not reuse EEBBK `FD_BASE`, `FD_SIZE`, stack, heap, initrd, or framebuffer
  addresses.
- A future C21Y UEFI map must distinguish usable conventional RAM from
  bootloader, firmware, secure-world, modem/DSP, framebuffer, ramoops, and
  initrd reservations.
- The two populated Android zones are evidence for physical DRAM coverage,
  not a ready-to-use UEFI descriptor table.
