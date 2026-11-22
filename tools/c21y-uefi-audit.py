#!/usr/bin/env python3
"""Static safety audit for the Realme C21Y EDK2 scaffold (not an EDK2 build)."""
from pathlib import Path
import re
import tomllib

root = Path(__file__).resolve().parents[1]
dsc = root / "uefi/Platforms/Unisoc/c21yPkg/c21y.dsc"
fdf = root / "uefi/Platforms/Unisoc/c21yPkg/c21y.fdf"
inf = root / "uefi/Platforms/Unisoc/c21yPkg/Library/MemoryMapLib/MemoryMapLib.inf"
cfile = root / "uefi/Platforms/Unisoc/c21yPkg/Library/MemoryMapLib/MemoryMapLib.c"
cfg = root / "uefi/Resources/Configs/realme-c21y.toml"
build_script = root / "uefi/build-c21y.sh"
for p in (dsc, fdf, inf, cfile, cfg, build_script):
    assert p.is_file(), f"missing {p.relative_to(root)}"

dsc_text = dsc.read_text()
assert "PLATFORM_NAME                  = realmeC21Y" in dsc_text
assert "c21yPkg/Library/MemoryMapLib/MemoryMapLib.inf" in dsc_text
assert "bbkA2Pkg" not in dsc_text and "BbkA2" not in dsc_text
for match in re.findall(r"(?m)^\s*(?:PLATFORM_GUID|FILE_GUID)\s*=\s*([0-9A-Fa-f-]+)", dsc_text + inf.read_text()):
    assert re.fullmatch(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", match), match

cfg_data = tomllib.loads(cfg.read_text())
assert cfg_data["boot_image"]["header_version"] == 2
assert cfg_data["boot_image"]["pagesize"] == 2048
assert cfg_data["boot_image_kernel"]["kernel_compression"] == "none"

mem = cfile.read_text()
assert "GetMemoryMap (" in mem
assert "0x81FF0000" in mem and "0xFFF80000" in mem
assert "High RAM" not in mem and "DXE Heap" not in mem
assert "not bootable" in (root / "uefi/C21Y-UEFI-STATUS.md").read_text().lower()
assert "C21Y_FD_BASE" in build_script.read_text()
assert "DO NOT package or flash" in build_script.read_text()
assert "!include SiliciumPkg/Common.fdf.inc" in fdf.read_text()

print("C21Y UEFI scaffold static audit: PASS")
print("NOTE: this does not compile EDK2 and does not validate hardware boot safety.")
