/*
 * Realme C21Y RMX3261 initial UEFI memory-map scaffold.
 * Compile-time only: no usable DRAM is advertised until cboot's live FDT,
 * load address and reserved regions are verified. Do not boot or flash.
 */
#include <Library/MemoryMapLib.h>

STATIC EFI_MEMORY_REGION_DESCRIPTOR gMemoryDescriptor[] = {
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

VOID
GetMemoryMap (
  OUT EFI_MEMORY_REGION_DESCRIPTOR **MemoryDescriptor,
  OUT UINT8                         *MemoryDescriptorCount
  )
{
  *MemoryDescriptor = gMemoryDescriptor;
  *MemoryDescriptorCount = ARRAY_SIZE (gMemoryDescriptor);
}
