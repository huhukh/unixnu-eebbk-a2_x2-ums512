# Realme C21Y boot handoff research

Date: 2026-11-22

Target: Realme C21Y RMX3261 / S19610AA1 / Unisoc UMS512 (SharkL5Pro).

## Confirmed from the UMS512 1h10 U-Boot source

Reference repository:
- https://github.com/Veynamer/bsp_bootloader_u-boot15_sharkl5pro
- inspected revision: `eba43fa3542553a7d493edd9c1a47e423b9c5b28`

Relevant files:
- `arch/arm/include/asm/arch-sharkl5pro/chip_releted_def.h`
- `include/chipram_env.h`
- `board/spreadtrum/ums512_1h10/ums512_1h10.c`
- `common/loader/sprd_fdt_support.c`
- `common/loader/loader_common.c`

Findings:

1. SharkL5Pro defines `CHIPRAM_ENV_LOCATION = 0x82000000`.
2. The handoff structure contains `cs_number`, `cs0_size`, and `cs1_size`.
3. With `CONFIG_DDR_AUTO_DETECT`, `dram_init()` sums the chip-select sizes into `real_ram_size` (one or two chip selects).
4. `fdt_fixup_ddr_size()` replaces the `/memory/reg` property using `CONFIG_SYS_SDRAM_BASE` and `get_real_ram_size()`.
5. `loader_common.c` calls `fdt_fixup_ddr_size()` as part of the kernel FDT fixup path.
6. The reference board config sets `CONFIG_SYS_SDRAM_BASE = 0x80000000`.

This is strong evidence that the 2 GiB `/memory/reg` in the raw C21Y base DTB is not necessarily the final memory description passed to Linux. The bootloader dynamically rewrites it from the DDR training handoff.

## Cross-check against this C21Y unit

Previously collected device observations:
- `ro.boot.ddrsize=4096M`
- `ro.boot.ddrsize.range=[4096,5120)`
- Android memory zones: DMA starts at PFN 524288 (0x80000000), Normal starts at PFN 1048576 (0x100000000).
- Raw boot DTB `/memory/reg`: base 0x80000000, size 0x80000000 (2 GiB).
- Raw DTB has vendor reserved-memory nodes; DTBO adds additional display/face/writeback reservations.

The zone boundary at 0x100000000 is adjacent to the first 2 GiB range. Together with the 4096M boot property, this is consistent with 4 GiB of contiguous DRAM beginning at 0x80000000, but does NOT by itself prove the complete usable UEFI map or the exact reservations.

## Important safety conclusions

- Do not read `0x82000000` as a live chipram structure from UEFI without proving its lifetime. It is a boot-stage handoff address and may be reused by the bootloader for the merged FDT.
- Do not copy the EEBBK A2 `ums512_1h190` memory descriptors into C21Y `ums512_1h10`.
- Do not advertise all of `[0x80000000, 0x180000000)` as free RAM. Secure-world, modem, DSP, framebuffer, bootloader, and firmware reservations must be excluded.
- Do not treat the raw base DTB as the final live FDT.
- The current C21Y `MemoryMapLib` intentionally remains empty until the final live FDT and bootloader handoff are captured.

## Next engineering task

Trace the exact C21Y boot path in the stock U-Boot binary and establish:
1. the actual kernel/BootShim entry address and register ABI;
2. the address and lifetime of the final merged FDT;
3. the final `/memory/reg` and every `/reserved-memory` range after all bootloader fixups;
4. the firmware relocation/stack/heap window that is safe before UEFI memory services start.

Only after those are known should the C21Y UEFI memory descriptors and FD/stack addresses be implemented.

## Separate iOS version mismatch

The current root `board.toml` selects `ipados-17.7.11-21H461`. The stated target for this project is iOS 16. That OS-profile mismatch must be resolved with an explicit iOS 16 profile (matching XNU 8796 and its ABI inputs) before claiming an iOS 16 kernel build. It is intentionally not changed in this research-only commit.
