# C21Y Device Evidence — read-only adb采集

Device `1804093810BA06J3`, model `RMX3261`, Android 11 / SDK 30, build `user release-keys`, boot `orange` + `vbmeta.device_state=unlocked` + `flash.locked=no` + `secureboot=1` + `veritymode=enforcing`.
Kernel `Linux 4.14.193+`, Clang 11.0.2 (r383902b), LLD 11.0.2, SMP PREEMPT, build host `root@ubuntu-134-47`, 2024-04-22.

Raw captures in `C:\opencode-c21y\` (host only, not repo): `c21y-config.txt`, `device-facts.txt`, `deep1.txt`, `iomem.txt`, `topo-iomem.txt`.

## Bootargs (`/sys/firmware/devicetree/base/chosen/bootargs`)
Verified strings:
- `earlycon=sprd_serial,nx7n1nnnnn,1152nnn8 console=ttyS1,1152nnn8 loglevel=1`
  - `n` = digit 0 after `tr '\000' '\n'` display quirk; real values `115200`, `ttyS1`, `70000000`.
- `init=/init root=/dev/ramn rw printk.devkmsg=on`
- `androidboot.boot_devices=soc/soc:ap-apb/714nnnnn.sdio` → `/soc/ap-apb/71400000.sdio` (mmc2)
- `swiotlb=1 androidboot.init_fatal_panic=true`
- `androidboot.hardware=S1961nAA1`, `androidboot.board_id=S1961nBA1`, `androidboot.product.hardware.sku=S1961nBA1`, `androidboot.keybox_id_value=RMX3261`
- `lcd_id=ID22 bias_id=3 lcd_name=lcd_hx831n2d_skyworth_mipi_hd lcd_base=9ennnnnn lcd_size=16nnx72n pixel_clock=768nnnnn logo_bpix=24`
- `androidboot.ddrsize=4n96M range=[4n96,512n)` → 4096 MiB / [4096,5120) MiB
- `androidboot.auto.efuse=T61n`, `androidboot.auto.chipid=UMS512-AC`
- `androidboot.wdten=e551`, `modem=shutdown`, `ltemode=lcsfb`, `rfhw.id=32816`, `crystal=6`, `32k.less=1`, `marlin.clktype=1`, `androidboot.pmic.chipid=273n`, `modemboot.method=emmcboot`
- `androidboot.usb_port_flag=1`, `androidboot.hw_id=1961n_1_1n_PVT`, `androidboot.sub_match=match`
- `androidboot.vbmeta.device=PARTUUID=1.n`, `avb_version=1.1`, `hash_alg=sha256`, `size=4416n`, `digest=14e95e2e39f9e422n5n62na89b1e669ef3baf3e5a38df56d6de4b35b7de789n7`, `invalidate_on_error=yes`
- `androidboot.slot_suffix=_a`, `androidboot.force_normal_boot=1`, `bootcause="Pbint triggered"`, `sysdump_magic=821nnnnn`, `androidboot.country_region=ID`

## CPU / GIC / timer
- `cpu0..cpu7` all online, `possible`/`present` matched, `physical_package_id=0` for cpu0..5 and `1` for cpu6..7, `core_id` 0..5 then 0..1 → 2 clusters (6×A76? + 2×A55? — cluster 1 has 2 cores; not yet cross-checked with DTS `reg`/compatible).
- `/proc/interrupts`: `GICv3 4 Level arch_timer` on CPU0 only (14,751,064) — other CPU columns zero. `GICv3 103 Level /soc/aon/timer@32050000` on all CPUs. `CustomIPI 13 Edge trusty` on all CPUs. `arm-pmu` GICv3 144..151 all zero.
- Serial IRQ `GICv3 35 Level sprd_serial1`; bootargs `console=ttyS1`.
- No `/sys/devices/system/cpu/cpu0/cache` (kernel built `CONFIG_DEBUG_FS` off; cache sysfs suppressed). Cache geometry still unresolved from live device.
- `CONFIG_ARM64_VA_BITS=39`, `CONFIG_HZ=250`, `CONFIG_NO_HZ_IDLE=y`, `CONFIG_DEBUG_KERNEL=y`, `CONFIG_DEBUG_INFO=y`, `CONFIG_DEBUG_LIST=y`, `CONFIG_KASAN` off, `CONFIG_DEBUG_FS` off, `CONFIG_MOCKFS` absent.
- `MemTotal=3875088 kB` (~3.7 GiB); bootargs DDR 4 GiB; `System RAM 80000000-81feffff` + `82000000-17fffefff` from `/proc/iomem`. Kernel code `80080000-8100ffff`, kernel data `812c0000-81802fff`, namespace0.0 `81ff0000-81ffffff`.
- `/proc/iomem` verified UARTs: `70000000-700000ff` (`/soc/ap-apb/serial@70000000`), `70100000-701000ff`; eMMC host `/soc/ap-apb/71400000.sdio`; GPU `60000000-600fffff`; AON timer `32050000-3205003f` (2×); GICv3 distributor/CPU IF not shown in visible excerpt (flash), PMU/ETM trace `3f040000-3f740000`.

## Partitions (`/dev/block/by-name`, eMMC `mmcblk0`)
Confirmed: `prodnv p1`, `miscdata p2`, `misc p3`, `trustos_a p4`, `trustos_b p5`, `sml_a p6`, `sml_b p7`, `uboot_a p8`, `uboot_b p9`, `uboot_log p10`, `logo p11`, `fbootlogo p12`, `l_fixnv1_a p13`, `l_fixnv2_a p14`, `l_fixnv1_b p15`, `l_fixnv2_b p16`, `l_runtimenv1 p17`, `l_runtimenv2 p18`, `gnssmodem_a/b p19/20`, `l_modem_a/b p24/25`, `l_deltanv_a/b p26/27`, `l_gdsp_a/b p28/29`, `l_ldsp_a/b p30/31`, `l_agdsp_a/b p32/33`, `pm_sys_a/b p34/35`, `teecfg_a/b p36/37`, `hypervsior_a/b p38/39`, `boot_a/b p40/41`, `dtb_a/b p44/45`, `dtbo_a/b p46/47`, `cache p49`, `socko_a/b p50/51`, `odmko_a/b p52/53`, `vbmeta_a/b p54/55`, `metadata p56`, `sysdumpdb p57`, `avbmeta_rs_a/b p68/69`, `common_rs1_a/b p70/71`, `common_rs2_a/b p72/73`, `my_preload p74`, `userdata p75`; `super p48`.
## Boot image headers — verified 2026-11-26

`boot_a` starts `41 4e 44 52 4f 49 44 21` = `ANDROID!` (Android boot image v4 header: kernel size `0x01604910` = 23,092,240? little-endian bytes `10 60 49 01` = `0x01496010` = 21,532,688; ramdisk `0x00903d10` = 9,455,632; page size `0x1000`). `dtb_a` first 64 bytes are zero (header not at offset 0, or partition empty — unresolved). `vbmeta_a` starts `41 56 42 30` = `AVB0`. `uboot_a` starts `44 48 54 42` = `DHTB`. `stat -Lc %s` on device nodes returns 0; use `/sys/class/block/<partition>/size` × 512: `boot_a/b 131072 sectors = 67,108,864 bytes (64 MiB)`, `vendor_boot_a/b 204800 = 104,857,600 (100 MiB)`, `dtb_a/b 16384 = 8,388,608 (8 MiB)`, `vbmeta_a/b 2048 = 1,048,576 (1 MiB)`, `uboot_a/b 2048 = 1,048,576 (1 MiB)`. eMMC `mmcblk0` size `122,142,720 × 512 = 62,537,072,640 (~58.2 GiB)`, manfid `0x15` (Samsung), name `DP6DAB`, serial `0x1accd43f`. boot_a device node major:minor `259:33`.

## Full FDT
`deep1.txt` contains full `/sys/firmware/fdt` as hex (`od -An -tx1 -v`, 17735 lines). No DTB parse/extraction done yet. `cat` as binary emitted NULs; hex capture is the complete blob. Next: decode `fdtget`/`dtc` offline and diff against device DTS.

## Unverified after this pass
- Cache geometry, L2/L3 sizes, coherency.
- DT node-level `reg` for GIC/timer/PSCI (raw hex needs decode).
- Bootloader/firmware base, BootShim handoff, framebuffer ownership.
- Exact fastboot partition target for kernel/payload.
- Boot on C21Y, XNU CPU/timer/IPI, SPRD UART under XNU, GIC routing, display/storage/GPU/modem.
