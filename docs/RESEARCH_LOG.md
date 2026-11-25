# RESEARCH_LOG — Build #124 `Parse failure` investigation

Evidence IDs are stable. A conclusion may use only IDs listed with it. No guessed addresses, registers, offsets or configs.

---

## R1 — Repository and branch are unchanged from the previous checkpoint

**Command/API**
- `GET /repos/huhukh/unixnu-eebbk-a2_x2-ums512/branches/port/realme-c21y-rmx3261`
- `GET /repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs?branch=port%2Frealme-c21y-rmx3261&per_page=10`

**Observation**
- Branch HEAD is still `8d914b2f3dd35cefd09e123b67ea7a41e51864b4`, tree `c97b752a3018fb15f58c524f3e822f1ae00d43b1`.
- Run #124 is still the newest run for the branch: `45357899006`, `conclusion: failure`, head SHA equal to branch HEAD.
- PR #1 remains open from this branch into `main` (base SHA `7149f64a91cbfc8ef3cbe84c75d42c8f5050f7f2`).

**Conclusion**
- There is no newer commit or newer successful CI run to inherit. Work must continue from this exact SHA.

---

## R2 — Build #124 failure location

**API**
- `GET /actions/runs/45357899006/jobs`

**Observation**
- Job `138320222000`, `Linux - C21Y XNU 8796 build and DTS`, failed after step 17 `Build native XNU kernel`.
- Job `138320222584` (`EDK2 - C21Y firmware-volume compile (scaffold)`) succeeded.
- The failing step invokes:
  `python3 ./unixnu build kernel --skip-prelink -D "$GITHUB_WORKSPACE" --out "$GITHUB_WORKSPACE/$OUTPUT_DIR"`.
- Steps before it, including DTS compilation and `Build Linux XNU toolchain`, succeeded. The toolchain step is the long step (~96 min); the kernel step failed in ~13 s, consistent with an early header-processing failure rather than a compile/link failure.
- The public failing-step log body could not be downloaded without authentication (job HTML requires sign-in; artifacts API returns `401 Requires authentication`). The failure message itself is recorded in the checkpoint history and is reproduced locally below.

**Conclusion**
- The failure is in XNU `installhdrs`, before any ARM64 object compilation or kernel link.

---

## R3 — The observed config values are not causal

**Source read**
- `UniXNU-main/scripts/build-xnu-4k-baseline.sh:147-148`:
  `make -C .cache/xnu-work installhdrs SDKROOT=macosx ARCH_CONFIGS=ARM64 MACHINE_CONFIGS=BCM2837 KERNEL_CONFIGS=DEVELOPMENT ...`
- This command is shared by all Linux baseline builds. It is not emitted by `configs/realme-c21y-rmx3261_defconfig` or by `board.toml`.

**Conclusion**
- `MACHINE_CONFIGS=BCM2837` explains why the string appears, but there is no evidence linking it to header parsing. Do not treat it as the root cause.

---

## R4 — XNU source revision is exactly the pinned revision

**API**
- `GET /repos/apple-oss-distributions/xnu/git/ref/tags/xnu-8796.121.2` → annotated tag object `d2583069f8fa86bf95890afd5ac1c12d2f13dc2e`.
- `GET /repos/apple-oss-distributions/xnu/git/tags/d2583069...` → commit `c54f35ca767986246321eb901baf8f5ff7923f6a`.

**Observation**
- The tag dereferences to the same commit pinned in `os-profiles/ios-16.5-20F66/profile.toml`.
- The locally extracted tree is from that tag; all file/line references below refer to this exact source.

---

## R5 — Exact emitter of `Parse failure`

**Source read**
- `xnu-8796.121.2/makedefs/MakeInc.rule:63-89`, `INSTALLHDRS_RULE_template`:
  - line 78: `$(UNIFDEF) $(4) $< > ...;`
  - line 79: `if [ $$? -eq 2 ]; then`
  - line 80: `$(ERR) Parse failure for $<;`
  - line 81: `exit 1;`
- `libkern/libkern/c++/Makefile:23` lists `OSEndianTypes.h` in `DATAFILES`.

**Conclusion**
- XNU treats **only unifdef exit status 2** as a parse failure. Exit 0/1 are accepted. The message names the input file being processed; it does not imply the header is semantically wrong for the compiler.

---

## R6 — Exact unifdef flags for data headers

**Source read**
- `xnu-8796.121.2/makedefs/MakeInc.def:1047-1070`, especially:
  - `XNU_PRIVATE_UNIFDEF` lines 1048-1054,
  - `DATA_UNIFDEF` line 1070: `$(PLATFORM_UNIFDEF) $(XNU_PRIVATE_UNIFDEF) $(SEED_DEFINES) -UPRIVATE -D_OPEN_SOURCE_ -D__OPEN_SOURCE__`.

**Conclusion**
- Reproduction must use `-U...KERNEL_PRIVATE`, `-UPRIVATE`, `-D_OPEN_SOURCE_`, `-D__OPEN_SOURCE__`, not a kernel-private flag set. This was done in R7 and R10.

---

## R7 — Local reproduction: unifdef 2.10 rejects `OSEndianTypes.h`

**Method**
- Downloaded fanf2/unifdef tag `unifdef-2.10`, built it locally with small host shims for Windows (`err.h`, `version.h`, `tmpfile()` substitution, fake mode constants). No source logic of unifdef was changed.
- Command (equivalent flags):
  `unifdef -DKERNEL '-D_OPEN_SOURCE_=1' '-D__OPEN_SOURCE__=1' -UMACH_KERNEL_PRIVATE -UBSD_KERNEL_PRIVATE -UIOKIT_KERNEL_PRIVATE -ULIBKERN_KERNEL_PRIVATE -ULIBSA_KERNEL_PRIVATE -UPEXPERT_KERNEL_PRIVATE -UXNU_KERNEL_PRIVATE -UKERNEL_PRIVATE -UPRIVATE -UDRIVERKIT OSEndianTypes.h`

**Observation**
- Exit `2`.
- stderr: `OSEndianTypes.h: 184: Premature EOF (#if line 125 depth 1)`.
- The two multiline directives are at lines 180-181 and 183-184:
  `#endif /* __cplusplus` + continuation `*/`, and `#endif /* ! _OS_OSENDIANHELPER_H` + continuation `*/`.
- fanf2/unifdef 2.10 source comment at `unifdef.c:522-529` explicitly calls these "dodgy directives" (multi-line comments hanging off a directive) and says they cannot always be handled when state changes.

**Conclusion**
- The reported Build #124 failure is reproducible from first principles with the documented tool version and the exact pinned header.

---

## R8 — The runner tool version is 2.10, and 2.10 is known-bad upstream

**Sources**
- `.github/workflows/build.yml:22` → `runs-on: ubuntu-22.04`.
- `UniXNU-main/scripts/linux/setup-toolchain.py:36` → apt `unifdef` is installed as a dependency; no newer version is built by that script.
- Ubuntu packages page for jammy: `unifdef (2.10-1.1build0.2 and others)`, amd64 `2.10-1.1build0.2`.
- UniXNU `docs/devices/enuma.md:532`: "A WSL-only toolchain change was required: unifdef 2.10 (system) -> 2.12 (~/.local/bin) because v2.10 fails parsing bsd/net/pfvar.h during installhdrs; the base repo itself was not modified for this."
- UniXNU `docs/devices/nuwa.md:662`: kernel patch set includes `8796-unifdef-headers (two headers the host unifdef 2.10 rejects)`.

**Conclusion**
- This is a known host-tool/source compatibility issue on Linux, not a C21Y hardware, DTS, defconfig or EDK2 issue.

---

## R9 — Exact upstream fix patch and blob-hash proof

**Source**
- `https://raw.githubusercontent.com/wh1stl3/UniXNU-nuwa/master/patches/xnu/8796-unifdef-headers.patch` (retrieved and read).
- It changes exactly two files:
  - `bsd/net/pfvar.h:148`: bare `#error` → `#error "PF_MD5_DIGEST_LENGTH must match MD5_DIGEST_LENGTH"`.
  - `libkern/libkern/c++/OSEndianTypes.h:180-184`: two multi-line `#endif /* ...` comments → one-line forms.

**Local hash check**
- Git blob SHA-1 of pinned `bsd/net/pfvar.h` pre-image: `09b3ac0ab002f53508a706781e751079a76ba040` (matches patch `index 09b3ac0`).
- Git blob SHA-1 of pinned `libkern/libkern/c++/OSEndianTypes.h` pre-image: `487eb3ec7cc340ac978e45700bdf6a37db003fba` (matches patch `index 487eb3e`).
- Reproducing the patch text locally gave post-images `c624f0de8556419712ae810bed3ab0c366a69352` and `fdd4ff9913799142bc1cf9e148217bd643055dc6`, matching the Nuwa patch `index c624f0d` and `index fdd4ff9`.
- Therefore the patch is byte-for-byte applicable to the C21Y-pinned XNU source. It was copied into `patches/xnu/8796-unifdef-headers.patch` with full 40-hex blob IDs.

---

## R10 — Local verification of the fix under unifdef 2.10 and 2.12

**Commands/results**
- unifdef 2.10 on unpatched `OSEndianTypes.h` → exit `2`, `Premature EOF (#if line 125 depth 1)`.
- unifdef 2.10 on patched `OSEndianTypes.h` → exit `0`, no stderr.
- unifdef 2.10 on unpatched `pfvar.h` → exit `2`, `Premature EOF (#if line 63 depth 1)`.
- unifdef 2.10 on patched `pfvar.h` → exit `1` (normal success code meaning output differs), no stderr.
- unifdef 2.12 on unpatched `OSEndianTypes.h` → exit `0`.

**Conclusion**
- Either upgrading the tool to 2.12 or applying this two-header patch resolves the parser class. The patch is chosen because it is minimal, uses the existing patch pipeline, needs no new toolchain fetch, and is already proven in another device port.

---

## R11 — Mechanism detail from unifdef 2.10 debug trace

**Command**
- `unifdef -d -DKERNEL '-D_OPEN_SOURCE_=1' '-D__OPEN_SOURCE__=1' -UKERNEL_PRIVATE -UPRIVATE -UDRIVERKIT pfvar.h`

**Observation**
- Unpatched:
  - line 148 → `PLAIN`, parser state `DIRTY`
  - line 149 (`#endif /* PF_MD5_DIGEST_LENGTH != ... */`) → `PLAIN`, not `ENDIF`
  - line 150 → `ENDIF`, leaving one level too many open
- Patched:
  - line 148 → `PLAIN`, parser state `START`
  - line 149 → `ENDIF`
  - line 150 → `ENDIF`

**Conclusion**
- The bare `#error` with no message is the trigger for the `pfvar.h` half of the failure. Adding a message makes the following `#endif` recognizable. This explains why a one-line textual change fixes a parse failure.

---

## R12 — Decision record

**Decision**
- Apply `8796-unifdef-headers.patch` from the C21Y device patch series, before `sdhci-block-personality.patch`.
- Do not change `MACHINE_CONFIGS`, `ARCH_CONFIGS`, defconfig, memory map, ADT or EDK2 files for this failure.
- Do not replace the XNU patch with a toolchain-only fix, because that would add a new fetched/compiled dependency to CI for the same proven result. The upgrade path remains documented as an alternative.

**Verification gate still open**
- The patch has been verified locally, but no GitHub Actions run has compiled the kernel after applying it. Compile success requires a new run whose job `Linux - C21Y XNU 8796 build and DTS` concludes `success` and whose artifact contains a non-empty `kernel.macho`.

---

## R13 — Build #126 link failure: undefined `arm64_platform_sleep_hook`

**API / log**
- Run `45385291507` (Build #126), head `100a64ccee1d153b2baa7432a47a2b5877f09ed6`.
- Job `138414510202` (`Linux - C21Y XNU 8796 build and DTS`): steps 1–16 `success`, step 17 `Build native XNU kernel` `failure`, step 18 `Upload build-check artifacts` `success`.
- Step 17 log:
  - `Undefined symbols for architecture arm64:`
  - `"_arm64_platform_sleep_hook", referenced from:`
  - `    __ZN6ArmCpu5startEP9IOService in libArmCpu.a(ArmCpu.o)`
  - `ld: symbol(s) not found for architecture arm64`
- No `Parse failure` appears anywhere in the log: the unifdef fix (R9–R12) worked.
- Artifact `realme-c21y-build-check` exists (`14922332850`, 71,555,458 bytes, `sha256:f9380b35bf0b303f80009cd3076998060f611db981bde788b1efe42d871166bc`), but step 17 aborted the build command before the `find ... kernel.macho` gate, so no `kernel.macho` was produced.

**Source read**
- `UniXNU/ArmCpu` revision `5f3702697ed80fd2e98594de1af7e32b4b77b08b`, `ArmCpu.cpp:65`:
  `extern "C" void (*arm64_platform_sleep_hook) (boolean_t boot_cpu) __attribute__((weak_import));`
- `ArmCpu.cpp:600-603` assigns the hook only when boot-arg `platform-sleep=1`.
- Pinned XNU `osfmk/arm64/cpu.c` (blob `94e91306b14364f720ea80e46d853035aabd78e6`) declares `arm64_prepare_for_sleep()` but never defines `arm64_platform_sleep_hook`.
- UniXNU's own device records state the link rule: "A static kernel link refuses to leave any weak_import undefined."
- The newer-XNU reference patch (`UniXNU-sheng/patches/xnu-12377/sheng-platform-sleep.patch`) defines the hook in `osfmk/arm64/cpu.c` and calls it from `ml_arm_sleep`, but it also calls `arm_init_cpu()`, which does not exist in xnu-8796.

**Conclusion**
- Root cause: the board XNU patch that defines the hook is missing from the C21Y series. `weak_import` only defers resolution on Darwin dynamic linking; the kernel link is static.
- Fix: `patches/xnu/8796-arm64-platform-sleep-hook.patch` defines `void (*arm64_platform_sleep_hook)(boolean_t) = NULL;` in `osfmk/arm64/cpu.c`. The pre-image blob hash `94e91306…` matches GitHub's tree entry for the pinned commit, and the hunk reproduces post-image `9a43e588…`.
- No call site is added on 8796: `arm_init_cpu()` does not exist there, and the kernel args do not set `platform-sleep=1`, so sleep behaviour is unchanged. Wiring the sleep path is a separate change that needs a verified 8796 wake path.
- This is a compile/link fix only. It does not claim boot success or sleep support.

---

## R14 — Second live-FDT probe: UART register/IRQ/clock graph, GICv3 detail, timer PPIs, CPU `reg` encoding, PSCI conduit

**Commands (read-only, `su -c` over ADB, no device writes)**
- `od -An -tx1 /proc/device-tree/soc/ap-apb/serial@70000000/*`
- `od -An -tx1 /proc/device-tree/soc/ap-apb/serial@70100000/*`
- `od -An -tx1 {/proc/device-tree/soc/apapb-gate,/soc/clock-controller@20200000,/soc/clock-controller@32080000,...}/phandle|reg|compatible`
- `od -An -tx1 /proc/device-tree/ext-26m/clock-frequency` and the other root fixed clocks
- `od -An -tx1 /proc/device-tree/interrupt-controller@12000000/{reg,redistributor-stride,#redistributor-regions,interrupts}`
- `od -An -tx1 /proc/device-tree/timer/{compatible,interrupts}` (and absence of `clock-frequency`)
- `od -An -tx1 /proc/device-tree/cpus/cpu@*/{reg,compatible,enable-method,capacity-dmips-mhz,phandle}`, `/cpus/#address-cells`
- `ls /proc/device-tree/cpus/cpu-map/*`, `ls /proc/device-tree/psci`, `od -An -tx1 /proc/device-tree/psci/method`
- `cat /proc/cmdline`, `cat /proc/device-tree/chosen/bootargs_ext`, `ls -l /proc/device-tree/chosen/`

**Observations**
- Both UART nodes are `sprd,ums518-uart` + `sprd,sc9836-uart`, `reg` size `0x100`; `serial@70000000` = SPI 2, `serial@70100000` = SPI 3, both level-high (`<0 n 4>`). Neither node has `clock-frequency`.
- UART clock cells resolve to `apapb-gate` (`0x1c`), `sprd,sharkl5pro-ap-clk` at `0x20200000` (`0x1d`), and `sprd,sharkl5pro-aonapb-clk` at `0x32080000` (`0x1e`), each with `#clock-cells = 1`; gate and clk-controller windows are `0x1000`.
- Root fixed clocks: `ext-26m` = `0x018CBA80` = 26 000 000 Hz; `ext-32k` = 0x8000; `rco-100m` = 0x05F5E100 = 100 000 000 Hz. Factor clocks: `clk-13m` = `clk-*` mult 1 div 2 (of `0x1e`), `clk-4m3` = mult 1 div 6.
- GICv3 node is root-level `/interrupt-controller@12000000`, phandle `0x01`, `reg` = `0x12000000`+`0x20000` and `0x12040000`+`0x100000`, `redistributor-stride` = `0x20000`, `#redistributor-regions` = 1, maintenance `interrupts` = `<1 9 4>`, `#interrupt-cells = 3`. Eight `0x20000` frames fit the 1 MiB GICR window.
- Timer `/timer`: `arm,armv8-timer`, PPIs `<1 13 4> <1 14 4> <1 11 4> <1 10 4>`, `arm,no-tick-in-suspend`, and **no** `clock-frequency` property.
- `/cpus` `#address-cells = 2`, `#size-cells = 0`. `reg` values: `0x0`, `0x100`, `0x200`, `0x300`, `0x400`, `0x500` (A55, `capacity-dmips-mhz` 544), `0x600`, `0x700` (A75, 1024). `enable-method = psci` on all.
- `cpu-map` names cluster0 = 6 cores and cluster1 = 2 cores, which is the ODM's grouping, not an MPIDR cluster encoding; `reg` remains authoritative.
- `/psci`: `compatible = "arm,psci-0.2"`, `method = "smc"`, nothing else. `/idle-states` `entry-method = "arm,psci"`.
- `/chosen` has `bootargs`, `bootargs_ext`, `linux,initrd-start/end`, `stdout-path`; **no** `kaslr-seed`, **no** `rng-seed`, **no** `linux,usable-memory-range`. `stdout-path` = `/soc/ap-apb/serial@70100000`.
- `/soc` and `/soc/ap-apb` are `simple-bus` with `#address-cells = 2`, `#size-cells = 2`; `ranges` present (empty listing from the procfs dump but the node exists).
- Identity nodes: `cpuinfo_hardware` = `T610-Unisoc`, `sprd,sc-id` = `ums512 1000 1000`.

**Conclusion**
- The UART needs a three-clock chain (gate, AP clock, AONPWB source clock) before its registers are usable; a driver that only writes the data register will most likely transmit nothing.
- Baud divider input is **not** in the DT. It must be derived from the 26 MHz reference through the `ap-clk`/`aonapb-clk` register windows, and that derivation is not proven yet. Do not hardcode a divisor.
- GICv3 CPU interface is system-register only (no GICC MMIO), 8 redistributors, SPI 2/3 for the UARTs at level-high, timer PPI 14 (INTID 30) for EL1.
- CPU enumeration must use `Aff1 = 0..7`, not `Aff0` and not a flat 0..7 index, and must be based on `reg`, not `cpu-map` names.
- PSCI is SMC32 0.2 only; any HVC path is wrong for this device.
- No KASLR seed and no `usable-memory-range` means the kernel gets the whole `/memory` range; reservations come from `/reserved-memory` and the bootloader's own claims.

**Claim boundary**
- These are hardware observations from the live FDT, not driver support. No XNU code reads this yet, and no baud value, MMIO address or interrupt route has been exercised from XNU.

---

## R15 — Build #128 failure: corrupt patch due to missing trailing newline

**API / log**
- Run #128 (`45413693437`), commit `5c39de471823b72081f5afc6e1490ca3ccf199ff`.
- Job `Linux - C21Y XNU 8796 build and DTS`: failed in step 17 (`Build native XNU kernel`) instantly (1s).
- Log tail:
  `unixnu: git failed (128): error: corrupt patch at .../patches/xnu/8796-arm64-platform-sleep-hook.patch:18`

**Root cause**
- The patch file lacked a trailing newline (ended at byte 0x41 'A' of the last line without LF).
- `git apply` requires every patch file to end with a newline; otherwise it considers the last line incomplete and treats the patch as corrupt.

**Fix**
- Added a trailing LF to `patches/xnu/8796-arm64-platform-sleep-hook.patch` (now 749 bytes, ends with `0x0a`).
- Committed as `c7c6de6` ("xnu: fix missing trailing newline in platform-sleep hook patch"). Triggered Build #129 (`45413693437` / `#129`).

---

## R16 — Build #129 failure: missing `[kernel.prelink]` in `board.toml`

**API / log**
- Run #129 (`45426457426`), commit `c7c6de6`.
- Job `Linux - C21Y XNU 8796 build and DTS`: failed in step 17 during `build-xnu-4k-baseline.sh`.
- Error log:
  `unixnu: board.toml has no [kernel.prelink]`

**Root cause**
- The build harness requires a `[kernel.prelink]` section in `board.toml` to configure prelinking components (`DarwinBoot`, `XnuPrelink`) before generating the final kernel artifact. The C21Y board config lacked this section.

**Fix**
- Added `[kernel.prelink]` with `enabled = true` and `components = ["DarwinBoot", "XnuPrelink"]` to `board.toml`.
- Committed and pushed to `port/realme-c21y-rmx3261` (Build #130).

## R17 — Build #136 failure: `apple-only-cpu-tunables.patch` does not apply

**API / log (job `138869627199`, run `45490266645`)**
```
+ git apply ... apple-only-cpu-tunables.patch
error: patch failed: osfmk/arm64/start.s:33
error: osfmk/arm64/start.s: patch does not apply
```
Step 16 `Build Linux XNU toolchain` passed (1h 15m 33s); failure is step 17, first patch in the OS series.

**Root cause**
- The patch was authored against a different `osfmk/arm64/start.s`. Verified by fetching the CI-pinned tree (`apple-oss-distributions/xnu` commit `c54f35ca767986246321eb901baf8f5ff7923f6a`, tag `xnu-8796.121.2`) and diffing hunk context:
  - hunk 1 declared `@@ -33,7 +33,9 @@` but the shipped file has this block at lines 33-39; the two added lines do not change the count, so `oldCount` must stay 7 and the header start must be 33 — that part is fine, but the *preceding* commit had `@@ -17,...` which was wrong.
  - hunk 2 declared `@@ -783,10 +785,13 @@` and ended with context `#if HAS_CLUSTER && !NO_CPU_OVRD`. The shipped file has `#if HAS_CLUSTER` at line 783 and `#endif // APPLE_ARM64_ARCH_FAMILY` at 775 with the MIDR/tunables block at 777-780. The patched-in guard therefore needs the hunk to start at 775, not 783.
- Independent cross-check: the upstream UniXNU copy `zus12873/UniXNU:patches/xnu/apple-only-cpu-tunables.patch` has the same two defects (`@@ -783` and `#if HAS_CLUSTER && !NO_CPU_OVRD`), so this is **not** a transcription error here — the upstream patch targets a tree whose `start.s` differs from the OSS `xnu-8796.121.2` release.

**Additional finding — `tunables.s` is absent from the OSS release**
- `osfmk/arm64/tunables/tunables.s` and an `APPLY_TUNABLES` macro do **not** exist anywhere in `xnu-8796.121.2` (tree of 5328 paths checked) nor in `xnu-10063.141.1` (5529 paths). `osfmk/arm64/start.s` nevertheless `#include`s it at line 36 and calls `APPLY_TUNABLES` at line 780.
- `APPLE_ARM64_ARCH_FAMILY` is not defined by `config/MASTER.arm64.bcm2837`, `config/MASTER`, `osfmk/conf/files.arm64`, `osfmk/arm64/asm.h`, or `osfmk/arm64/proc_reg.h` for a non-Apple board. So on this port the guard evaluates false and both the `#include` and the `APPLY_TUNABLES` expansion are removed — which is exactly why the guard is required: without it the assemble step would fail on a missing file.
- Consequence: this patch is **mandatory** for every non-Apple arm64 build of xnu-8796, not an optional Apple-tuning removal.

**Fix**
- Rewrote `os-profiles/ios-16.5-20F66/patches/xnu-8796/apple-only-cpu-tunables.patch` with hunks recomputed against `c54f35ca7679`:
  - hunk 1 `@@ -33,7 +33,9 @@` with context `mach_assert.h` / `machine/asm.h` / `"assym.s"` / `tunables.s` / `exception_asm.h` / blank / `#if __ARM_KERNEL_PROTECT__`.
  - hunk 2 `@@ -775,9 +777,11 @@` with context `#endif  // APPLE_ARM64_ARCH_FAMILY`, blank, the tab-indented MIDR block, blank, `APPLY_TUNABLES`, blank, blank, `#if HAS_CLUSTER`.
  - Dropped the bogus `index a261552b8cdd..f435c87d6ac7` line; git does not need it for `git apply`.
- Verification performed offline before commit: both hunks were replayed against the fetched file and every context byte matched; the file is LF-only, 572 bytes, ends with a newline, and keeps the single leading space on tab-indented context lines.
- All 60 hunks of all 12 patches in the OS series were replayed against the pinned tree. The only genuine mismatch was this patch (the other four reported offsets — `clang-uio-stackbuf` `sys_generic.c`/`vfs_lookup.c`, `native-aes-personality`, `zzx-pmap-sync-64bit-pa` — apply with a line offset because earlier patches in the same series shift text, which `git apply` tolerates).
