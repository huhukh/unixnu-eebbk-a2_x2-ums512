# Progres Port XNU — Realme C21Y (RMX3261 / UMS512 T610)

> File ini di-update tiap ada info/progres baru. Ringkas saja.
> Terakhir update: 2026-11-24 (UTC).

## Status Sekarang

- **Build #126** (`45385291507`) — **SEDANG BERJALAN**
  - Commit: `100a64ccee1d153b2baa7432a47a2b5877f09ed6` (merge PR #2)
  - EDK2 job: **sukses**
  - XNU job: step 16 "Build Linux XNU toolchain" (berjalan)
  - Step 13 (patch), 14 (config), 15 (DTS): **sukses**
  - Step 17 "Build native XNU kernel": **belum** — ini tes utama (tempat Build #124 gagal)

## Yang Sudah Selesai

- Root cause Build #124 `Parse failure` = `unifdef 2.10` (Ubuntu 22.04) menolak 2 header XNU 8796 saat `installhdrs`.
- Patch `patches/xnu/8796-unifdef-headers.patch` dibuat; blob hash cocok persis dengan source XNU pinned.
- `patches/xnu/series` diperbarui (patch ditaruh sebelum `sdhci-block-personality.patch`).
- Mekanisme patch terverifikasi: `board.toml` `[kernel] patch_series` memuat `device:patches/xnu/series`; `patches.py` apply via `git apply` sebelum build.
- PR #2 di-merge ke `port/realme-c21y-rmx3261`.
- Dokumentasi checkpoint: `PROJECT_STATE.md` + `docs/`.

## Yang Belum / Risiko

- Kernel ARM64 belum terbukti terkompilasi sampai step 17 sukses + `kernel.macho` ada.
- **Alamat / memory map TIDAK diubah.** `MemoryMapLib` masih fail-closed.
- `MACHINE_CONFIGS=BCM2837` masih begitu (bukan penyebab error ini).
- Defconfig / DTS / UEFI tidak diubah.
- Kompilasi sukses != boot sukses != hardware didukung.

## Log

- 2026-11-24 ~11:33 UTC: PR #2 merged -> Build #126 mulai (EDK2 sukses, XNU jalan).
- 2026-11-24: XNU step 13-15 sukses (patch/config/DTS), masuk step 16 (toolchain).
