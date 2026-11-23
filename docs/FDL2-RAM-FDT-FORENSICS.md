# FDL2 RAM/FDT Static Triage

Date: 2026-11-23

## Scope and artifact identity

Read-only analysis of the handset firmware FDL2:

- Path on the Windows host: `E:\Alat flash\ios\SPD_Upgrade_Tool_R27.25.4601\ImageFiles\_DLFiles_126C_A25C06_0\fdl2-sign.bin`
- Size: 888,548 bytes
- SHA-256: `c1dbff5b6f1d8c91ae3f8e4ae59df54a0bfc35611b5fb60b72c8dcd4a1cd2922`
- Image header begins with bytes `44 48 54 42 01` (`DHTB`, version-like field); this is not an ELF file.
- The byte sequence `7f 45 4c 46` occurs at offset `0x94c9a` inside the image, but the following bytes are printable text (`\0sprd_dump\0...`). It is not an ELF header and must not be used to infer a load address or architecture.
- AArch64 disassembly is plausible in executable-looking regions; this is a static triage, not a full image unpack or symbolized reverse engineering.

## Findings

The image contains:

- `fdt_fixup_ddr_size` at file offset `0x81440`
- `get real ram size: 0x%lx\n` at `0x8b51d`
- `dram_size_inMB:%u\n` at `0x8b537`
- Board string `S19610AA1`

It does not contain the literal strings `get_real_ram_size`, `chipram_env`, `cs0_size`, `cs1_size`, `cs_number`, or `DDR_AUTO_DETECT`. Their absence does not establish that the corresponding code or data is absent; firmware may use different names or binary structures.

An AArch64 PC-relative reference at file offsets `0x51f64–0x51f68` resolves to the `fdt_fixup_ddr_size` text at `0x81440`. This reference is in a diagnostic/logging path and, by itself, does not prove that the successful FDT memory-size fixup ran on this handset. The presence of the size log strings proves only that related code/messages are present in the image, not the runtime size or final RAM map.

## Conclusion for the port

This artifact strengthens the evidence that the handset's firmware includes DDR/FDT-related code for the S19610AA1 family. Combined with the live Android FDT and the referenced U-Boot implementation documented in [stock-firmware-audit.md](stock-firmware-audit.md), it supports the hypothesis that the boot chain updates the FDT memory node from detected DRAM size.

It does **not** establish:

- the exact FDL2 execution path or whether this FDL2 image is the final U-Boot stage used for normal Android boot;
- the final FDT pointer and its lifetime at a custom UEFI entry;
- UEFI ownership/reservations for the complete RAM range;
- safe UEFI FD, stack, heap, payload, or usable-memory ranges; or
- a validated C21Y UEFI memory map.

Keep `MemoryMapLib` fail-closed until those are measured or derived from the actual C21Y boot contract. Do not use the FDT `/memory/reg` range as a UEFI usable map without subtracting and validating all firmware-owned/reserved areas.

## Reproduction

On the Windows host, use a read-only SHA-256 check and a binary parser/disassembler. Record file offsets and distinguish strings from executable cross-references. Do not flash or execute FDL2 as part of this analysis.
