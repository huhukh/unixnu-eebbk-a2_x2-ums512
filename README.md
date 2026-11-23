# UniXNU / XNU Realme C21Y RMX3261 Port

Eksperimen port sistem berbasis XNU untuk **Realme C21Y RMX3261/RMX3263**
dengan SoC **Unisoc UMS512 / T610 (S19610AA1)**.

> **Status: bring-up hardware dan audit firmware. Belum bootable. Jangan flash artefak dari branch ini.**

## Perkembangan terakhir — 23 November 2026

### Sudah dikonfirmasi dari firmware dan perangkat

- Identitas hardware yang dilaporkan perangkat: `S19610AA1`; overlay DTBO stock juga berisi compatible board `sprd,S19610AA1`. Boot properties juga melaporkan `ro.boot.board_id=S19610BA1` dan SKU `S19610BA1`; perbedaan label ini perlu direkonsiliasi sebelum dipakai sebagai identitas board tunggal.
- Base DTB dari `boot.img` berhasil diekstrak dan diparse sebagai FDT v17.
- SoC: `Unisoc UMS512 SoC`, compatible `sprd,ums512`.
- CPU: 8 core ARM64 — 6x Cortex-A55 dan 2x Cortex-A75; MPIDR `0x0` sampai `0x700` dengan langkah `0x100`.
- GICv3: distributor `0x12000000` ukuran `0x20000`; redistributor `0x12040000` ukuran `0x100000`, stride `0x20000`.
- UART stock console: `0x70100000`, status `okay`; UART kedua `0x70000000`.
- Display blocks: DPU `0x20300000` ukuran `0x1000`; DSI `0x20400000` ukuran `0x1000`.
- Base DTB memory node: `0x80000000 + 0x80000000` (2 GiB).
- FDT live dari perangkat stock berhasil dibaca secara read-only melalui ADB root pada 23 November 2026 (283729 byte, FDT v17). `/memory/reg` live adalah `0x80000000 + 0xfffff000`, satu rentang hampir 4 GiB sampai `0x17fffff000` (eksklusif). Disassembly AArch64 menunjukkan jalur persiapan FDT U-Boot memanggil routine yang mencari `/memory` lalu menyetel `reg` dari ukuran RAM global; detail bukti dan batasnya ada di audit firmware.
- Boot property read-only `ro.boot.ddrsize=4096M` dan `ro.boot.ddrsize.range=[4096,5120)` menguatkan kapasitas DRAM yang dilaporkan sebagai 4 GiB. Properti ini tidak menentukan bank layout, reserved memory, atau RAM usable UEFI.
- Android runtime sebelumnya menunjukkan zone DMA mulai `0x80000000` dan zone Normal mulai `0x100000000`. FDT live menggambarkan satu rentang besar; pembagian pada 4 GiB lebih konsisten dengan batas zone kernel daripada bukti dua bank DRAM terpisah. Ini tetap **bukan** peta RAM UEFI yang siap dipakai.
- Stock DTBO berisi satu overlay board `Unisoc UMS512 1H10 board`, compatible `sprd,S19610AA1`. Overlay menambahkan reservasi logo/framebuffer/face-id/writeback dan konfigurasi perangkat board.
- Paket firmware memuat `u-boot-sign.bin` berperan `UBOOTLOADER`; byte-nya sama dengan FDL2 kecuali 256 byte dekat akhir berkas. U-Boot image-preparation path dan live FDT mendukung bahwa U-Boot normal-boot memperbarui node RAM; kapasitas runtime dilaporkan `4096M`. Ini tetap bukan memory map UEFI atau rentang RAM usable. Lihat [FDL2 RAM/FDT forensic triage](docs/FDL2-RAM-FDT-FORENSICS.md) dan [stock firmware audit](docs/stock-firmware-audit.md).

Rincian, rentang alamat, reserved-memory, dan batas bukti dicatat di
[`docs/stock-firmware-audit.md`](docs/stock-firmware-audit.md).

### Implementasi yang masih belum selesai

