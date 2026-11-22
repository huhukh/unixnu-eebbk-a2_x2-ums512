#!/usr/bin/env python3
"""Inspect memory and reserved-memory nodes in a flattened device tree (FDT).

Uses only Python's standard library; no dtc/libfdt dependency.
This is an evidence-gathering tool, not a memory-map generator.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

MAGIC = 0xD00DFEED
BEGIN_NODE, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def align4(value: int) -> int:
    return (value + 3) & ~3


def decode_string(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("utf-8", "replace")


def parse_fdt(blob: bytes):
    if len(blob) < 40 or u32(blob, 0) != MAGIC:
        raise ValueError("Not a valid FDT: missing 0xd00dfeed header")
    total = u32(blob, 4)
    off_struct, off_strings, off_reserve = u32(blob, 8), u32(blob, 12), u32(blob, 16)
    version, last_compat = u32(blob, 20), u32(blob, 24)
    size_strings, size_struct = u32(blob, 32), u32(blob, 36)
    if total > len(blob) or total < 40:
        raise ValueError(f"Invalid FDT total size {total} for file size {len(blob)}")
    if off_struct + size_struct > total or off_strings + size_strings > total:
        raise ValueError("FDT structure/string block extends beyond total size")

    strings = blob[off_strings:off_strings + size_strings]
    struct_end = off_struct + size_struct
    pos = off_struct
    stack = []
    nodes = []
    while pos + 4 <= struct_end:
        token = u32(blob, pos)
        pos += 4
        if token == BEGIN_NODE:
            end = blob.find(b"\0", pos, struct_end)
            if end < 0:
                raise ValueError("Unterminated FDT node name")
            name = decode_string(blob[pos:end])
            pos = off_struct + align4(end + 1 - off_struct)
            parent = stack[-1] if stack else None
            path = (parent["path"].rstrip("/") + "/" + name) if parent and parent["path"] != "/" else "/" + name
            node = {"name": name, "path": path, "parent": parent, "props": {}}
            nodes.append(node)
            stack.append(node)
        elif token == END_NODE:
            if not stack:
                raise ValueError("Unbalanced FDT END_NODE")
            stack.pop()
        elif token == PROP:
            if not stack or pos + 8 > struct_end:
                raise ValueError("Malformed FDT property")
            length, nameoff = struct.unpack_from(">II", blob, pos)
            pos += 8
            if nameoff >= len(strings) or pos + length > struct_end:
                raise ValueError("FDT property outside string/structure block")
            name_end = strings.find(b"\0", nameoff)
            if name_end < 0:
                raise ValueError("Unterminated FDT property name")
            prop_name = decode_string(strings[nameoff:name_end])
            stack[-1]["props"][prop_name] = blob[pos:pos + length]
            pos = off_struct + align4(pos + length - off_struct)
        elif token == NOP:
            continue
        elif token == END:
            break
        else:
            raise ValueError(f"Unknown FDT structure token 0x{token:08x}")
    if stack:
        raise ValueError("Unclosed FDT node")
    return total, version, last_compat, nodes


def cells_value(raw: bytes, count: int):
    if count < 1 or count > 4 or len(raw) != count * 4:
        return None
    value = 0
    for i in range(count):
        value = (value << 32) | u32(raw, i * 4)
    return value


def reg_entries(node):
    parent = node["parent"]
    if not parent:
        return []
    ac = cells_value(parent["props"].get("#address-cells", b""), 1)
    sc = cells_value(parent["props"].get("#size-cells", b""), 1)
    # Device-tree defaults are 2 address cells and 1 size cell.
    ac = ac if ac is not None else 2
    sc = sc if sc is not None else 1
    raw = node["props"].get("reg")
    if raw is None or ac + sc == 0 or len(raw) % ((ac + sc) * 4):
        return []
    result = []
    stride = (ac + sc) * 4
    for off in range(0, len(raw), stride):
        addr = cells_value(raw[off:off + ac * 4], ac)
        size = cells_value(raw[off + ac * 4:off + stride], sc)
        result.append((addr, size))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dtb", type=Path, help="input .dtb file")
    args = ap.parse_args()
    blob = args.dtb.read_bytes()
    total, version, compat, nodes = parse_fdt(blob)
    print(f"FDT OK: {args.dtb} | total={total} bytes | version={version} | last-compatible={compat}")
    selected = []
    for node in nodes:
        path = node["path"]
        if path == "/memory" or path.startswith("/memory@") or path == "/reserved-memory" or path.startswith("/reserved-memory/"):
            selected.append(node)
    if not selected:
        print("No /memory or /reserved-memory nodes found.")
        return 2
    for node in selected:
        print(f"\n[{node['path']}]")
        for key in ("device_type", "status", "compatible", "no-map", "reusable", "ranges", "linux,usable-memory"):
            if key in node["props"]:
                value = node["props"][key]
                print(f"  {key} = {decode_string(value) if key in ('device_type','status') else value.hex() or '<empty>'}")
        entries = reg_entries(node)
        if entries:
            for addr, size in entries:
                print(f"  reg: base=0x{addr:x} size=0x{size:x} end=0x{addr + size:x}")
        elif "reg" in node["props"]:
            print(f"  reg(raw): {node['props']['reg'].hex()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, struct.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
