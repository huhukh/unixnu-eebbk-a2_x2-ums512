# C21Y stock DTB/DTBO merge audit

This procedure is offline and read-only with respect to the supplied firmware.
It does not flash, repack, or modify `boot.img` / `dtbo.img`.

## Inputs

- `stock_boot_dtb.dtb`: base FDT extracted from the stock RMX3261 A.119 boot image.
- `dtbo.img`: stock Android DT table containing the S19610AA1 overlay.

The repository's stock audit recorded a 152,721-byte Android DT table inside
`boot.img`, with a 152,657-byte base FDT matching the supplied
`stock_boot_dtb.dtb` after ignoring its 64-byte zero padding. The DTBO
image has one entry, whose compatible string is `sprd,S19610AA1`.
Re-run the checks below against the original files before treating the merge
as a reproducible result.

## Run on Ubuntu / WSL

Install the device-tree compiler utilities:

```bash
sudo apt update
sudo apt install -y device-tree-compiler
```

From the repository root:

```bash
python3 tools/c21y-dtbo-audit.py \
  --base-dtb /path/to/stock_boot_dtb.dtb \
  --dtbo /path/to/dtbo.img \
  --out out/c21y-fdt-audit
```

The tool validates the Android DT table bounds, selects exactly one FDT overlay
containing `sprd,S19610AA1`, extracts it, and invokes `fdtoverlay`
to create `merged-S19610AA1.dtb` and its decompiled DTS. It prints
SHA-256 hashes and memory/reserved-memory lines for review.

## Interpretation limits

- A successful `fdtoverlay` merge proves only that this overlay can be
  applied structurally to this base FDT.
- The stock DTB's memory node describes 2 GiB at `0x80000000`, while
  Android runtime zoneinfo showed a second populated range beginning at
  `0x100000000`. The merge alone cannot explain that second range.
- The bootloader's live FDT and exact UEFI handoff are still needed before
  creating a C21Y `MemoryMapLib` or changing the DTS memory node.
- Do not flash any output from this audit.

## Android DT table format

The parser follows the Android `dt_table_header` / `dt_table_entry`
layout documented by AOSP. The overlay merge uses `fdtoverlay` from
`device-tree-compiler` (libfdt).
