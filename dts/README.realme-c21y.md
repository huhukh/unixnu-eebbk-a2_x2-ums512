# Experimental Realme C21Y RMX3261 DTB skeleton

`realme-c21y-rmx3261.dts` records the S19610AA1 / UMS512 board identity and
publicly documented logo/framebuffer reservations, while including the shared
UMS512 CPU/GIC/timer/UART description. `realme-c21y-rmx3261_defconfig` is a
conservative kernel bring-up configuration without the EEBBK-specific storage
driver.

These files are intentionally separate from `board.toml`, which still selects
the EEBBK `bbk-a2` platform and its `ums512_1h190` UEFI package/memory map.
Consequently this is **not yet a complete C21Y firmware build target** and must
not be flashed. The exact RMX3261 DTB/DTBO, memory map, bootloader handoff and
boot image packaging still need verification and a dedicated C21Y EDK2 platform.
The values are adequate only for host-side DTS syntax/DTB compilation checks.
