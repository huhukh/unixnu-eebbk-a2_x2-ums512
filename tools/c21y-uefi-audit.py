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
assert "*MemoryDescriptor = NULL;" in mem
assert "*MemoryDescriptorCount = 0;" in mem
# These are EEBBK A2 carve-out addresses, not established C21Y UEFI reservations.
for borrowed in ("0x87500000", "0x87800000", "0x89000000", "0x89600000", "0x90000000", "0x94000000", "0x94040000", "0xFFF80000"):
    assert borrowed not in mem, f"unverified/inherited memory range: {borrowed}"
assert "not bootable" in (root / "uefi/C21Y-UEFI-STATUS.md").read_text().lower()
assert "C21Y_FD_BASE" in build_script.read_text()
assert "DO NOT package or flash" in build_script.read_text()
assert "!include SiliciumPkg/Common.fdf.inc" in fdf.read_text()

print("C21Y UEFI scaffold static safety audit: PASS")
print("MemoryMapLib is intentionally empty; no RAM is advertised to UEFI.")
print("NOTE: this does not compile EDK2 and does not validate hardware boot safety.")
