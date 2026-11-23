# Stock firmware audit — Realme C21Y RMX3261

Date: 2026-11-22

This document records observations from the user's stock `boot.img`,
embedded base DTB, separate `dtbo.img`, and runtime Android inspection.
It is an audit, not a bootability claim. No firmware image was modified or
flashed.

## 1. Image layout and board identity

- The stock `boot.img` contains an Android boot image with an embedded DTB
  payload. The extracted FDT is 152657 bytes and reports FDT version 17.
- The extracted base DTB was parsed successfully from
  `E:\\Alat flash\\c21y-port\\c21y-stock.dtb`.
- The separate `dtbo.img` was previously inspected as an Android DT table
  with one overlay entry at payload offset 64.
- The overlay identifies itself as:
  - model: `Unisoc UMS512 1H10 board`
  - compatible: `sprd,S19610AA1`
  - sc-id: `ums512 1h10 1000`
- The device's collected hardware ID is `S19610AA1`, matching the overlay.

## 2. Base DTB — directly parsed values

Root:
- model: `Unisoc UMS512 SoC`
- compatible: `sprd,ums512`
- `#address-cells = 2`, `#size-cells = 2`

### CPU topology

The parsed `/cpus` nodes identify eight ARMv8 CPUs:

| MPIDR / node | CPU |
|---|---|
| `0x000` / `cpu@0` | Cortex-A55 |
| `0x100` / `cpu@100` | Cortex-A55 |
| `0x200` / `cpu@200` | Cortex-A55 |
| `0x300` / `cpu@300` | Cortex-A55 |
| `0x400` / `cpu@400` | Cortex-A55 |
| `0x500` / `cpu@500` | Cortex-A55 |
| `0x600` / `cpu@600` | Cortex-A75 |
| `0x700` / `cpu@700` | Cortex-A75 |

All CPU nodes use `enable-method = "psci"`. This confirms the static DTB
CPU topology; runtime PSCI behavior and CPU start-up from a new loader remain
to be tested.

### GICv3

Parsed node: `/interrupt-controller@12000000`

| Register block | Base | Size |
|---|---:|---:|
| GIC Distributor (GICD) | `0x12000000` | `0x20000` |
| GIC Redistributor (GICR) | `0x12040000` | `0x100000` |

- Redistributor stride: `0x20000`
- `#redistributor-regions = 1`
- Compatible: `arm,gic-v3`

These are base-DTB register ranges, not proof that an experimental XNU
interrupt controller implementation is already functional.

### UART

| Node | Base | Size | Status |
|---|---:|---:|---|
| `serial@70000000` | `0x70000000` | `0x100` | okay |
| `serial@70100000` | `0x70100000` | `0x100` | okay |

The `/chosen/stdout-path` is
`/soc/ap-apb/serial@70100000`. Boot arguments specify
`earlycon=sprd_serial,0x70100000,115200n8` and
`console=ttyS1,115200n8`. This makes `0x70100000` the stock console
candidate. The UART is Spreadtrum/Unisoc-specific, not assumed to be PL011;
loader UART compatibility must be checked.

### Display controller

| Node | Base | Size | Compatible |
|---|---:|---:|---|
| DPU `dpu@20300000` | `0x20300000` | `0x1000` | `sprd,display-processor` |
| DSI `dsi@20400000` | `0x20400000` | `0x1000` | `sprd,dsi-host` |

Both nodes are marked `okay`. The DSI node references a
`sprd,generic-mipi-panel`. This identifies controller register blocks;
it does not establish UEFI GOP support or the framebuffer's live address,
pixel format, stride or ownership.

## 3. Base DTB memory description

The base DTB has one `device_type = "memory"` node:

```
reg = <0x0 0x80000000 0x0 0x80000000>
```

Therefore the raw base DTB describes a 2 GiB range beginning at physical
address `0x80000000`, ending at `0x100000000` (exclusive).

This is the raw/static DTB result, not necessarily the final memory map
handed to the kernel by the bootloader.

