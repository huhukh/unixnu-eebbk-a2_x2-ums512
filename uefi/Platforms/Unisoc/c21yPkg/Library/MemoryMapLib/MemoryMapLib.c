/*
 * Realme C21Y RMX3261 initial UEFI memory-map scaffold.
 *
 * FAIL CLOSED: no C21Y-safe UEFI memory map has been established.
 *
 * The previous table copied several EEBBK A2 / ums512_1h190 carve-out
 * addresses into this C21Y / ums512_1h10 package. Those addresses are not
 * evidence for this board and must not be advertised to the UEFI allocator.
 *
 * Return an empty map until the exact C21Y live FDT, bootloader-owned ranges,
 * firmware relocation window, and usable DRAM banks have been reconciled.
 * This deliberately prevents a usable/bootable firmware build.
 */
#include <Library/MemoryMapLib.h>

VOID
GetMemoryMap (
  OUT EFI_MEMORY_REGION_DESCRIPTOR **MemoryDescriptor,
  OUT UINT8                         *MemoryDescriptorCount
  )
{
  *MemoryDescriptor = NULL;
  *MemoryDescriptorCount = 0;
}
