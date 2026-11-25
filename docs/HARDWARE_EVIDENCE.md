# HARDWARE_EVIDENCE — Realme C21Y RMX3261 / UMS512

This file separates verified device observations from build artifacts and from assumptions. Presence here is **not** a claim that XNU boots or that a peripheral is supported.

## 0. Live device access (2026-11-24)

- Device connected over ADB: serial `1804093810BA06J3`, `ro.product.device=RMX3261`, `ro.board.platform=ums512`, Android 11 (`RP1A.201005.001/1713785217000:user/release-keys`), stock kernel `Linux 4.14.193 aarch64`.
- Bootloader unlocked: `ro.boot.verifiedbootstate=orange`, `ro.boot.flash.locked=0`, `vbmeta.device_state=unlocked`.
- ADB shell is `uid=2000(shell)`, but **root is available via Magisk**: `/system_ext/bin/su` -> `su -c id` = `uid=0(root) gid=0(root) ... u:r:magisk:s0`.
- Every value below was read with `su -c` from `/proc/iomem`, `/proc/cmdline`, `/proc/partitions`, `/proc/device-tree/*`, and a pulled live FDT (`/sys/firmware/fdt`, 283729 bytes). Only read-only commands were used: **no fastboot, flash, reboot, or partition write**.

## 1. Device identity

| Observation | Value | Source |
| --- | --- | --- |
| Board name used by this port | `realme-c21y-rmx3261` | `board.toml`, `porting.toml` |
| SoC | Unisoc UMS512 / SharkL5Pro, marketing T610 | `board.toml`, vendor sources |
| Board platform string | `ums512_1h10` | C21Y device-tree references |
| `ro.boot.hardware` | `S19610AA1` | Live `getprop` + cmdline |
| `ro.boot.board_id` | `S19610BA1` | Live `getprop` + cmdline |
| `ro.boot.product.hardware.sku` | `S19610BA1` | Live `getprop` + cmdline |
| `ro.boot.hw_id` | `19610_1_10_PVT` | Live cmdline |
| Chip / efuse | `androidboot.auto.chipid=UMS512-AC`, `androidboot.auto.efuse=T610`, `androidboot.pmic.chipid=2730` | Live cmdline |
| Root DT compatible | `sprd,ums512` | Live FDT `/compatible` |
| DTBO compatible | `sprd,S19610AA1` | DTBO audit |
| Stock kernel | Linux `4.14.193` | Live `uname -a` |
| Target XNU | `8796.121.2` / Darwin `22.5`, iOS `16.5` build `20F66` | `os-profiles/ios-16.5-20F66/profile.toml` |

`iPhone10,3` / `D22AP` in the OS profile is a software identity chosen for iOS compatibility. It is **not** the C21Y hardware identity and must not be reported as such.

## 2. CPU / interrupt controller / timer — verified from live FDT

| Item | Verified value | Source |
| --- | --- | --- |
| CPU topology | 6x Cortex-A55 (`cpu@0`..`cpu@500`) + 2x Cortex-A75 (`cpu@600`..`cpu@700`) | Live FDT `/cpus/cpu@*` |
| MPIDR values | `0x0`..`0x700`, step `0x100` | Live FDT `/cpus/cpu@*/reg` |
| CPU enable method | `psci` | Live FDT `/cpus/cpu@*/enable-method` |
| PSCI | compatible `arm,psci-0.2`, method `smc` | Live FDT `/psci` |
| GIC version | GICv3, `arm,gic-v3` | Live FDT `/interrupt-controller@12000000` |
| GICD | base `0x12000000`, size `0x20000` | Live FDT reg |
| GICR | base `0x12040000`, size `0x100000` | Live FDT reg |
| Timer | `arm,armv8-timer` (generic timer; CNTFRQ from firmware) | Live FDT `/timer` |
| UART console | `0x70100000` + `0x100`; `chosen/stdout-path` = `/soc/ap-apb/serial@70100000` | Live FDT + cmdline |
| Console / earlycon | `console=ttyS1,115200n8`, `earlycon=sprd_serial,0x70100000,115200n8` | Live cmdline |
| Second UART | `0x70000000` + `0x100` | `/proc/iomem` |

These are hardware facts, not proof of XNU driver support.

