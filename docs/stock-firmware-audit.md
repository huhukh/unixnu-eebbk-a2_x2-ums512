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

## Important unresolved issue

The Android userspace report collected earlier showed approximately 3.7 GiB
of total RAM, while the base DTB memory node describes only 2 GiB. These
observations do not reconcile yet. Possible boot-chain/runtime memory fixups
must be investigated; no 4 GiB DRAM range should be invented or committed
until the effective runtime memory map is verified.

## Safety and next work

- Do not flash the minimal DTS output or any experimental WDT loader.
- The overlay has external and local phandle fixups. A proper merged tree must
  be produced with a real DT overlay implementation (for example
  `fdtoverlay`) before treating the combined hardware description as final.
- Current GitHub Actions success validates configuration resolution and DTS
  compilation only. It does not validate a complete kernel, UEFI handoff,
  storage, display, input, power management, or bootability.
