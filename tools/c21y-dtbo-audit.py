#!/usr/bin/env python3
"""Extract the C21Y overlay from Android dtbo.img and merge it with a stock DTB.

This tool is intentionally read-only with respect to the supplied firmware files.
It writes extracted/merged artifacts only into the selected output directory.
Requires: Python 3.10+ and device-tree-compiler (fdtoverlay + dtc).
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
from pathlib import Path

DT_TABLE_MAGIC = 0xD7B7AB1E
FDT_MAGIC = 0xD00DFEED
TARGET_COMPATIBLE = b"sprd,S19610AA1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_fdt(data: bytes, label: str) -> bytes:
    if len(data) < 40:
        raise ValueError(f"{label}: shorter than an FDT header")
    magic, total_size = struct.unpack_from(">II", data, 0)
    if magic != FDT_MAGIC:
        raise ValueError(f"{label}: invalid FDT magic 0x{magic:08x}")
    if total_size < 40 or total_size > len(data):
        raise ValueError(
            f"{label}: invalid FDT totalsize {total_size} for {len(data)} bytes"
        )
    return data[:total_size]


def extract_target_overlay(image: bytes) -> tuple[bytes, dict[str, int]]:
    if len(image) < 32:
        raise ValueError("dtbo.img is shorter than dt_table_header")
    fields = struct.unpack_from(">8I", image, 0)
    magic, total_size, header_size, entry_size, entry_count, entries_offset, page_size, version = fields
    if magic != DT_TABLE_MAGIC:
        raise ValueError(f"not an Android DT table (magic=0x{magic:08x})")
    if header_size < 32 or entry_size < 32:
        raise ValueError("invalid DT table header/entry size")
    if total_size > len(image) or total_size < header_size:
        raise ValueError("DT table total_size is outside the input image")
    entries_end = entries_offset + entry_count * entry_size
    if entries_offset < header_size or entries_end > total_size:
        raise ValueError("DT table entry array is out of bounds")

    matches: list[tuple[bytes, dict[str, int]]] = []
    for index in range(entry_count):
        pos = entries_offset + index * entry_size
        dt_size, dt_offset, board_id, revision, c0, c1, c2, c3 = struct.unpack_from(
            ">8I", image, pos
        )
        end = dt_offset + dt_size
        if dt_size < 40 or dt_offset < header_size or end > total_size:
            raise ValueError(f"DT table entry {index} has an invalid payload range")
        blob = check_fdt(image[dt_offset:end], f"DTBO entry {index}")
        if TARGET_COMPATIBLE in blob:
            matches.append((blob, {
                "index": index, "size": len(blob), "offset": dt_offset,
                "id": board_id, "rev": revision, "custom0": c0,
                "custom1": c1, "custom2": c2, "custom3": c3,
            }))

    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one overlay containing {TARGET_COMPATIBLE.decode()}, "
            f"found {len(matches)}"
        )
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dtb", required=True, type=Path,
                        help="extracted stock_boot_dtb.dtb (or matching boot.img DTB)")
    parser.add_argument("--dtbo", required=True, type=Path, help="stock dtbo.img")
    parser.add_argument("--out", type=Path, default=Path("c21y-fdt-audit"),
                        help="output directory (default: c21y-fdt-audit)")
    args = parser.parse_args()

    for executable in ("fdtoverlay", "dtc"):
        if shutil.which(executable) is None:
            parser.error(f"required executable not found: {executable}")
    if not args.base_dtb.is_file() or not args.dtbo.is_file():
        parser.error("both --base-dtb and --dtbo must point to existing files")

    args.out.mkdir(parents=True, exist_ok=True)
    base_bytes = check_fdt(args.base_dtb.read_bytes(), "base DTB")
    overlay, metadata = extract_target_overlay(args.dtbo.read_bytes())

    base = args.out / "base.dtb"
    overlay_path = args.out / "S19610AA1-overlay.dtbo"
    merged = args.out / "merged-S19610AA1.dtb"
    merged_dts = args.out / "merged-S19610AA1.dts"
    base.write_bytes(base_bytes)
    overlay_path.write_bytes(overlay)

    subprocess.run(
        ["fdtoverlay", "-v", "-i", str(base), "-o", str(merged), str(overlay_path)],
        check=True,
    )
    subprocess.run(
        ["dtc", "-I", "dtb", "-O", "dts", "-o", str(merged_dts), str(merged)],
        check=True,
    )

    print("C21Y stock DTB + S19610AA1 DTBO merge: SUCCESS")
    print(f"DTBO entry: {metadata}")
    print(f"base sha256: {sha256(args.base_dtb)}")
    print(f"dtbo sha256: {sha256(args.dtbo)}")
    print(f"merged sha256: {sha256(merged)}")
    print(f"merged DTB: {merged}")
    print(f"merged DTS: {merged_dts}")
    print()
    print("Memory and reservation nodes in merged DTS:")
    lines = merged_dts.read_text(errors="replace").splitlines()
    for number, line in enumerate(lines, 1):
        if any(token in line for token in (
            "memory@", "device_type = \"memory\"", "reserved-memory",
            "reg = <", "no-map", "reusable",
        )):
            print(f"{number}: {line.strip()}")
    print()
    print("NOTE: this merge does not prove the bootloader's live FDT or UEFI map.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