### 2.1 Additional live-FDT detail captured 2026-11-24 (second probe)

Read-only, via `su -c` and `/proc/device-tree`. All values are raw big-endian cells from the live FDT.

**UART nodes** — `/soc/ap-apb/serial@70000000` and `serial@70100000`:

| Property | `serial@70000000` | `serial@70100000` |
| --- | --- | --- |
| `compatible` | `sprd,ums518-uart`, `sprd,sc9836-uart` | same |
| `reg` | `0x70000000` + `0x100` | `0x70100000` + `0x100` |
| `interrupts` | `<0 2 4>` (SPI 2, level-high) | `<0 3 4>` (SPI 3, level-high) |
| `clocks` | enable `0x1c`, uart `0x1d`, source `0x1e` | same |
| `clock-names` | `enable`, `uart`, `source` | same |
| `status` | `okay` | `okay` |
| `phandle` | `0xfe` | `0xff` |

No `clock-frequency` property in either UART node, so the baud divisor input must come from the clock tree, not from the node.

**Clock tree resolved** — the three UART clock phandles are:

| phandle | Node | Compatible | Register window |
| --- | --- | --- | --- |
| `0x1c` | `/soc/apapb-gate` | `sprd,sharkl5pro-apapb-gate` (`#clock-cells = 1`) | gate, no `reg` at this node |
| `0x1d` | `/soc/clock-controller@20200000` | `sprd,sharkl5pro-ap-clk` (`#clock-cells = 1`) | `0x20200000` + `0x1000` |
| `0x1e` | `/soc/clock-controller@32080000` | `sprd,sharkl5pro-aonapb-clk` (`#clock-cells = 1`) | `0x32080000` + `0x1000` |

Source oscillators/fixed clocks at root: `ext-26m` `fixed-clock` `clock-frequency = 0x018CBA80` = **26 000 000 Hz**; `ext-32k` = `0x8000` = **32 768 Hz**; `rco-100m` = `0x05F5E100` = **100 000 000 Hz**. Derived root clocks: `clk-13m` (`factor`, mult 1 / div 2 of `0x1e`), `clk-4m3` (`factor`, mult 1 / div 6 of `0x1e`), `clk-1m`, `clk-250k`, `clk-6m5`. So the 26 MHz UART reference is present in the tree, and 115200 must be derived from it by the AP clock controller — the divisor chain is **not yet proven** and is not assumed here.

Other clock/gate nodes in `/soc`: `apahb-gate` (phandle `0x24`, `sprd,sharkl5pro-apahb-gate`), `aonapb-gate` (phandle `0x04`, `sprd,sharkl5pro-aon-gate`), `clock-controller@62100000` (`sprd,sharkl5pro-mm-clk`, phandle `0x06`), `clock-controller@62200000` (`sprd,sharkl5pro-mm-gate-clk`, phandle `0x05`).

**GIC detail** — `/interrupt-controller@12000000` (root level, not under `/soc`):

| Property | Value |
| --- | --- |
| `compatible` | `arm,gic-v3` |
| `phandle` | `0x01` (so `interrupt-parent` resolves to it) |
| `reg` | `0x12000000` + `0x20000` (GICD), `0x12040000` + `0x100000` (GICR) |
| `#redistributor-regions` | `1` |
| `redistributor-stride` | `0x20000` |
| `#interrupt-cells` | `3` |
| `interrupts` (maintenance) | `<1 9 4>` → PPI 9 = INTID 25, level-high |
| `#address-cells` / `#size-cells` | `2` / `2` |
| child | `v2m@0` (Coresight, not used for bring-up) |

`0x100000` of redistributor window with `0x20000` stride = **8** redistributor frames, matching the 8 PEs. This is a GICv3 **system-register** CPU interface (`ICC_*`), not a GICC MMIO frame.

**Timer** — `/timer`:

| Property | Value |
| --- | --- |
| `compatible` | `arm,armv8-timer` |
| `interrupts` | `<1 13 4>`, `<1 14 4>`, `<1 11 4>`, `<1 10 4>` → PPI 13 secure phys, PPI 14 non-secure phys, PPI 11 virtual, PPI 10 hyp; all level-high |
| `arm,no-tick-in-suspend` | present |
| `clock-frequency` | **absent** |