## 4. Base DTB reserved-memory nodes

The parser reported these entries in `/reserved-memory`:

| Region | Address | Size |
|---|---:|---:|
| DDRBIST | `0x80000000` | `0x1000` |
| Reboot escrow | `0x81FF0000` | `0x10000` |
| Audio | `0x87500000` | `0x300000` |
| SIPC | `0x87800000` | `0x800000` |
| SP DDR | `0x88000000` | `0x300000` |
| Audio DSP | `0x89000000` | `0x600000` |
| CP memory | `0x89600000` | `0x4900000` |
| IQ memory | `0x90000000` | `0x4000000` |
| SML | `0x94000000` | `0x40000` |
| TOS | `0x94040000` | `0x3FC0000` |
| Ramoops | `0xFFF80000` | `0x40000` |
| Debug memory | `0x100000000` | `0x1000` |
| Debug memory | `0x844C0000` | `0x4000` |

The table is limited to nodes present in the raw base DTB. It is not a
complete list of firmware-owned memory after the board overlay and runtime
bootloader fixups.

## 5. Board overlay reserved-memory observations

The board overlay adds these regions:

| Region | Address | Size |
|---|---:|---:|
| Logo buffer | `0x9E000000` | `0x9E4000` |
| Face ID | `0xEFAAE000` | `0x500000` |
| Framebuffer | `0xFD708000` | `0x1E5A000` |
| Writeback | `0xFF562000` | `0xA1E000` |

The overlay also contains board-specific fragments and fixups for GPIO/pinctrl,
thermal zones, camera, audio, charger, NFC, touch, Wi-Fi and display-panel
alternatives. A fully merged FDT must be generated with a real overlay
implementation before treating all base/overlay phandles and nodes as one
final tree.

The overlay does not add a second memory node or explain the larger DRAM map.

## 6. Runtime Android memory evidence

Previously collected `/proc/zoneinfo` from the running stock Android kernel
reported two populated zones (4 KiB pages):

| Zone | start_pfn | spanned pages | Physical start | Span | present pages |
|---|---:|---:|---:|---:|---:|
| DMA | 524288 | 524288 | `0x80000000` | 2 GiB | 524272 |
| Normal | 1048576 | 524287 | `0x100000000` | almost 2 GiB | 524287 |

This is runtime evidence for two populated Linux zones, not proof of two
separate physical DRAM banks. The live FDT captured below describes one large
range and is consistent with a Linux zone boundary at 4 GiB.

Previously collected `MemTotal` was 3,875,088 kB. This is usable-memory
accounting after kernel and firmware reservations, not a firmware memory map.

## 7. Live FDT from the running stock device

On 2026-11-23, the FDT exposed by the running Android kernel at
`/sys/firmware/fdt` was captured through ADB using a read-only root command.
The blob parses as FDT v17, totalsize 283729 bytes, SHA-256
`085ef7c0f9d2b7072466868ef1cd6456e1fcc77e23f058fea13449ccdbd62c83`.
The connected device reported model `RMX3261`, hardware ID `S19610AA1`,
Android 11, and Linux `4.14.193`.

The live tree's `/memory/reg` is:

```
base = 0x80000000
size = 0xfffff000
end  = 0x17fffff000 (exclusive)
```

This is one described range of 4 GiB minus 4 KiB, starting at 2 GiB and
ending just below 6 GiB. The raw base DTB described only
`0x80000000 + 0x80000000`. The live FDT therefore directly proves that the
tree used by the running Android kernel contains a larger memory description.
Together with the previously audited base DTB and overlay, this is strong
evidence of a live boot-chain FDT/memory fixup. It does not identify which
boot-chain component performed it.

The captured live `/reserved-memory` tree reports:

| Region | Address | Size |
|---|---:|---:|
| DDRBIST | `0x80000000` | `0x1000` |
| Debug memory | `0x844c0000` | `0x4000` |
| Reboot escrow | `0x81ff0000` | `0x10000` |
| Audio | `0x87500000` | `0x300000` |
| SIPC | `0x87800000` | `0x800000` |
| SP DDR | `0x88000000` | `0x300000` |
| Audio DSP | `0x89000000` | `0x600000` |
| CP | `0x89600000` | `0x4900000` |
| SML | `0x94000000` | `0x40000` |
| TOS | `0x94060000` | `0x4fa0000` |
| Logo buffer | `0x9e000000` | `0x9e4000` |
| Face ID | `0xefaae000` | `0x500000` |
| Framebuffer | `0xfd708000` | `0x1e5a000` |
| Writeback | `0xff562000` | `0xa1e000` |
| Ramoops | `0xfff80000` | `0x40000` |
| Debug memory | `0x100000000` | `0x1000` |

The live tree does not contain the base-DTB `iq-mem@90000000` node, and the
TOS `reg` differs from the base tree. Do not infer that omitted ranges are
available to UEFI; reconcile the live tree with firmware ownership and the
actual handoff before building descriptors.

### U-Boot static disassembly evidence

The signed `u-boot-sign.bin` and `fdl2-sign.bin` files both have a DHTB
header and a `0xd8a30`-byte payload starting at file offset `0x200`.
Their headers and code payloads are byte-identical; the payload SHA-256 is
`7436c1bf6ee9bb04c95ae7f521d0f0f0f5c57d8fb8125698e717719273c7e235`.
The 692-byte signature trailers differ. The U-Boot file SHA-256 is
`37e01de6b0d87df33ba1e4258b54bf6a6d71805c2da606d949383cfaf22d2f5d`;
the FDL2 file SHA-256 is
`c1dbff5b6f1d8c91ae3f8e4ae59df54a0bfc35611b5fb60b72c8dcd4a1cd2922`.
The payload disassembles as AArch64. Offsets below are relative to the start
of that DHTB payload, not physical load addresses.

The normal U-Boot image-preparation path at payload offset `0x1f114`
passes its FDT pointer to the fixup group at `0x1cb74`. That group calls the
routine at `0x2162c`. Its instructions:
- read a 64-bit RAM-size value through helper `0x3460`;
- find the `/memory` node and its `reg` property;
- set the first 8-byte cell to the big-endian encoding of base
  `0x80000000`;
- append the big-endian 64-bit RAM size to `reg`.

The relevant property helpers at `0x69110` and `0x69164` were also
disassembled: the first replaces the property data and the second grows it
and appends data. This code path matches the captured live FDT's one-range
`/memory/reg` and is direct evidence that normal U-Boot image preparation
updates the memory description. It still does not establish U-Boot's load
address or make that whole range safe for UEFI allocation.

A separate code body at payload offset `0x34a0` checks a magic value at
`0x82000000`, reads a count at offset `+0x20`, and on count 1 or 2 reads
64-bit values at `+0x28` and optionally `+0x30`, summing the latter case
before storing the result to the global later read by helper `0x3460`.
This layout is consistent with chipram DDR/CS metadata, but the field names
and its init-table invocation have not been independently proven. Treat that
interpretation as a strong lead, not a resolved ABI.



A follow-up byte-aligned AArch64 sweep of the U-Boot payload found no direct
`BL`/`B` instruction targeting `0x34a0` and no literal 32/64-bit payload pointer
`0x34a0`. This does not exclude an indirect callback/init-table path, and it is
not proof that the parser is dead code. The routine's invocation and the
producer of the global RAM-size value therefore remain unresolved. The next
static-analysis gate is to trace the initialization/callback tables and all
writes to that global, then match the result to the normal boot path.

Although the FDL2 and U-Boot code payloads match exactly, this does not mean
the download-loader stage runs during a normal phone boot. The normal-boot
evidence comes from the `u-boot-sign.bin` image and its traced U-Boot
image-preparation call path. The live FDT confirms the resulting memory
description; no firmware was executed or modified during this analysis.



