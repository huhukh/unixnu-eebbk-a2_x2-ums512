# FDL2 RAM/FDT Static Triage

Date: 2026-11-23

## Scope and artifact identity

Read-only analysis of firmware package _DLFiles_126C_A25C06_0:

| Artifact | Manifest role | Size | SHA-256 |
| --- | --- | ---: | --- |
| fdl2-sign.bin | FDL2 | 888,548 | c1dbff5b6f1d8c91ae3f8e4ae59df54a0bfc35611b5fb60b72c8dcd4a1cd2922 |
| u-boot-sign.bin | UBOOTLOADER | 888,548 | 37e01de6b0d87df33ba1e4258b54bf6a6d71805c2da606d949383cfaf22d2f5d |

FileList.ini maps FDL2 to the first file and UBOOTLOADER to the second. The two files have equal lengths and are byte-identical except for the 256-byte interval [0xd8de4, 0xd8ee4); the prefix and suffix outside that interval match. This directly ties the examined code payload to the package's normal-boot U-Boot image, though it does not prove the currently installed device partition is byte-for-byte identical to this package.

- Both image headers begin with bytes 44 48 54 42 01 (DHTB, version-like field); neither file is an ELF executable.
- The byte sequence 7f 45 4c 46 occurs at offset 0x94c9a, but the following bytes are printable text (\0sprd_dump\0...). It is not an ELF header and must not be used to infer a load address or architecture.
- AArch64 disassembly is plausible in executable-looking regions; this is a static triage, not a full image unpack or symbolized reverse engineering.

## Read-only runtime properties

On 2026-11-23, ADB identified the connected handset as RMX3261. Read-only Android boot properties returned:

| Property | Value |
| --- | --- |
| ro.boot.ddrsize | 4096M |
| ro.boot.ddrsize.range | [4096,5120) |
| ro.boot.hardware | S19610AA1 |
| ro.boot.board_id | S19610BA1 |
| ro.boot.product.hardware.sku | S19610BA1 |
| ro.boot.slot_suffix | _a |
| ro.boot.dynamic_partitions | true |
| ro.boot.vbmeta.device_state | unlocked |

The boot properties corroborate a reported 4 GiB DRAM capacity. They do not disclose the physical bank layout, firmware reservations, or a UEFI memory map. The S19610AA1 hardware property and S19610BA1 board/SKU properties differ; reconcile these with the stock DTBO and board descriptors before hard-coding board identity. /proc/cmdline was permission denied and /proc/bootconfig was absent to the unprivileged ADB shell; no access escalation was attempted.

## Findings

The identical code in both package files contains:

- fdt_fixup_ddr_size at file offset 0x81440
- get real ram size: 0x%lx\n at 0x8b51d
- dram_size_inMB:%u\n at 0x8b537
- Board string S19610AA1

It does not contain the literal strings get_real_ram_size, chipram_env, cs0_size, cs1_size, cs_number, or DDR_AUTO_DETECT. Their absence does not establish that the corresponding code or data is absent; firmware may use different names or binary structures.

An AArch64 PC-relative reference at file offsets 0x51f64–0x51f68 resolves to the fdt_fixup_ddr_size text at 0x81440. This reference is in a diagnostic/logging path and, by itself, does not prove that the successful FDT memory-size fixup ran on this handset. The presence of the size log strings proves only that related code/messages are present, not the runtime size or final RAM map. Separately, docs/stock-firmware-audit.md records a disassembly of the U-Boot image-preparation path that calls the FDT /memory/reg update routine and matches the live Android FDT result.

## Conclusion for the port

The exact package U-Boot image contains the same relevant code payload as FDL2, and the runtime boot property independently reports 4 GiB. Together with the live Android FDT and the U-Boot image-preparation path documented in docs/stock-firmware-audit.md, this is strong evidence that the package's normal-boot U-Boot updates the memory description from a RAM-size value.

It does **not** establish:

- that the currently installed U-Boot partition matches this package image byte-for-byte;
- the producer/ABI of the RAM-size global or its exact runtime input;
- the final FDT pointer and its lifetime at a custom UEFI entry;
- UEFI ownership/reservations for the complete RAM range;
- safe UEFI FD, stack, heap, payload, or usable-memory ranges; or
- a validated C21Y UEFI memory map.

Keep MemoryMapLib fail-closed until those are measured or derived from the actual C21Y boot contract. Do not use the FDT /memory/reg range as a UEFI usable map without subtracting and validating all firmware-owned/reserved areas.

## Reproduction

On the Windows host, hash both images and compare their bytes; inspect FileList.ini to verify package roles. Use a binary parser/disassembler and record file offsets, distinguishing strings from executable references. Read boot properties with adb shell getprop <property>. Do not flash or execute FDL2 as part of this analysis.
