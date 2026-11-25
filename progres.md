# Progres Port XNU — Realme C21Y (RMX3261 / UMS512 T610)

> File ini di-update tiap ada info/progres baru. Ringkas saja.
> Terakhir update: 2026-11-25 (UTC).

## Bukti hardware baru (read-only, belum dipakai DTS)

- GPU `sprd,mali-gondul`: MMIO `0x60000000` + `0x100000`, 3 IRQ `JOB/MMU/GPU` = SPI 60, phandle `0xfd`.
- Touchscreen SPI `0x70a00000` + `0x1000`; anak `touchscreen@0` aktif `himax,hxcommon` (getevent `himax-touchscreen`), 720×1600, IRQ GPIO 144, reset GPIO 145, SPI 10 MHz.
- Batre: 3 node `simple-battery` (LWN/ATL/non-standard), 4872 mAh, 3.456–4.42944 V; `monitored-battery = <0x1a8 0x1a9 0x1aa>`; charger `bq2560x_charger`, fuel gauge `sc27xx-fgu`. Tidak ada alamat MMIO batre — jangan dikarang.
- Clock controller live ditemukan (`0x20200000`, `0x32080000`, `0x62100000`, `0x62200000`); koreksi catatan lama. Mapping phandle clock UART masih belum.
- Detail byte: `docs/HARDWARE_EVIDENCE.md` §9.

## Status Sekarang

- **Build #143** (`45565371465`, head `5d6b6e3`) — **GAGAL di step 17** setelah 2m05s. Fix R20 (`reserved10`) terbukti hilang; error baru: `fatal error: 'arm64/ppl/sart.h' file not found` dari `pmap.c:87` (R21).
  - Penyebab: xnu-8796 punya include + call `sart_bootstrap()`/`uat_bootstrap()` tanpa guard; board BCM2837 tidak punya `XNU_MONITOR`/SART/UAT. OS series belum mem-port `non-apple-iommu-bootstrap` dari arch series.
  - Fix: `os-profiles/ios-16.5-20F66/patches/xnu-8796/8796-non-apple-iommu-bootstrap.patch`, 2 hunk tervalidasi byte-for-byte terhadap `c54f35ca7679`; belum di-CI.
  - `kernel.macho` masih belum ada.
- Build #142 (`45542624841`, head `4b3a42e3`) — **GAGAL di step 17**, tapi ini pertama kalinya kompilasi XNU asli jalan (3m16s).
  - Step 1–16 sukses; toolchain 1h45m.
  - Error compiler pertama: `osfmk/arm/pmap/pmap.h:445:7: error: duplicate member 'reserved10'` (deklarasi sebelumnya di baris 422).
  - Penyebab: xnu-8796 punya dua field `reserved10` di branch `#else` `CONFIG_ROSETTA` dan `HAS_APPLE_PAC`. C21Y tanpa PAC → dua branch aktif. Bukan salah config fragment.
  - Fix: `patches/xnu/8796-pmap-no-pac-reserved10.patch` (rename field slot PAC), hunk tervalidasi offline terhadap `c54f35ca7679`; belum di-CI.
  - `kernel.macho` masih belum ada. Lihat `docs/RESEARCH_LOG.md` R20.