Timer PPI 14 (INTID 30) is the one an ordinary EL1 kernel must use. The counter frequency is not in the DT; it must come from `CNTFRQ_EL0` or from firmware.

**CPU topology** — `/cpus` has `#address-cells = 2`, `#size-cells = 0`; each CPU `reg` is a 2-cell big-endian value:

| Node | `reg` | `compatible` | `capacity-dmips-mhz` | phandle |
| --- | --- | --- | --- | --- |
| `cpu@0` | `0x0` | `arm,cortex-a55`, `arm,armv8` | 544 (`0x220`) | `0xaa` |
| `cpu@100` | `0x100` | A55 | 544 | `0xac` |
| `cpu@200` | `0x200` | A55 | 544 | `0xae` |
| `cpu@300` | `0x300` | A55 | 544 | `0xb0` |
| `cpu@400` | `0x400` | A55 | 544 | `0xb2` |
| `cpu@500` | `0x500` | A55 | 544 | `0xb4` |
| `cpu@600` | `0x600` | `arm,cortex-a75`, `arm,armv8` | 1024 (`0x400`) | `0xb6` |
| `cpu@700` | `0x700` | A75 | 1024 | `0xb8` |

So MPIDR `Aff1` = 0..7 and `Aff0` = 0 for all eight PEs; there is **no** `Aff2`. `enable-method = psci` on every CPU, no per-CPU `clock-frequency` property.

`/cpus/cpu-map` groups them as `cluster0 = core0..core5` (A55) and `cluster1 = core0..core1` (A75). That grouping is a naming convenience in the ODM DT and does **not** match the `reg` values above (a true cluster map would repeat `Aff0` for cores inside one cluster). For the port, **`reg` is authoritative**: eight distinct `Aff1` values.

**PSCI** — `/psci`: `compatible = "arm,psci-0.2"`, `method = "smc"` (ASCII `smc`), no other properties, no `cpu_suspend`/`cpu_off`/`migrate` cells. `/idle-states` only has `entry-method = "arm,psci"`. So CPU on/off must go through PSCI 0.2 over SMC32/SMC64; there is no HVC conduit.

Same-PPI observation for the XNU port: the SPRD UART raises level-high SPIs 2 and 3, which the GICv3 must route as Group1 NS interrupts before any XNU serial driver can receive them.

**Misc root nodes** (present in live FDT, not used yet): `firmware`, `trusty` (`android,trusty-smc-v1`), `seth@0`..`seth@13`, `hwfeature` (`auto`, `lwfq`), `cpuinfo_hardware` = `T610-Unisoc`, `sprd,sc-id` = `ums512 1000 1000`.

## 3. Memory — RESOLVED from live FDT (2026-11-24)

The earlier "raw DTB 2 GiB vs runtime 4 GiB" conflict is now settled by the live device. The bootloader fixes `/memory` up to the real DDR size.

| Evidence | Value |
| --- | --- |
| `/memory/reg` (live FDT) | base `0x80000000`, size `0xFFFFF000` (~4 GiB) |
| `androidboot.ddrsize` | `4096M`, `androidboot.ddrsize.range=[4096,5120)` |
| `/proc/iomem` | `System RAM 80000000-81feffff`; `namespace0.0 81ff0000-81ffffff`; `System RAM 82000000-17fffefff` |
| Android `MemTotal` | ~`3875088 kB` (~3.7 GiB after reservations) |
| Kernel code / data | `0x80080000` / `0x812c0000` |
| initrd (`chosen`) | `linux,initrd-start=0x82100000`, `linux,initrd-end=0x82a03d10` |
| `sysdump_magic` | `0x82100000` (cmdline) |

**Conclusion:** physical DRAM is `0x80000000`..`0x17FFFFFFF` (4 GiB). The stock base-DTB `2 GiB` `/memory` value is overridden at boot to 4 GiB (consistent with `ddrsize=4096M`). The earlier `/proc/zoneinfo` "two banks" is the normal DMA/Normal split at `0x100000000`, not a second physical DRAM bank.

Reserved-memory regions (live FDT `/reserved-memory`, `#address-cells=2`, `#size-cells=2`):

