/*
 * Realme C21Y RMX3261 initial UEFI memory-map scaffold.
 *
 * IMPORTANT: compile-time scaffold only. The stock DTB exposes one 2-GiB
 * bank at 0x80000000, while Android runtime zoneinfo suggests additional
 * memory above 4 GiB. Until the live cboot handoff FDT and bootloader
 * reservations are measured, this package intentionally does not advertise
 * general-purpose DRAM to DXE. Do not boot/flash this image.
 */
#include <Library/MemoryMapLib.h>

STATIC EFI_MEMORY_REGION_DESCRIPTOR gMemoryDescriptor[] = {
  // Keep only the vendor-confirmed low-memory reservations visible.
  // No guessed UEFI stack, heap, FD, FDT, initrd, or high-RAM ranges.
  {"DDRBIST", 0x80000000, 0x00001000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"RebootEscrow", 0x81FF0000, 0x00010000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"Audio Mem", 0x87500000, 0x00300000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"SIPC", 0x87800000, 0x00800000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"SP DDR", 0x88000000, 0x00300000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"AudioDSP", 0x89000000, 0x00600000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"CP Memory", 0x89600000, 0x04900000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"IQ Memory", 0x90000000, 0x04000000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"SML", 0x94000000, 0x00040000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"TOS", 0x94040000, 0x03FC0000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"Ramoops", 0xFFF80000, 0x00040000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"DebugMem0", 0x100000000, 0x00001000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN},
  {"DebugMem1", 0x844C0000, 0x00004000, AddMem, MEM_RES, UNCACHEABLE, Reserv, UNCACHED_UNBUFFERED_XN}
};

EFI_MEMORY_REGION_DESCRIPTOR *
EFIAPI
GetMemoryRegionDescriptor (
  VOID
  )
{
  return gMemoryDescriptor;
}
