# Progres Port XNU — Realme C21Y (RMX3261 / UMS512 T610)

> File ini di-update tiap ada info/progres baru. Ringkas saja.
> Terakhir update: 2026-11-24 (UTC).

## Status Sekarang

- **Build #126** (`45385291507`) — **SEDANG BERJALAN**
  - Commit: `100a64ccee1d153b2baa7432a47a2b5877f09ed6` (merge PR #2)
  - EDK2 job: **sukses**
  - XNU job: masih step 16 "Build Linux XNU toolchain" (lama)
  - Step 13 (patch), 14 (config), 15 (DTS): **sukses**
  - Step 17 "Build native XNU kernel": **belum** — ini tes utama (tempat Build #124 gagal)
- Build #127 (redundan, commit progres.md) sudah **dibatalkan**.

## Info Hardware Baru (dari HP via ADB, read-only, 2026-11-24)

- HP terhubung: serial `1804093810BA06J3`, RMX3261, Android 11, kernel 4.14.193.
- **Bootloader unlocked** (`verifiedbootstate=orange`, `flash.locked=0`).
- **Root tersedia via Magisk**: `/system_ext/bin/su` -> `su -c id` = uid=0.
- **MEMORY (kunci yang dulu belum pasti):**
  - `/memory/reg` live = base **0x80000000**, size **0xFFFFF000** (~4 GiB) -> **konflik 2GB vs 4GB SELESAI**.
  - `ddrsize=4096M`, range `[4096,5120)`.
  - `/proc/iomem`: `80000000-81feffff` RAM, `81ff0000-81ffffff` reserved (`namespace0.0`/rebootescrow), `82000000-17fffefff` RAM.
  - Kernel code `0x80080000`, data `0x812c0000`; initrd `0x82100000-0x82a03d10`.
  - Reserved-memory (16 node): ddrbist@80000000, rebootescrow@81ff0000, audio@87500000, sipc@87800000, sp-ddr@88000000, audiodsp@89000000, cp-mem@89600000, sml@94000000, tos@94060000, logobuffer@9e000000, faceid@efaae000, framebuffer@fd708000, writeback@ff562000, ramoops@fff80000, debug@100000000, debug@844c0000.
- **GICv3**: GICD `0x12000000`+`0x20000`, GICR `0x12040000`+`0x100000` (dari live FDT).
- **PSCI 0.2 (smc)**; CPU: 6x Cortex-A55 (`cpu@0..500`) + 2x Cortex-A75 (`cpu@600..700`), MPIDR 0x0..0x700.
- Timer: `arm,armv8-timer`. Console: `ttyS1` @ `0x70100000` (stdout-path `/soc/ap-apb/serial@70100000`).
- Boot storage: eMMC `mmcblk0` (~58.2 GiB) via `71400000.sdio`. A/B slot, aktif `_a`.
- Partisi penting: boot_a=p40(64M), vendor_boot_a=p42(100M), dtb_a=p44(8M), dtbo_a=p46(8M), super=p48(~8.6G), vbmeta_a=p54, uboot_a=p8, trustos_a=p4, sml_a=p6.

## Yang Sudah Selesai

- Root cause Build #124 `Parse failure` = `unifdef 2.10` (Ubuntu 22.04) menolak 2 header XNU 8796 saat `installhdrs`.
- Patch `patches/xnu/8796-unifdef-headers.patch` dibuat; blob hash cocok persis.
- `patches/xnu/series` diperbarui (patch sebelum `sdhci-block-personality.patch`).
- Mekanisme patch terverifikasi (`board.toml` `[kernel] patch_series` + `patches.py` `git apply`).
- PR #2 di-merge ke `port/realme-c21y-rmx3261`.
- **Memory map & reserved regions C21Y sudah dibuktikan dari device live.**
- `docs/HARDWARE_EVIDENCE.md`, `PROJECT_STATE.md` diperbarui dengan data device.

## Yang Belum / Risiko

- Kernel ARM64 belum terbukti terkompilasi sampai step 17 sukses + `kernel.macho` ada.
- **MemoryMapLib tetap fail-closed** — layout RAM sudah terbukti, tapi handoff (FDT pointer/lifetime, ownership, stack/heap, FD & payload window) belum.
- Boot XNU di HP belum dicoba/diklaim.
- Defconfig/DTS/UEFI belum diubah ke data baru.
- Kompilasi sukses != boot sukses != hardware didukung.

## Log

- 2026-11-24 ~11:33 UTC: PR #2 merged -> Build #126 mulai (EDK2 sukses, XNU jalan).
- 2026-11-24: XNU step 13-15 sukses (patch/config/DTS), masuk step 16 (toolchain).
- 2026-11-24: commit `progres.md` (d1ef1f4) memicu Build #127 -> dibatalkan.
- 2026-11-24: ADB read-only ke HP (root Magisk) -> ambil memory map, GIC, PSCI, CPU, partisi, FDT.