| Node | Base | Size |
| --- | --- | --- |
| `ddrbist-mem@80000000` | `0x80000000` | `0x00001000` |
| `rebootescrow@0x81ff0000` (no-map) | `0x81ff0000` | `0x00010000` |
| `audio-mem@87500000` | `0x87500000` | `0x00300000` |
| `sipc-mem@87800000` | `0x87800000` | `0x00800000` |
| `sp-ddr-mem@88000000` | `0x88000000` | `0x00300000` |
| `audiodsp-mem@89000000` | `0x89000000` | `0x00600000` |
| `cp-mem@89600000` | `0x89600000` | `0x04900000` |
| `sml-mem@94000000` | `0x94000000` | `0x00040000` |
| `tos-mem@94040000` (reg starts `0x94060000`) | `0x94060000` | `0x04fa0000` |
| `logobuffer@9e000000` | `0x9e000000` | `0x009e4000` |
| `faceid-mem@efaae000` | `0xefaae000` | `0x00500000` |
| `framebuffer-mem@fd708000` | `0xfd708000` | `0x01e5a000` |
| `writeback-mem@ff562000` | `0xff562000` | `0x00a1e000` |
| `ramoops@fff80000` (compatible `ramoops`) | `0xfff80000` | `0x00040000` |
| `debug-mem@100000000` | `0x100000000` | `0x00001000` |
| `debug-mem@844c0000` | `0x844c0000` | `0x00004000` |

The memory **layout** is now proven. `C21Y MemoryMapLib` still stays fail-closed because the boot-handoff facts are separate and not yet proven: FDT pointer/lifetime, firmware ownership, stack/heap, FD window and XNU payload window. Do not fill those from estimates.

## 4. Boot / storage

- Boot device: eMMC `mmcblk0` (~`61071360` KiB, ~58.2 GiB) via `androidboot.boot_devices=soc/soc:ap-apb/71400000.sdio` (SDIO controller at `0x71400000`).
- Rootfs: `root=/dev/ram0 rw` (ramdisk); A/B slots active, `slot_suffix=_a`, `force_normal_boot=1`.
- Key partitions from `/dev/block/by-name`: `boot_a=mmcblk0p40` (64 MiB), `vendor_boot_a=p42` (100 MiB), `dtb_a=p44` (8 MiB), `dtbo_a=p46` (8 MiB), `super=p48` (~8.6 GiB), `vbmeta_a=p54`, `uboot_a=p8`, `trustos_a=p4`, `sml_a=p6`, `misc=p3`, `persist=p23`, `metadata=p56`, `userdata=p75`.

### Boot image header (`boot_a`, raw read-only dump, base/interpretation unproven)

| Field | Raw value |
| --- | --- |
| magic | `ANDROID!` |
| header_version | `2` |
| kernel_size | `0x1496010` (~20.6 MiB) |
| ramdisk_size | `0x903d10` (~9.0 MiB) — equals live initrd size (`0x82a03d10 - 0x82100000`) |
| kernel_addr | `0x8000` |
| ramdisk_addr | `0x5400000` |
| tags_addr | `0x100` |
| page_size | `0x800` |
| boot-image cmdline | `console=ttyS1,115200n8 video=HDMI-A-1:1280x800@60 buildvariant=user` |

These are the header fields baked into the stock boot image. The live boot loaded the ramdisk at `0x82100000` (`chosen/linux,initrd-start`), which does **not** equal `0x80000000 + ramdisk_addr`, so the bootloader's relocation/base convention is **not yet proven**. Do not use these as a BootShim handoff address without further evidence.

### Boot handoff evidence (standard arm64 Linux protocol; not yet verified with XNU)

| Item | Evidence |
| --- | --- |
| DRAM base | `0x80000000` (live FDT `/memory/reg`) |
| Decompressed kernel | `/proc/iomem` `Kernel code 80080000-8100ffff`, `Kernel data 812c0000-81802fff`; consistent with `0x80000000 + TEXT_OFFSET 0x80000` |
| Compressed kernel load | `0x80000000 + kernel_addr(0x8000) = 0x80008000` (header-derived, not directly observed) |
| Initrd | `0x82100000-0x82a03d10` (`chosen/linux,initrd-start/end`) |
| KASLR | no `chosen/kaslr-seed` present |
| `chosen/bootargs_ext` | `androidboot.hardware=S19610AA1 androidboot.dtbo_idx=0` |
| FDT handoff register | standard arm64 Linux: `x0` = FDT pointer (not directly observed) |

