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

## 7. Session safety ledger

- 2026-11-24: read-only ADB diagnostics were run against the connected C21Y (`getprop`, `/proc/iomem`, `/proc/cmdline`, `/proc/partitions`, `/proc/device-tree/*`, pulled `/sys/firmware/fdt` and `dmesg`). No `fastboot`, no flash, no reboot, no partition write, no device-side mutation.
- No memory address, register, offset, reservation or config value was inferred from the unifdef investigation.
- The Build #124 `Parse failure` is a host-tool/source compatibility issue. It says nothing about CPU, GIC, UART, memory or firmware correctness.
