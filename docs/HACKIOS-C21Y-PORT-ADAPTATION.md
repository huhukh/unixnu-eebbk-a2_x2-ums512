# HackiOS XNU port adaptation: Realme C21Y (UMS512)

Status: research/porting specification only. This is **not** a bootable device profile.

## Target decision

- Physical hardware: Realme C21Y RMX3261, Unisoc UMS512 / T610 (SharkL5Pro).
- XNU/userland baseline to investigate: HackiOS iOS 16.5, XNU `xnu-8796.121.2`.
- Requested iPhone X identity: a userspace/device identity experiment only (`iPhone10,3` / `D22AP`). It does not make the C21Y an Apple A11 device and must not replace the C21Y hardware description.
- Hardware board data must come from the C21Y live DTB/vendor firmware, not from HackiOS's Qualcomm `redwood` or `garnet` profiles.

## What can be reused from JosephMontfort/hackios-xnu-kernel

The HackiOS repository supplies a useful *porting architecture*:
1. A per-device shell profile in `common/devices/<codename>.conf`.
2. A loader platform descriptor selected by firmware framebuffer base.
3. A UEFI port and boot shim that places the XNUP payload at a reserved RAM address.
4. A device-specific driver bring-up sequence: framebuffer first, then touch/buttons/CPU, then storage/network/audio/GPU.

It does **not** supply a UMS512 board. `redwood` and `garnet` are Qualcomm Snapdragon devices; their UEFI targets, peripheral windows, framebuffer addresses, firmware blobs and drivers are not transferable to C21Y.

## C21Y facts currently available

From the C21Y UMS512 DTS and prior stock-device inspection:

| Field | Current evidence | Porting status |
|---|---|---|
| SoC | UMS512 / T610, SharkL5Pro | known |
| CPU topology | 6x Cortex-A55 + 2x Cortex-A75 | source-derived; verify live DTB |
| MPIDR values | 0x0, 0x100, ... 0x700 | source-derived |
| GICD | 0x12000000 | source-derived |
| GICR | 0x12040000 | source-derived; 8 frames |
| UART | 0x70100000 | source-derived; serial mapping still needs validation |
| PSCI | SMC | source-derived; verify firmware behavior |
| Bootloader framebuffer | 0x9e000000, size 0x9e4000 | source-derived; UEFI GOP handoff must confirm |
| RAM | Android reports 4 GiB; raw DTB describes 2 GiB at 0x80000000 | unresolved final live map and reservations |
| UEFI FD base/size | not established | BLOCKER |
| XNUP payload base/window | not established | BLOCKER |
| Peripheral I/O window | not established as a safe contiguous range | BLOCKER |
| Touch panel / input | C21Y-specific wiring and driver not integrated | BLOCKER |
| Storage | C21Y-specific UFS/eMMC path not qualified | BLOCKER |

The GIC, CPU, UART and framebuffer entries above are starting evidence, not permission to program them blindly. The loader's runtime values and the final C21Y live FDT must agree.

## Draft HackiOS platform descriptor (values intentionally not guessed)

The descriptor should be added to HackiOS `xnuloader/loader.c` only after the TODO fields are proven:

```c
static const struct platform platform_c21y = {
    .name = "c21y",
    .io_base = TODO_C21Y_PERIPHERAL_BASE,
    .io_size = TODO_C21Y_PERIPHERAL_SIZE,
    .gic_dist = 0x12000000,
    .gic_redist = 0x12040000,
    .uart = 0, /* verify the loader's UART implementation; C21Y UART is not PL011 */
    .log_other_cpu = 1,
    .cores = 8,
    .core_shift = 8,
    .small_cores = 0x3f, /* 6 A55 little cores, subject to live MPIDR verification */
    .fb_base = 0x9e000000, /* accept only if UEFI GOP reports this exact base */
};
```

The `io_base/io_size` pair above is deliberately left unresolved. Do not copy the broad Qualcomm range from `redwood` or `garnet`.

## Draft device profile (not executable yet)

The following fields are the intended shape, not a usable `.conf`:

- `NAME="Realme C21Y RMX3261 (c21y)"`
- `KIND=phone`
- `SOC="Unisoc UMS512 / T610"`
- `UEFI_TARGET=c21y` — requires a new UEFI target/package.
- `DTB=<exact C21Y live DTB>`
- `FD_BASE=<verified boot-shim destination>`
- `FD_SIZE=<measured firmware image size>`
- `PAYLOAD_BASE=<verified free RAM range>`
- `FB_BASE=<UEFI GOP framebuffer base, confirm against 0x9e000000>`
- `WIFI_ATH11K=0` — Qualcomm ath11k is not the C21Y radio driver.
- Initial `BOOTARGS` should enable only the verified CPU/framebuffer path; no Qualcomm-specific touchscreen, cpufreq, Wi-Fi, audio or GPU switches.

## Why the current UniXNU branch is not automatically HackiOS-compatible

The existing C21Y repository uses the UniXNU board/defconfig/profile resolver and currently selects an iPadOS 17.7.11 profile. HackiOS uses a different XNU tree, loader ABI, payload format, userland build, UEFI shim and per-device configuration system. Changing only `os_profile` or copying a `.conf` file does not switch the kernel implementation to HackiOS iOS 16.5.

For an actual HackiOS experiment, port the C21Y hardware into a separate HackiOS worktree first. Keep the existing UniXNU branch intact until the HackiOS loader and UEFI can be built and audited independently.

## Next gates, in order

1. Export the **live** C21Y FDT from the running stock firmware and compare it with the static DTS.
2. Establish the exact boot-shim/UEFI load address, firmware size and reserved memory ownership.
3. Reconcile all RAM banks and carve-outs; never assume the Android-reported 4 GiB is all free.
4. Build a C21Y UEFI target and prove that it can start the HackiOS loader without writing partitions.
5. Add the C21Y loader platform and confirm its reported GIC, CPU topology and framebuffer at runtime.
6. Bring up XNU with framebuffer/logging only. Add touch, storage and other drivers separately.
7. Only after a repeatable RAM-only boot should a boot image be considered. Do not flash incomplete firmware.

## Upstream references

- HackiOS kernel and loader: https://github.com/JosephMontfort/hackios-xnu-kernel
- HackiOS porting guide: https://github.com/JosephMontfort/hackios-xnu-kernel/blob/main/docs/PORTING.md
- HackiOS device profiles: https://github.com/JosephMontfort/hackios-xnu-kernel/tree/main/common/devices
- Existing C21Y board branch: https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/tree/port/realme-c21y-rmx3261