This is consistent with the standard arm64 Linux boot protocol, but a BootShim/XNU handoff at `0x80080000` (runtime) / `0x80008000` (load) with `x0`=FDT is **not yet tested** on this device. Treat it as the leading hypothesis, not a verified handoff.

## 4.1 Arm64 CPU / MMU configuration — measured 2026-11-25

Read-only from `/proc/config.gz` (stock kernel config, 28589 bytes gzipped / 4799 lines) and `/proc/timer_list`.

| Kernel option | Value | Meaning for the XNU port |
| --- | --- | --- |
| `CONFIG_ARM64_VA_BITS` | `39` | 512 GiB VA. Matches XNU arm64 `T0SZ`/`T1SZ` 39-bit layout; do **not** assume 48-bit. |
| `CONFIG_ARM64_4K_PAGES` | `y` | 4 KiB granule (`PAGE_SHIFT` 12), same as XNU arm64 on this class of SoC. |
| `CONFIG_PHYS_ADDR_T_64BIT` | `y` | 64-bit `phys_addr_t`; DRAM above 4 GiB is addressable. |
| `CONFIG_ARM64_PAN` | `y` | FEAT_PAN present. |
| `CONFIG_ARM64_UAO` | `y` | FEAT_UAO present. |
| `CONFIG_ARM64_LSE_ATOMICS` | `y` | LSE atomics usable (A55/A75 both have them). |
| `CONFIG_ARM64_HW_AFDBM` | `y` | HW access-flag + dirty-bit management. |
| `CONFIG_UNMAP_KERNEL_AT_EL0` | `y` | Linux uses EL0 trampoline unmapping; XNU has no equivalent and must not assume it. |
| `CONFIG_ARM64_SW_TTBR0_PAN` | `y` | Software PAN fallback compiled in as well. |
| `CONFIG_ARM64_TAGGED_ADDR_ABI` | `y` | Top-byte-ignore ABI enabled (TBI). |
| Errata enabled | `826319`, `827319`, `824069`, `819472`, `845719`, `843419`, `1024718`, `858921` | A55/A75 erratum set the vendor kernel applies. `1024718` and `858921` matter for the A55/A75 mix. |
| `CONFIG_ARM_GIC_V3` | `y`, `ARM_GIC_MAX_NR=1` | Single GIC instance, v3. |
| `CONFIG_ARM_PSCI_FW` | `y` | PSCI firmware driver. |
| `CONFIG_ARM64_PTR_AUTH`, `_BTI`, `_MTE`, `_VHE`, `CONFIG_ARM64_PA_BITS` | absent | Pointer auth, BTI, MTE, VHE and an explicit PA-width option are **not** enabled. Absence of `ARM64_PA_BITS` on 4.14 means the 48-bit default. |
| `CONFIG_ARM_ARCH_TIMER` | `y` (+`_EVTSTREAM`, `_OOL_WORKAROUND`) | Generic timer; event stream and out-of-line workarounds in use. |
| `CONFIG_RANDOMIZE_BASE` | `y` | KASLR active in the stock kernel, yet no `chosen/kaslr-seed` exists in the live FDT — the bootloader is not the entropy source. |
| `CONFIG_CRYPTO_AES_ARM64` | `y` (`_CE`, `_CE_CCM`, `_CE_BLK`, `_NEON_BLK`; not `_BS`) | ARMv8 crypto extensions present; relevant to the port's `SoftwareAES` component choice. |

### Timer frequency derived from the running kernel (not from DT)

`/proc/timer_list`, per-CPU clock event device:

| Field | Value |
| --- | --- |
| `Clock Event Device` | `arch_sys_timer` |
| `set_next_event` | `arch_timer_set_next_event_phys` |
| `mult` | `111669150` |
| `shift` | `32` |
| `min_delta_ns` | `1000` |
| `max_delta_ns` | `82595524660` |

