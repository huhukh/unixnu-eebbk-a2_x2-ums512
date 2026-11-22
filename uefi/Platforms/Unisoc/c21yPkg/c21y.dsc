##
# Realme C21Y RMX3261 / UMS512 (ums512_1h10) EDK2 platform scaffold.
# This is intentionally a compile/architecture scaffold, NOT bootable yet.
# No BBK A2 board drivers, display, eMMC, reset hooks, or guessed memory map.
##
[Defines]
  PLATFORM_NAME                  = realmeC21Y
  PLATFORM_GUID                  = 6C21A326-1D10-4C21-9A51-3261C21Y0001
  PLATFORM_VERSION               = 0.1
  DSC_SPECIFICATION              = 0x00010005
  OUTPUT_DIRECTORY               = Build/c21yPkg
  SUPPORTED_ARCHITECTURES        = AARCH64
  BUILD_TARGETS                  = DEBUG|RELEASE
  SKUID_IDENTIFIER               = DEFAULT
  FLASH_DEFINITION               = c21yPkg/c21y.fdf

!include UMS512Pkg/UMS512Pkg.dsc.inc

[PcdsFixedAtBuild]
  gArmTokenSpaceGuid.PcdSystemMemoryBase|0x80000000
  # Conservative initial values only; must be reconciled with live cboot handoff.
  gArmPlatformTokenSpaceGuid.PcdCPUCoresStackBase|0x80480000
  gArmPlatformTokenSpaceGuid.PcdCPUCorePrimaryStackSize|0x00040000
  gEfiMdePkgTokenSpaceGuid.PcdDebugPrintErrorLevel|0x8000004F
  gEfiMdePkgTokenSpaceGuid.PcdDebugPropertyMask|0x02
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemManufacturer|"realme"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemModel|"C21Y RMX3261"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailModel|"RMX3261"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailSku|"ums512_1h10"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemBoardModel|"S19610AA1"

[LibraryClasses]
  MemoryMapLib|c21yPkg/Library/MemoryMapLib/MemoryMapLib.inf

[Components]
  MdeModulePkg/Universal/ResetSystemRuntimeDxe/ResetSystemRuntimeDxe.inf