- Build #126 (`45385291507`) — **GAGAL di step 17** (link), bukan lagi `Parse failure`
  - Commit: `100a64ccee1d153b2baa7432a47a2b5877f09ed6` (merge PR #2)
  - EDK2 job: **sukses**
  - XNU step 1–16: **sukses** (termasuk step 13 patch, 15 DTS, 16 toolchain)
  - Step 17 "Build native XNU kernel": **GAGAL** — 1 simbol undefined:
    `_arm64_platform_sleep_hook`, direferensikan `ArmCpu::start` di `libArmCpu.a(ArmCpu.o)`
  - **Bukti unifdef fix berhasil:** tidak ada `Parse failure` di log #126
  - **`kernel.macho` TIDAK ada** — link gagal sebelum pengecekan `kernel.macho`
  - Artifact `realme-c21y-build-check`: 71.555.458 byte, sha256 `f9380b35...`, isinya log/build, bukan kernel
- Build #127 (redundan, commit progres.md) sudah **dibatalkan**.
- **Fix link sudah di-push:** `patches/xnu/8796-arm64-platform-sleep-hook.patch` (definisi simbol hook di `osfmk/arm64/cpu.c`) + entri `patches/xnu/series`, commit `5c39de471823b72081f5afc6e1490ca3ccf199ff`.
- Build #128 (`45413693437`) — **GAGAL** karena patch sleep-hook tanpa newline akhir (R15); sudah diperbaiki di `c7c6de6`.

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
- **GICv3**: GICD `0x12000000`+`0x20000`, GICR `0x12040000`+`0x100000`, stride redistributor `0x20000` (=8 frame, cocok 8 core), maintenance PPI 9 (INTID 25) level-high, `#interrupt-cells=3` (dari live FDT).
- **PSCI 0.2 (smc)**: node `/psci` cuma `compatible` + `method=smc`, **tanpa** HVC dan tanpa sel `cpu_suspend/migrate`; `/idle-states` `entry-method=arm,psci`.
- CPU: 6x Cortex-A55 (`cpu@0..500`, `capacity-dmips-mhz` 544) + 2x Cortex-A75 (`cpu@600..700`, 1024). `/cpus/#address-cells=2`, tiap `reg` = `Aff1` 0x0,0x100,…,0x700 (Aff0=0, tanpa Aff2). `cpu-map`: cluster0=core0..5, cluster1=core0..1 — penamaan ODM saja, **reg yang otoritatif**.
- Timer: `arm,armv8-timer`, PPI `<1 13 4>` secure-phys, `<1 14 4>` non-secure-phys (INTID 30, ini yg dipakai EL1), `<1 11 4>` virt, `<1 10 4>` hyp; **tidak ada** `clock-frequency`, ada `arm,no-tick-in-suspend` → frekuensi harus dari `CNTFRQ_EL0`.
- Console/UART: `/soc/ap-apb/serial@70100000` + `@70000000`, keduanya `compatible = "sprd,ums518-uart","sprd,sc9836-uart"`, `reg` size `0x100`, SPI level-high **2** (`@70000000`) dan **3** (`@70100000`), clocks `enable`/`uart`/`source` = phandle `0x1c`/`0x1d`/`0x1e`, **tidak ada** `clock-frequency` di node.
- Clock tree UART: `0x1c` = `/soc/apapb-gate` (`sprd,sharkl5pro-apapb-gate`, #clock-cells 1); `0x1d` = `/soc/clock-controller@20200000` (`sprd,sharkl5pro-ap-clk`, `0x20200000`+`0x1000`); `0x1e` = `/soc/clock-controller@32080000` (`sprd,sharkl5pro-aonapb-clk`, `0x32080000`+`0x1000`). Referensi `ext-26m` = **26 000 000 Hz** (`0x018CBA80`), `ext-32k` = 32768, `rco-100m` = 100 MHz; `clk-13m` = 26/2, `clk-4m3` = 26/6. Gate lain: `apahb-gate` phandle `0x24`, `aonapb-gate` phandle `0x04`, mm clk `0x06`, mm gate `0x05`. **Divisor 115200 belum dibuktikan** — jangan diasumsikan.
- Node root lain (belum dipakai): `firmware`, `trusty` (`android,trusty-smc-v1`), `seth@0..13`, `hwfeature` (`auto`,`lwfq`), `cpuinfo_hardware`=`T610-Unisoc`, `sprd,sc-id`=`ums512 1000 1000`.
- Boot storage: eMMC `mmcblk0` (~58.2 GiB) via `71400000.sdio`. A/B slot, aktif `_a`.
- Partisi penting: boot_a=p40(64M), vendor_boot_a=p42(100M), dtb_a=p44(8M), dtbo_a=p46(8M), super=p48(~8.6G), vbmeta_a=p54, uboot_a=p8, trustos_a=p4, sml_a=p6.
- Boot image `boot_a` header v2: kernel_size 0x1496010, ramdisk_size 0x903d10 (sama dgn initrd live), kernel_addr 0x8000, ramdisk_addr 0x5400000, tags_addr 0x100, page_size 0x800. **Base/relokasi bootloader BELUM terbukti** (initrd live 0x82100000 != 0x80000000+0x5400000) — jangan dipakai sebagai handoff address dulu.

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
- 2026-11-24: boot handoff evidence: kernel runtime `0x80080000`, compressed load `0x80008000` (header), initrd `0x82100000`, no KASLR seed; protokol arm64 `x0`=FDT (belum diuji dgn XNU).
- 2026-11-24 ~14:24 UTC: patch `8796-arm64-platform-sleep-hook.patch` + `series` di-commit ke branch (`5c39de4`) → **Build #128** mulai; EDK2 sukses, XNU lanjut step 16.
- 2026-11-24: ADB read-only probe ke-2 (UART/clock/GIC/timer/CPU topology) → detail masuk `docs/HARDWARE_EVIDENCE.md` §2.1. Belum ada klaim driver.

---

## Sesi 2026-11-25 — akar Build #136/#137 ketemu, data HP tambahan

### Akar masalah (terbukti, bukan dugaan)

`apple-only-cpu-tunables.patch` **tidak cocok** dengan source XNU yang dipakai CI.

Diverifikasi langsung terhadap tree yang di-pin CI: `apple-oss-distributions/xnu` commit `c54f35ca767986246321eb901baf8f5ff7923f6a` (tag `xnu-8796.121.2`, 873 baris di `osfmk/arm64/start.s`).

| Hunk | Ditulis di patch | Kenyataan di source | Hasil |
| --- | --- | --- | --- |
| 1 | `@@ -33,7 +33,9 @@` | blok memang di baris 33-39 | **cocok** |
| 2 | `@@ -783,10 +785,13 @@` + konteks `#if HAS_CLUSTER && !NO_CPU_OVRD` | `#endif // APPLE_ARM64_ARCH_FAMILY` di 775, `#if HAS_CLUSTER` di 783 (tanpa `&& !NO_CPU_OVRD`) | **GAGAL** |

Jadi hunk 2 harus mulai di baris **775**, bukan 783, dan konteks penutup harus `#if HAS_CLUSTER`.

Patch upstream UniXNU (`zus12873/UniXNU:patches/xnu/apple-only-cpu-tunables.patch`) punya **dua cacat yang sama**. Artinya ini bukan salah ketik di repo kita — patch upstream memang dibuat untuk tree yang `start.s`-nya beda dari rilis OSS `xnu-8796.121.2`.

### Temuan tambahan yang penting

`osfmk/arm64/tunables/tunables.s` **tidak ada** di rilis OSS `xnu-8796.121.2` (sudah dicek: 5328 path) maupun `xnu-10063.141.1` (5529 path). Makro `APPLY_TUNABLES` juga tidak ada di mana pun. Tapi `start.s` baris 36 meng-`#include` file itu dan baris 780 memanggil `APPLY_TUNABLES`.

`APPLE_ARM64_ARCH_FAMILY` **tidak** di-define oleh `config/MASTER.arm64.bcm2837`, `config/MASTER`, `osfmk/conf/files.arm64`, `asm.h`, maupun `proc_reg.h` untuk board non-Apple. Jadi guard-nya bernilai **false**, dan justru itulah yang menyelamatkan build: `#include` dan `APPLY_TUNABLES` ikut hilang. Tanpa guard ini, assemble akan gagal karena file tidak ada.

**Konsekuensi:** patch ini **wajib** untuk semua build arm64 non-Apple di xnu-8796. Bukan sekadar "buang tuning Apple".

### Yang sudah diperbaiki

`os-profiles/ios-16.5-20F66/patches/xnu-8796/apple-only-cpu-tunables.patch` ditulis ulang, hunk dihitung ulang terhadap `c54f35ca7679`:

- hunk 1: `@@ -33,7 +33,9 @@`
- hunk 2: `@@ -775,9 +777,11 @@`
- baris `index a261552b8cdd..f435c87d6ac7` dibuang (git tidak butuh untuk `git apply`)
- 572 byte, LF semua, diakhiri newline, spasi+tanggal di baris konteks ber-tab tetap utuh

**Verifikasi sebelum commit:** kedua hunk di-replay terhadap file asli yang di-fetch, **setiap byte konteks cocok**. Tidak perlu tunggu build 78 menit untuk tahu patch ini benar.

Sebagai tambahan, **seluruh 60 hunk dari 12 patch** di OS series di-replay terhadap tree yang di-pin. Hasilnya: hanya patch ini yang benar-benar tidak cocok. Empat lainnya (`clang-uio-stackbuf` di `sys_generic.c`/`vfs_lookup.c`, `native-aes-personality`, `zzx-pmap-sync-64bit-pa`) hanya **offset** karena patch sebelumnya menggeser teks — dan `git apply` toleran terhadap offset.

### Data HP baru (ADB, read-only, 2026-11-25)

**Konfigurasi CPU/MMU dari** `/proc/config.gz` (4799 baris):

| Opsi | Nilai | Arti untuk port |
| --- | --- | --- |
| `CONFIG_ARM64_VA_BITS` | `39` | 512 GiB VA — cocok layout XNU arm64 39-bit, **jangan** asumsikan 48-bit |
| `CONFIG_ARM64_4K_PAGES` | `y` | granule 4 KiB |
| `CONFIG_PHYS_ADDR_T_64BIT` | `y` | `phys_addr_t` 64-bit |
| `CONFIG_ARM64_PAN` / `_UAO` / `_LSE_ATOMICS` / `_HW_AFDBM` | `y` | fitur CPU tersedia |
| `CONFIG_ARM64_TAGGED_ADDR_ABI` | `y` | TBI aktif |
| `CONFIG_UNMAP_KERNEL_AT_EL0` | `y` | Linux pakai trampoline EL0 — **XNU tidak punya padanannya** |
| `CONFIG_ARM64_PTR_AUTH` / `_BTI` / `_MTE` / `_VHE` / `ARM64_PA_BITS` | **tidak ada** | jangan aktifkan fitur ini |
| Errata aktif | `826319 827319 824069 819472 845719 843419 1024718 858921` | set erratum A55/A75 yang dipakai vendor |
| `CONFIG_RANDOMIZE_BASE` | `y` | KASLR aktif, tapi FDT **tidak** punya `chosen/kaslr-seed` → bootloader bukan sumber entropi |

**Frekuensi timer sekarang TERBUKTI = 26 MHz.** Dari `/proc/timer_list`, clock event device per-CPU:

- `arch_sys_timer`, `set_next_event: arch_timer_set_next_event_phys`
- `mult = 111669150`, `shift = 32`
- `2^32 / 111669150` = **38.4615 ns** per cycle → **CNTFRQ = 26 000 000 Hz**

Ini mengonfirmasi `ext-26m` di DT secara independen, dan cocok dengan referensi 26 MHz yang dibutuhkan rantai clock UART SPRD. **Nilai ini terukur dari kernel yang hidup**, jadi setup timer XNU boleh memakai 26 MHz di board ini — tapi tetap bukan bukti XNU membacanya dengan benar.

Ada juga broadcast clock event device kedua `sprd_timer` (`mult 70369`, `shift 31` ≈ 30 518 ns) untuk `tick_handle_oneshot_broadcast` dengan mask `b8` (CPU 3,4,5,7). Clocksource tersedia: `arch_sys_counter` dan `sprd_suspend_timer` (yang terakhir vendor-specific, tidak ada padanannya di XNU).

**Routing GIC terbukti saat runtime** dari `/proc/interrupts`:

| IRQ tercetak | Perangkat |
| --- | --- |
| `30` | `arch_timer` — PPI 14, **berjalan di kedelapan CPU** |
| `103` | `/soc/aon/timer@32050000` |
| `35` | `sprd_serial1` |
| `42`/`51`/`52` | `mmc0`/`mmc1`/`mmc2` |
| `58`/`59` | `GSP0`/`DISPC` |

`arch_timer` punya hitungan non-nol di **semua 8 CPU** → PPI 14 benar-benar terkirim ke setiap PE, dan redistributor GICv3 untuk 8 frame hidup semua.

### Yang masih kurang / belum terbukti

- `kernel.macho` masih belum pernah ada. Link belum pernah tercapai.
- Handoff final (pointer FDT, ownership, window payload, stack/heap, window FD) belum terbukti.
- Divisor baud UART SPRD 26 MHz → 115200 belum terbukti (yang terbukti baru referensi 26 MHz-nya).
- Apakah pmap arm64 XNU jalan dengan `VA_BITS=39` + 4 KiB di board ini — nilainya cocok dengan kernel stok, tapi tabel XNU belum pernah dibangun.
- Boot XNU di HP belum dicoba/diklaim. Kompilasi sukses != boot sukses != hardware didukung.

### Log

- 2026-11-25: ambil `/proc/config.gz`, `/proc/timer_list`, `/proc/interrupts`, `/sys/devices/system/clocksource`, listing `/proc/device-tree` — semua read-only.
- 2026-11-25: replay 60 hunk dari 12 patch terhadap tree pinned; hanya `apple-only-cpu-tunables.patch` yang gagal.
- 2026-11-25: `apple-only-cpu-tunables.patch` ditulis ulang + diverifikasi byte-per-byte.

## Sesi 2026-11-25 (lanjutan) - DTS port dibandingkan byte-per-byte dengan DT live

Fokus sesi ini: bukan menebak, tapi membandingkan `dts/` milik port dengan isi
`/proc/device-tree` di HP yang benar-benar jalan. Semua dump diambil read-only
dengan `od -An -tx1` (serial `1804093810BA06J3`), rinciannya masuk
`docs/HARDWARE_EVIDENCE.md` §8.

### Temuan: DTS port sebelumnya hanya stub

`dts/realme-c21y-rmx3261.dts` cuma 681 byte dan **tidak punya node
`device_type = "memory"`**. Itu bukan cacat kosmetik:
`scripts/unixnu/devicetree.py:302-304` menolak ADT kalau tidak ada tepat satu
node memory dengan satu tuple `reg` (`ADT handoff requires one contiguous DRAM
range`). Artinya tahap payload/ADT pasti gagal walaupun kernel berhasil dilink.

### 8 cacat yang terbukti dari byte DT live, dan perbaikannya

| # | Sebelum (port) | Live | Sesudah (port) |
| --- | --- | --- | --- |
| 1 | `psci` = `"arm,psci-1.0"`, `"arm,psci-0.2"` | `61 72 6d 2c 70 73 63 69 2d 30 2e 32 00` = `arm,psci-0.2` saja | satu string `"arm,psci-0.2"` |
| 2 | `/timer` punya `clock-frequency = <26000000>` | properti itu **tidak ada** | dihapus; 26 MHz hanya di `/cpus/timebase-frequency` |
| 3 | GIC `#address-cells = <0>` | `#address-cells = 2`, `#size-cells = 2` | 2 / 2 |
| 4 | GIC tanpa maintenance IRQ | `1 9 4` (PPI 9) | `interrupts = <1 9 4>` |
| 5 | GIC pakai `AAPL,phandle = <0x1>` | DT live pakai `phandle` | `phandle = <0x1>` (workflow macOS yang mengubahnya jadi `AAPL,phandle` saat emit ADT) |
| 6 | UART `"sprd,sc9836-uart"` saja | `"sprd,ums518-uart"` lalu `"sprd,sc9836-uart"` | urutan dibetulkan |
| 7 | tidak ada node memory | `reg = <0 0x80000000 0 0xfffff000>` | `/memory@80000000` ditambahkan |
| 8 | `tos-mem` `0x94040000` | `0x94060000` / `0x4fa0000` | dikoreksi |

Catatan penting: DTB statis di `docs/C21Y-STOCK-DTB-MEMORY-INSPECTION.md` menulis
DRAM 2 GiB (`0x80000000`), sedangkan tree yang benar-benar diserahkan ke kernel
yang jalan menulis `size = 0xfffff000`. Yang dipakai port adalah nilai live.

### Yang sengaja TIDAK diisi (biar tidak menebak)

- `clocks` untuk UART: `clock-names = "enable","uart","source"` terbukti, tapi
  node clock controller UMS512 belum dideskripsikan, dan generator ADT menolak
  referensi phandle yang tidak resolve. Daripada memalsukan, properti
  dihilangkan dan dicatat sebagai gap.
- `v2m@0` (ITS/MSI GIC) terbukti ada di DT live, belum ada konsumen.
- `capacity-dmips-mhz` (1024 di cluster A75) terbukti, tapi itu hint scheduler
  Linux dan tidak dibaca ADT.

### ADT: kebutuhan generator yang dikonfirmasi dari source

`scripts/unixnu/devicetree.py` (UniXNU `main`) + `ArmDTPlatform.cpp`
(submodule `e8bd8d5d`):

- wajib tepat satu node `device_type = "memory"`, satu tuple `reg`;
- `timebase-frequency` dibaca dari node `/cpus`, bukan `/timer`;
- `/arm-io`, `/defaults`, `/options`, proxy NVRAM `/chosen`
  (`nvram-bank-size`, `nvram-proxy-data`), `random-seed`, `dram-base`,
  `dram-size` **dibuat oleh generator** — jangan ditulis manual di DTS. DT
  vendor memang tidak punya `/arm-io`, `/defaults`, `/options`, atau node
  `*nvram*` sama sekali;
- `ArmDTPlatform::configure()` gagal kalau proxy NVRAM tidak ada, jadi tidak
  bisa "dilewati";
- baris 313 `int(options['chip_id'], 16)` jalan setiap kali `--unique-chip-id`
  diberikan, jadi `[payload.adt] chip_id` **wajib**. Sebelumnya tidak ada di
  `board.toml` → `KeyError` saat build payload.

`board.toml` sekarang: `chip_id = "0x8015"` (32789), yaitu nilai yang sudah
dideklarasikan OS profile `ios-16.5-20F66` untuk kernel D22AP/iPhone10,3 yang
kita boot. Ini nilai identitas OS, **bukan** ID hardware Unisoc — tidak ada
sumber vendor yang mendokumentasikan properti `chip-id` untuk UMS512, jadi
mengarang nilai lain justru tidak berdasar.

### Status build

- **Build #138/#139/#140 gagal di langkah 17, bukan karena patch R17.** Toolchain
  sukses 105 menit, lalu `git apply` gagal 2 detik di `start.s:33`. `status.json`
  di ringkasan run membuktikan `board.kernel.patch_series` masih
  `arch → soc → os → device`: pada head `0c12f50d`, header `[kernel.prelink]`
  ditulis **sebelum** array `patch_series`, sehingga array itu masuk ke tabel
  `[kernel.prelink]` dan board tidak pernah mengganti daftar arsitektur.
  Patch yang gagal adalah patch xnu-10063 bawaan `arch:patches/xnu/series`;
  patch OS yang sudah diperbaiki (`f94c73d2`) bahkan tidak pernah dipakai dan
  sudah diverifikasi cocok byte-per-byte. Lihat R18.
- Commit `3614a701` memindahkan `[kernel.prelink]` ke akhir `board.toml`.
  Sekarang `patch_series = soc → os → device` dan fragment `soc`/`os` ikut
  terpakai. **Belum ada build yang jalan di head yang sudah benar** — run baru
  diperlukan. Klaim compile/boot/hardware masih nol.
- Perubahan DTS/`board.toml` sudah di-push: `3f4c55d0` (dtsi), `f09d4fa1`
  (board DTS), `3614a701` (chip_id + perbaikan tabel + docs).
- **Build #139 dan #140 lolos langkah 15 `Compile C21Y device tree`** —
  `dtc` menerima DTS/DTSI baru (sintaks + jumlah cell). Bukan bukti ADT,
  handoff, atau hardware.