`ns_per_cycle = 2^shift / mult = 2^32 / 111669150 = 38.4615…` ns, so **`CNTFRQ` = 26 000 000 Hz**. This independently confirms the `ext-26m` fixed clock in the DT and matches the 26 MHz reference required by the SPRD UART clock chain. It is a measured value from the live kernel, so the XNU timer setup may use 26 MHz on this board; it is still not proof that XNU reads it correctly.

Also present: a second broadcast clock event device `sprd_timer` (`sprd_timer_set_next_event`, `mult 70369`, `shift 31` ≈ 30 518 ns quantum) used for `tick_handle_oneshot_broadcast` with `tick_broadcast_oneshot_mask = b8` (CPUs 3,4,5,7). Available clocksources: `arch_sys_counter`, `sprd_suspend_timer` (the latter is vendor-specific and has no XNU counterpart).

### GIC SPI assignments confirmed at runtime

From `/proc/interrupts` (GICv3, 3-cell DT encoding → the printed number is the SPI number):

| Printed IRQ | `arch_timer` counterpart | Device | DT node |
| --- | --- | --- | --- |
| `30` | PPI 14 | `arch_timer` | `/timer` (8 CPUs, all incrementing) |
| `103` | SPI 103 | SPRD AON timer | `/soc/aon/timer@32050000` |
| `35` | SPI 35 | `sprd_serial1` | the second SPRD UART |
| `42`, `51`, `52` | SPIs | `mmc0`, `mmc1`, `mmc2` | SDIO/eMMC controllers |
| `58`, `59` | SPIs | `GSP0`, `DISPC` | display subsystem |
| `43`, `44`, `47` | SPIs | `70300000.i2c`, `70400000.i2c`, `70700000.i2c` | I2C |
| `56`, `59`, `62`, `63`, `66` | SPIs | `sprd_dma`, `DISPC`, `DSI_INT0`, `DSI_INT1`, `VSP` | misc |

`arch_timer` shows non-zero counts on **all eight** CPUs, which proves PPI 14 is delivered to every PE and that the GICv3 redistributors for all 8 frames are live.

## 5. Firmware / EDK2

- The EDK2 job in Build #124 and Build #126 succeeded and produced `realme-c21y-uefi-scaffold.fd`.
- `C21Y_FD_BASE=0x80800000` in `.github/workflows/build.yml` is explicitly a compile-time placeholder. The resulting `.fd` is a **scaffold**, not flashable firmware.
- No verified C21Y BootShim handoff address, firmware base, final firmware size, or reserved firmware range is recorded yet.
- The repository `MemoryMapLib` is for EEBBK A2/X2/X2P (`ums512_1h190`), not C21Y (`ums512_1h10`), and must not be reused as a C21Y map.

## 6. What remains unverified

- XNU kernel compile after the unifdef patch (Build #126 in progress).
- Presence and validity of a non-empty `kernel.macho` artifact.
- Any boot on Realme C21Y hardware.
- CPU release/timer/IPI behaviour, SPRD UART console under XNU, GIC routing under XNU.
- Final memory/FDT handoff, firmware ownership, payload window, stack/heap and FD window.
- Display, storage, GPU and modem support.
- Whether XNU's arm64 pmap can run with `VA_BITS=39` + 4 KiB granule as configured here (the values match the stock kernel; XNU's own tables have not been built yet).
- The SPRD UART baud divisor chain from 26 MHz to 115200 is still unproven, even though the 26 MHz reference is now confirmed by `CNTFRQ`.

## 7. Session safety ledger

- 2026-11-24: read-only ADB diagnostics were run against the connected C21Y (`getprop`, `/proc/iomem`, `/proc/cmdline`, `/proc/partitions`, `/proc/device-tree/*`, pulled `/sys/firmware/fdt` and `dmesg`). No `fastboot`, no flash, no reboot, no partition write, no device-side mutation.
- 2026-11-25: read-only ADB again: `/proc/iomem`, `/proc/config.gz` (pulled with `zcat`), `/proc/timer_list`, `/proc/interrupts`, `/sys/devices/system/clocksource/*`, `/proc/device-tree` listing. No write, no reboot, no flash, no `su` side effects beyond reading.
- No memory address, register, offset, reservation or config value was inferred from the unifdef investigation.
- The Build #124 `Parse failure` is a host-tool/source compatibility issue. It says nothing about CPU, GIC, UART, memory or firmware correctness.
