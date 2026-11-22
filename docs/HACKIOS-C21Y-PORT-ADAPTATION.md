# HackiOS XNU port adaptation: Realme C21Y (UMS512)

Status: hardware research and porting specification. This is **not** a
bootable device profile.

## Target decision

- Physical hardware: Realme C21Y RMX3261/RMX3263, Unisoc UMS512 / T610,
  board identity S19610AA1.
- XNU/userland baseline to investigate: HackiOS iOS 16.5, XNU
  `xnu-8796.121.2`.
- Requested iPhone X identity: userspace/device-identity experiment only
  (`iPhone10,3` / `D22AP`). It does not make C21Y Apple A11 hardware and
  must not replace the UMS512 hardware description.
- Hardware facts below are now separated into values parsed from the raw
  C21Y base DTB and values from other runtime/overlay sources.

## What can be reused from JosephMontfort/hackios-xnu-kernel

The HackiOS repository supplies a useful porting architecture:
1. Per-device shell profile in `common/devices/<codename>.conf`.
2. Loader platform descriptor selected by firmware framebuffer base.
3. UEFI port and boot shim that places the XNUP payload at a reserved RAM address.
4. Device-specific driver bring-up sequence: framebuffer first, then
   touch/buttons/CPU, then storage/network/audio/GPU.

It does **not** supply a UMS512 board. HackiOS `redwood` and `garnet`
are Qualcomm Snapdragon devices; their UEFI targets, peripheral windows,
framebuffer addresses, firmware blobs and drivers are not transferable to C21Y.

## C21Y hardware facts

### Directly parsed from stock base DTB

| Field | Value | Evidence / status |
|---|---|---|
| SoC | Unisoc UMS512, compatible `sprd,ums512` | parsed from root node |
| CPU topology | 6x Cortex-A55 + 2x Cortex-A75 | parsed from `/cpus` |
| CPU MPIDRs | `0x0, 0x100, ... 0x700` | parsed from CPU `reg` |
| CPU enable method | PSCI | parsed from CPU nodes; runtime behavior untested |
| GIC | ARM GICv3 | parsed from interrupt-controller node |
| GICD | `0x12000000`, size `0x20000` | parsed from `reg` |
| GICR | `0x12040000`, size `0x100000` | parsed from `reg` |
| GICR stride | `0x20000` | parsed from `redistributor-stride` |
| UART 0 | `0x70000000`, size `0x100` | enabled Unisoc UART |
| UART console | `0x70100000`, size `0x100` | enabled; selected by `/chosen/stdout-path` |
| DPU | `0x20300000`, size `0x1000` | parsed; node status okay |
| DSI | `0x20400000`, size `0x1000` | parsed; node status okay |
| Raw DTB RAM | `0x80000000 + 0x80000000` | 2 GiB in base DTB only |

### Evidence from overlay and running Android

| Field | Value | Limitation |
|---|---|---|
| Board identity | `S19610AA1` / overlay compatible `sprd,S19610AA1` | board identity match |
| Android DRAM coverage | about 2 GiB at `0x80000000` and almost 2 GiB at `0x100000000` | derived from Android `/proc/zoneinfo`; not a UEFI usable map |
| Logo buffer | `0x9e000000`, size `0x9e4000` | overlay reservation; GOP handoff unverified |
| Framebuffer | `0xfd708000`, size `0x1e5a000` | overlay reservation; pixel format/stride/ownership unverified |
| Face ID | `0xefaae000`, size `0x500000` | overlay reservation |
| Writeback | `0xff562000`, size `0xa1e000` | overlay reservation |

The raw base DTB describes only the first 2 GiB, while Android's runtime
zone data shows a second populated range starting at 4 GiB. The final
bootloader FDT/memory handoff remains unresolved. Do not construct a
contiguous or UEFI-usable RAM map from these observations alone.

More details and all base reserved-memory entries are in
[`stock-firmware-audit.md`](stock-firmware-audit.md).

## Draft HackiOS platform descriptor — not ready to compile

The verified static GIC register values and CPU count can inform a draft,
but the descriptor must not be integrated until the loader's assumptions
and runtime handoff are validated:

```c
static const struct platform platform_c21y = {
    .name = "c21y",
    .io_base = TODO_C21Y_PERIPHERAL_BASE,
    .io_size = TODO_C21Y_PERIPHERAL_SIZE,
    .gic_dist = 0x12000000,
    .gic_redist = 0x12040000,
    .uart = 0, /* loader must support Unisoc UART; not assumed PL011 */
    .log_other_cpu = 1,
    .cores = 8,
    .core_shift = 8,
    .small_cores = 0x3f, /* six A55 cores; validate loader MPIDR semantics */
    .fb_base = TODO_VERIFIED_UEFI_GOP_FRAMEBUFFER,
};
```

The `io_base/io_size`, UART driver mapping and framebuffer base are
intentionally unresolved. Do not substitute Qualcomm peripheral windows
or assume the overlay's framebuffer reservation is a working GOP surface.

## Draft device profile — not executable

- `NAME="Realme C21Y RMX3261 (c21y)"`
- `KIND=phone`
- `SOC="Unisoc UMS512 / T610"`
- `UEFI_TARGET=c21y` — requires a new C21Y UEFI target/package.
- `DTB=<merged and validated C21Y live DTB>`
- `FD_BASE=<verified boot-shim destination>`
- `FD_SIZE=<measured firmware image size>`
- `PAYLOAD_BASE=<verified free RAM range>`
- `FB_BASE=<verified UEFI GOP framebuffer>`
- `WIFI_ATH11K=0` — Qualcomm ath11k is not the C21Y radio driver.
- Initial boot arguments should enable only proven CPU/interrupt/logging
  paths; no Qualcomm-specific touch, cpufreq, Wi-Fi, audio or GPU switches.

## Why the current UniXNU branch is not automatically HackiOS-compatible

The existing C21Y repository uses the UniXNU board/defconfig/profile resolver
and currently selects an iPadOS 17.7.11 profile. HackiOS uses a different XNU
tree, loader ABI, payload format, userland build, UEFI shim and per-device
configuration system. Changing only `os_profile` or copying a `.conf`
does not switch the kernel implementation to HackiOS iOS 16.5.

For an actual HackiOS experiment, port the C21Y hardware into a separate
HackiOS worktree first. Keep the existing UniXNU branch intact until the
HackiOS loader and UEFI can be built and audited independently.

## Next gates, in order

1. Obtain/validate the final live C21Y FDT after bootloader fixups and
   correctly apply the stock DTBO overlay.
2. Establish exact boot-shim/UEFI load address, firmware size and reserved
   memory ownership.
3. Reconcile all RAM banks and carve-outs; Android's 4 GiB coverage is not
   equivalent to 4 GiB of free conventional memory.
4. Build a C21Y UEFI target and prove it starts the loader without writing
   partitions.
5. Add the C21Y loader platform and confirm GIC, CPU topology and framebuffer
   at runtime.
6. Bring up XNU with logging/framebuffer only; add touch, storage and other
   drivers separately.
7. Only after a repeatable RAM-only boot should a boot image be considered.

**Do not flash incomplete firmware.**

## Upstream references

- HackiOS kernel and loader: https://github.com/JosephMontfort/hackios-xnu-kernel
- HackiOS porting guide: https://github.com/JosephMontfort/hackios-xnu-kernel/blob/main/docs/PORTING.md
- HackiOS device profiles: https://github.com/JosephMontfort/hackios-xnu-kernel/tree/main/common/devices
- Existing C21Y board branch: https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/tree/port/realme-c21y-rmx3261
