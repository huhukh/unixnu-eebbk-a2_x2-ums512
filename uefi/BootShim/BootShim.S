//
//  BootShim for BBK/EEBBK A2 / X2 / X2P (Unisoc UMS512, ums512_1h190, SharkL5Pro).
//
//  Chain:  BootROM -> splloader -> cboot (U-Boot 2015.07) -> boot.img kernel field
//          -> this shim at 0x80080000 -> SILICIUM_UEFI.fd at FD_BASE -> SEC.
//
//  Contract with cboot (same handoff Project-Silicium relies on for Qualcomm ABL):
//
//    * cboot loads the boot.img "kernel" field to a fixed DRAM address.  The
//      Unisoc cboot address is 0x80080000; the stock boot.bin header says
//      kernel_addr = 0x8000 (offset from base 0), and the Bootshim-sprd
//      reference documents 0x80080000 for Unisoc cboot.  TO VERIFY ON HARDWARE.
//    * x0 = physical address of the merged (boot dtb + dtbo) device tree.
//      cboot hands over the FDT at 0x82000000 on this SoC family (measured in
//      the cboot image for ums512_1h190: start_linux is entered with
//      x0 = 0x82000000).  This shim does not touch x0: it is saved in x19 and
//      restored right before the jump, so Silicium SEC records it in the
//      gSiliciumEntryArgHobGuid HOB and DtPlatformDxe / the payload driver
//      can read /chosen from it.
//    * MMU and caches: cboot is expected to hand over with them off.  We still
//      run cache maintenance (harmless when off) because LK on the UMS9621
//      reference handed over with caches ON and that cost the E5 port a day.
//
//  The shim relocates the firmware volume:
//
//    0x80080000  _Head / _Start / this code
//    0x8008xxxx  _Payload = SILICIUM_UEFI.fd appended by the boot-image packer
//         |
//         +-- copy FD_SIZE bytes to FD_BASE (0x80800000), then br there
//
//  FD_BASE = 0x80800000 keeps the destination outside the source window
//  (0x80080000 + 4 MiB = 0x80480000) because the copy below is a forward
//  16-byte ldp/stp loop and would otherwise overwrite source bytes it has not
//  read yet.  Same reasoning as the E5 port (_repos/e5-xnu/docs/uefi-bringup.md).
//
//  The first 64 bytes double as a valid AArch64 Image header:
