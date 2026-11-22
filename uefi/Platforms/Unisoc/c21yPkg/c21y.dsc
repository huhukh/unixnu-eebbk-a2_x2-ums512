##
# Realme C21Y RMX3261 / UMS512 (ums512_1h10) EDK2 platform scaffold.
# Compile/architecture scaffold only; not bootable or flashable.
##
[Defines]
  PLATFORM_NAME                  = realmeC21Y
  PLATFORM_GUID                  = 6C21A326-1D10-4C21-9A51-3261C2100001
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
  # Minimal EDK2 bring-up set. No board display, eMMC, or XNU payload drivers.
  SiliciumPkg/Sec/Sec.inf
  SiliciumPkg/Drivers/RamManagerDxe/RamManagerDxe.inf
  EmbeddedPkg/Drivers/DtPlatformDxe/DtPlatformDxe.inf
  MdeModulePkg/Universal/ResetSystemRuntimeDxe/ResetSystemRuntimeDxe.inf