## 8. C21Y EDK2 platform integration audit

The local C21Y DSC/FDF and shared UMS512 package were inspected read-only:
- `c21y.dsc` sets `PcdSystemMemoryBase=0x80000000`, matching the live
  FDT range start, but still hard-codes `PcdCPUCoresStackBase=0x80480000`
  with a `0x40000` primary stack. That stack address is unverified.
- `build-c21y.sh` requires `C21Y_FD_BASE` from a measured cboot address.
  The FDF's size defaults are build conveniences, not measured placement.
- The C21Y DSC/FDF include SEC, RamManagerDxe, DtPlatformDxe and reset support.
  They do not include the shared GOP, SDHCI/eMMC DXE driver, UniXNU application,
  or DarwinBoot/XNU loader. A compiled FV would not yet launch XNU or provide
  these devices.
- The shared UMS512 DSC include sets GICv3 PCDs to `0x12000000` and
  `0x12040000`, timer interrupts to 13/14/11/10, and selects
  `SprdDebugSerialPortLib`. These match static stock-tree data where noted,
  but GIC, PSCI CPU-on, timer events, and UART handoff have not been validated
  by this EDK2 build on C21Y. The C21Y FDT's `enable-method = "psci"` is not
  proof that a new firmware's PSCI calls work.
- The serial library does not reprogram the UART clock/baud and also contains
  a debug framebuffer path hard-coded for 1200x1920 at `0x9e000000`.
  C21Y's panel is 720x1600 and the live FDT separately reserves its framebuffer
  at `0xfd708000`. The inherited framebuffer path is not a qualified C21Y
  console; its writes must not be treated as visible logging.
- The shared GOP driver is for the 1200x1920 HIMAX8279/BOE tablet panel and is
  not included in the C21Y FV. C21Y needs its own panel geometry, buffer,
  stride, and pixel-format validation before GOP can be added.

This audit is a static configuration review only; no EDK2 image was booted.
Until FD/stack placement and the C21Y display/storage/XNU handoff are proven,
the C21Y FV remains a compile scaffold.

## 9. UniXNU firmware memory-map constraints

The existing EDK2 memory map under
`uefi/Platforms/Unisoc/bbkA2Pkg/Library/MemoryMapLib/MemoryMapLib.c`
belongs to EEBBK A2/X2/X2P (`ums512_1h190`), not C21Y
(`ums512_1h10`). Its BootShim, UEFI FD, stack, heaps, FDT, initrd,
modem/TEE/audio carve-outs, display and MMIO values must not be copied.

The C21Y branch still lacks a hardware-qualified C21Y EDK2 package and
MemoryMapLib. The currently selected C21Y memory-map implementation is
intentionally fail-closed/empty rather than advertising unverified RAM.

## 10. Current conclusions and next gates

Confirmed from the raw base DTB:
- UMS512 SoC identity.
- Eight-core CPU topology: six A55 and two A75.
- GICv3 register ranges and redistributor stride.
- Two enabled Unisoc UART register blocks and stock console path.
- DPU and DSI register blocks.
- Raw base memory node and the listed base reserved-memory nodes.

Confirmed from separate sources:
- Board overlay identity matches `S19610AA1`.
- Android runtime reports two Linux zones, while the captured live FDT describes one large range spanning nearly 4 GiB.
- Overlay reserves logo, face-ID, framebuffer and writeback regions.

Still unresolved:
1. Which boot-chain stage performs the memory-size/FDT fixup.
2. Usable/reserved UEFI descriptors, including firmware-owned ranges and relocation windows.
3. Firmware FD, BootShim, stack, heap, initrd and XNUP payload addresses.
4. GOP framebuffer base, format, stride and ownership at UEFI handoff.
5. C21Y UEFI package and actual XNU loader compatibility.

**Do not flash experimental images.** Continue read-only inspection and
prove a repeatable RAM-only loader/XNU boot before considering any partition
write. DTS compilation and CI success do not establish bootability.
