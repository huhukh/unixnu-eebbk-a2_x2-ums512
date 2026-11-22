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

This is strong runtime evidence that Android manages two DRAM ranges:
approximately 2 GiB at `0x80000000` and almost 2 GiB at
`0x100000000`. Together they cover approximately 4 GiB of physical
address space, subject to holes and reservations.

Previously collected `MemTotal` was 3,875,088 kB. This is usable-memory
accounting after kernel and firmware reservations, not a firmware memory map.

The mechanism by which the second bank is supplied is still unverified.
The raw base DTB and overlay do not explain it. A bootloader-side live-FDT
fixup is plausible but not proven. Reading `/sys/firmware/fdt` and
`/proc/device-tree` from Android was blocked by permissions/SELinux in the
recorded session.

## 7. UniXNU firmware memory-map constraints

The existing EDK2 memory map under
`uefi/Platforms/Unisoc/bbkA2Pkg/Library/MemoryMapLib/MemoryMapLib.c`
belongs to EEBBK A2/X2/X2P (`ums512_1h190`), not C21Y
(`ums512_1h10`). Its BootShim, UEFI FD, stack, heaps, FDT, initrd,
modem/TEE/audio carve-outs, display and MMIO values must not be copied.

The C21Y branch still lacks a hardware-qualified C21Y EDK2 package and
MemoryMapLib. The currently selected C21Y memory-map implementation is
intentionally fail-closed/empty rather than advertising unverified RAM.

## 8. Current conclusions and next gates

Confirmed from the raw base DTB:
- UMS512 SoC identity.
- Eight-core CPU topology: six A55 and two A75.
- GICv3 register ranges and redistributor stride.
- Two enabled Unisoc UART register blocks and stock console path.
- DPU and DSI register blocks.
- Raw base memory node and the listed base reserved-memory nodes.

Confirmed from separate sources:
- Board overlay identity matches `S19610AA1`.
- Android runtime sees two populated DRAM zones spanning approximately 4 GiB.
- Overlay reserves logo, face-ID, framebuffer and writeback regions.

Still unresolved:
1. Final live FDT after bootloader fixups and overlays.
2. Exact DRAM banks and usable/reserved UEFI memory descriptors.
3. Firmware FD, BootShim, stack, heap, initrd and XNUP payload addresses.
4. GOP framebuffer base, format, stride and ownership at UEFI handoff.
5. C21Y UEFI package and actual XNU loader compatibility.

**Do not flash experimental images.** Continue read-only inspection and
prove a repeatable RAM-only loader/XNU boot before considering any partition
write. DTS compilation and CI success do not establish bootability.
