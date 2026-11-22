# C21Y stock boot DTB memory inspection

Date: 2026-11-22

Input extracted from the stock C21Y `boot.img` at offset `0x1d57040`.
The extracted FDT is valid (152,657 bytes, version 17).

## Observed base-DTB memory node

```
/memory
  device_type = "memory"
  reg = <0x00000000 0x80000000 0x00000000 0x80000000>
```

This describes one 2 GiB range:
- Base: `0x80000000`
- Size: `0x80000000`
- End (exclusive): `0x100000000`

## Observed reserved-memory entries

| Node | Base | Size | End (exclusive) |
|---|---:|---:|---:|
| ddrbist-mem | 0x80000000 | 0x1000 | 0x80001000 |
| rebootescrow | 0x81ff0000 | 0x10000 | 0x82000000 |
| audio-mem | 0x87500000 | 0x300000 | 0x87800000 |
| sipc-mem | 0x87800000 | 0x800000 | 0x88000000 |
| sp-ddr-mem | 0x88000000 | 0x300000 | 0x88300000 |
| audiodsp-mem | 0x89000000 | 0x600000 | 0x89600000 |
| cp-mem | 0x89600000 | 0x4900000 | 0x8df00000 |
| iq-mem | 0x90000000 | 0x4000000 | 0x94000000 |
| sml-mem | 0x94000000 | 0x40000 | 0x94040000 |
| tos-mem | 0x94040000 | 0x3fc0000 | 0x98000000 |
| ramoops | 0xfff80000 | 0x40000 | 0xfffc0000 |
| debug-mem | 0x100000000 | 0x1000 | 0x100001000 |
| debug-mem | 0x844c0000 | 0x4000 | 0x844c4000 |

The base DTB contains no second general-purpose RAM bank in `/memory`.
It does contain a small reserved debug range at `0x100000000`; this is
not evidence that the remainder of a second bank is usable by UEFI.

## Interpretation and safety

Separate Android runtime evidence previously showed a populated Normal zone
starting at `0x100000000`, while the stock base DTB advertises only the
first 2 GiB. The U-Boot BSP for this SoC performs dynamic DDR-size and FDT
fixups (including `fdt_fixup_ddr_size()`). Therefore this extracted base
DTB is not necessarily the final FDT handed to the kernel or firmware.

Do **not** convert the Android zone boundary into a UEFI RAM descriptor,
and do **not** advertise `0x80000000..0x180000000` as one contiguous RAM
range based only on the 4 GiB Android property. The second bank's exact
base/size and all bootloader, secure-world, modem, DSP, framebuffer, and
firmware reservations still need confirmation at the actual UEFI handoff.

## Next required evidence

1. Capture or reconstruct the final merged/fixed-up FDT after the stock
   U-Boot memory fixups, not merely the base DTB embedded in boot.img.
2. Establish the exact C21Y UEFI entry handoff and firmware relocation/
   stack/heap ranges.
3. Only then create UEFI memory descriptors and reserve every non-usable
   interval. Keep MemoryMapLib fail-closed until these are verified.

The host-side inspector is `tools/c21y-fdt-memory-inspect.py`. It reports
FDT memory and reserved-memory nodes; it intentionally does not generate
UEFI descriptors.