- Penyelesaian platform UEFI/EDK2 C21Y dan MemoryMapLib.
- Profil repo masih memilih iPadOS 17.7.11 dan patch XNU 10063.141.1; ini belum sesuai target iOS 16.5 / XNU 8796.121.2.
- Workflow Actions saat ini belum mengompilasi XNU; workflow hanya memeriksa konfigurasi/DTS dan mengompilasi UEFI scaffold.
- Scaffold C21Y belum memuat GOP, eMMC block I/O, atau aplikasi/loader XNU; UART/framebuffer debug yang diwarisi juga masih memiliki asumsi panel board A2.
- Rekonsiliasi FDT live yang sudah ditangkap dengan ownership firmware dan kontrak handoff C21Y.
- FD/firmware load address, payload window, stack/heap dan ownership setiap carve-out.
- UEFI GOP/framebuffer handoff yang terukur.
- Driver/bring-up C21Y untuk touch, storage, power, radio, audio dan GPU.
- Build serta uji boot RAM-only XNU dengan logging/framebuffer.

## Peringatan kompatibilitas

Board EEBBK A2/X2 dan profil Qualcomm HackiOS (Redwood/Garnet) bukan profil C21Y.
Hanya definisi SoC yang terbukti sama boleh dijadikan referensi. Jangan salin
alamat UEFI, peripheral window, framebuffer, storage atau reserved memory dari
board lain.

Repo ini juga memuat catatan adaptasi arsitektur HackiOS iOS 16.5 / XNU
`8796.121.2`: [`docs/HACKIOS-C21Y-PORT-ADAPTATION.md`](docs/HACKIOS-C21Y-PORT-ADAPTATION.md).
Eksperimen identitas software `iPhone10,3` / `D22AP` tidak mengubah hardware
fisik C21Y menjadi iPhone X dan tidak menggantikan board descriptor UMS512.

## Milestone

- [x] Identifikasi SoC dan board dari stock firmware.
- [x] Ekstraksi dan parsing base DTB dari stock boot image.
- [x] Identifikasi CPU, GICv3, UART, DPU dan DSI dari base DTB.
- [x] Audit awal DTBO dan board overlay.
- [x] Kumpulkan bukti runtime Android tentang dua rentang DRAM.
- [x] Tangkap dan parse FDT live yang digunakan Android melalui ADB read-only.
- [x] Catat properti boot read-only yang melaporkan kapasitas DRAM 4 GiB.
- [x] Triase statis FDL2 stock: string DRAM/FDT dan referensinya dicatat; jalur sukses runtime belum terbukti.
- [ ] Identifikasi komponen boot-chain yang melakukan memory-size fixup dan cocokkan reservasi FDT dengan ownership firmware.
- [ ] Rekonsiliasi semua reserved-memory dan firmware ownership.
- [ ] Tetapkan alamat UEFI FD, stack, heap dan payload berdasarkan bukti.
- [ ] Implementasikan C21Y UEFI MemoryMapLib dan platform package.
- [ ] Buktikan UEFI loader berjalan tanpa menulis partisi.
- [ ] Boot XNU RAM-only dengan logging/framebuffer.
- [ ] Bring-up input, storage dan perangkat lain.

## Dokumen teknis

- [Stock firmware audit](docs/stock-firmware-audit.md) — hasil DTB/DTBO, CPU/GIC/UART/display, RAM dan reserved memory.
- [FDL2 RAM/FDT forensic triage](docs/FDL2-RAM-FDT-FORENSICS.md) — identitas berkas firmware, string, AArch64 reference, boot properties dan batas kesimpulan.
- [HackiOS C21Y adaptation](docs/HACKIOS-C21Y-PORT-ADAPTATION.md) — pemetaan arsitektur HackiOS ke board C21Y dan blocker implementasi.

## Safety

**Jangan flash boot/vendor_boot/vbmeta atau image eksperimen.** Parsing DTB,
kompilasi DTS, dan CI yang sukses bukan bukti perangkat dapat boot. Lanjutkan
dengan inspeksi read-only dan validasi boot RAM-only sebelum mempertimbangkan
perubahan partisi.
