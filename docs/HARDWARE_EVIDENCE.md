# HARDWARE_EVIDENCE — Realme C21Y RMX3261 / UMS512

This file separates verified device observations from build artifacts and from assumptions. Presence here is **not** a claim that XNU boots or that a peripheral is supported.

## 1. Device identity

| Observation | Value | Source |
| --- | --- | --- |
| Board name used by this port | `realme-c21y-rmx3261` | `board.toml`, `porting.toml` |
| SoC | Unisoc UMS512 / SharkL5Pro, marketing T610 | `board.toml`, vendor sources |
| Board platform string | `ums512_1h10` | C21Y device-tree references |
| `ro.boot.hardware` | `S19610AA1` | Stock firmware audit |
| `ro.boot.board_id` | `S19610BA1` | Stock firmware audit |
| `ro.boot.product.hardware.sku` | `S19610BA1` | Stock firmware audit |
| DTBO compatible | `sprd,S19610AA1` | DTBO audit |
| Stock kernel | Linux `4.14.193` | Official Realme kernel source |
| Target XNU | `8796.121.2` / Darwin `22.5`, iOS `16.5` build `20F66` | `os-profiles/ios-16.5-20F66/profile.toml` |

`iPhone10,3` / `D22AP` in the OS profile is a software identity chosen for iOS compatibility. It is **not** the C21Y hardware identity and must not be reported as such.

## 2. CPU and interrupt controller

| Item | Verified value |
| --- | --- |
| CPU topology | 6× Cortex-A55 + 2× Cortex-A75 |
| MPIDR values | `0x0`–`0x700`, step `0x100` |
| GIC version | GICv3 |
| GICD | base `0x12000000`, size `0x20000` |
| GICR | base `0x12040000`, size `0x100000`, stride `0x20000` |
| UART console | `0x70100000` + `0x100` |
| Second UART | `0x70000000` + `0x100` |

These values come from the stock/firmware and DTS audits already recorded in `docs/stock-firmware-audit.md`, `docs/C21Y-STOCK-DTB-MEMORY-INSPECTION.md` and `docs/C21Y-BOOT-HANDOFF-RESEARCH.md`. They are hardware facts, not proof of XNU driver support.

## 3. Memory — unresolved conflict, no estimates

| Evidence | Value |
| --- | --- |
| Raw stock base DTB `/memory/reg` | `0x80000000 + 0x80000000` (2 GiB) |
| Public vendor `ums512-mach.dtsi` | 2 GiB at `0x80000000` |
| Matching S19610AA1 board overlay | Adds reservations; does not enlarge the memory node |
| Live Android FDT `/memory/reg` | `0x80000000 + 0xfffff000` |
| `ro.boot.ddrsize` | `4096M` |
| Android `MemTotal` | about `3875088 kB` |
| `/proc/zoneinfo` | DMA zone from PFN `524288`, 524288 pages; Normal zone from PFN `1048576`, 524287 pages; with 4 KiB pages these are adjacent ~2 GiB ranges starting at `0x80000000` and `0x100000000` |

The raw-DTB and live-FDT/runtime values conflict. A bootloader-side live fixup is plausible but unproven. Do **not** fill the second bank, firmware reservations or memory-map holes from estimates. C21Y `MemoryMapLib` must remain fail-closed until FDT pointer/lifetime, ownership, reservations, stack/heap, FD and payload windows are proven.

## 4. Firmware / EDK2

- The EDK2 job in Build #124 succeeded and produced `realme-c21y-uefi-scaffold.fd`.
- `C21Y_FD_BASE=0x80800000` in `.github/workflows/build.yml` is explicitly a compile-time placeholder. The resulting `.fd` is a **scaffold**, not flashable firmware.
- No verified C21Y BootShim handoff address, firmware base, final firmware size, or reserved firmware range is recorded.
- The repository `MemoryMapLib` is for EEBBK A2/X2/X2P (`ums512_1h190`), not C21Y (`ums512_1h10`), and must not be reused as a C21Y map.

## 5. Session safety ledger

- No `fastboot`, `adb`, flashing, reboot, partition write or device-side command was run in this session.
- No memory address, register, offset, reservation or config value was inferred from the unifdef investigation.
- The Build #124 `Parse failure` is a host-tool/source compatibility issue. It says nothing about CPU, GIC, UART, memory or firmware correctness.

## 6. What remains unverified

- XNU kernel compile after the patch (pending new GitHub Actions run).
- Presence and validity of a `kernel.macho` artifact.
- Any boot on Realme C21Y hardware.
- CPU release/timer/IPI behaviour, SPRD UART console under XNU, GIC routing.
- Final memory/FDT handoff, payload window and firmware ownership.
- Display, storage, GPU and modem support.
