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

## R18 — Build #138: the *other* `apple-only-cpu-tunables.patch` was applied first

**Evidence (run `45525087213`, head `0c12f50d`)**
- Step 16 `Build Linux XNU toolchain` succeeded after 105 min. Step 17 failed in 2 s with the same message as #136:
  `error: patch failed: osfmk/arm64/start.s:33` / `patch does not apply`.
- The run summary's `status.json` prints the **resolved** configuration. It shows:
  `board.kernel.patch_series = ["arch:patches/xnu/series", "soc:patches/xnu/series", "os:patches/xnu/series", "device:patches/xnu/series"]`,
  while `board.kernel.prelink.patch_series` holds the three-entry board list.

**Root cause**
- At commit `0c12f50d`, `board.toml` declared `[kernel.prelink]` **before** its `config_fragments` / `patch_series` / `archives` arrays. In TOML every key after a table header belongs to that table, so those arrays landed in `[kernel.prelink]` and the real `[kernel]` kept only `defconfig`.
- `profiles.merge()` replaces lists, but the board never supplied a `[kernel].patch_series`. The arch profile's list therefore survived and its first patch is UniXNU's xnu-10063-era `patches/xnu/apple-only-cpu-tunables.patch`. That patch's hunk 1 expects `#include <pexpert/arm64/board_config.h>` at line 33; the pinned xnu-8796 file has it at 32 and has `#include "assym.s"` at 35. Hence the failure at old line 33 — **not** the OS-series patch fixed in R17.
- Proof: replaying the committed OS patch (`sha=f94c73d2`, 572 bytes) against `c54f35ca7679` succeeds with zero mismatches; replaying the arch patch's hunk 1 against the same file fails at exactly line 33.

**Fix**
- Commit `3614a701` moved `[kernel.prelink]` to the end of `board.toml`, so the three arrays now belong to `[kernel]` again. Current resolved `patch_series` is `soc → os → device`, with no `arch` entry (verified against the branch's `board.toml` and all three series files).
- Consequence: builds #138/#139/#140 could never pass step 17 — they all started from commits with the broken board.toml. A fresh run at a post-`3614a701` head is required. The same TOML bug also meant the first build used only `arch:configs/common.config`; the corrected board now adds `soc:configs/ums512.config` and `os:configs/ios.config`.

## R19 — Build #141: UTF-8 BOM in `board.toml`

**Log (run `45541568640`, head `040b6898`, step 11 `Resolve C21Y defconfig`)**

```
unixnu: .../board.toml: Invalid statement (at line 1, column 1)
```

**Root cause**
- The browser upload that committed `3614a701` wrote a UTF-8 BOM (`EF BB BF`) followed by `0A` at byte 0 of `board.toml`. Python `tomllib` treats the BOM as the first character of an unterminated statement, hence "line 1, column 1".
- Other TOML files on the same branch (`feeds.toml`, `porting.toml`, the OS profile and SoC TOMLs) have no BOM; only `board.toml` was affected.

**Fix**
- Stripped the three BOM bytes locally and re-uploaded `board.toml` as `4b3a42e3`. Raw bytes at that commit start `0A 73 63 68 65 6D 61` (newline then `schema`), with no `EF BB BF`. Build #142 (`45542624841`) was triggered automatically.
- Prevention: after any browser upload of a `.toml` file, check the first three bytes via `raw.githubusercontent.com` before relying on CI.

## R20 — Build #142: duplicate `reserved10` in xnu-8796 `pmap.h` on a non-PAC board

**Evidence (run `45542624841`, head `4b3a42e3`)**
- Steps 1–16 all succeeded; step 17 ran 3m 16s, so patch application and headers completed and the build reached real compilation.
- Full `kernel-bootstrap.log` retrieved from the build-check artifact (39,296,602 byte zip via `nightly.link`; log 362,974,757 bytes). First compiler error:
  ```
  .../tree/.cache/xnu-work/osfmk/arm/pmap/pmap.h:445:7: error: duplicate member 'reserved10'
    445 |         bool reserved10;
        |              ^
  .../pmap.h:422:7: note: previous declaration is here
    422 |         bool reserved10;
        |              ^
  ```
- It occurs while compiling `genassym.o` (`osfmk/arm64/genassym.c` → `osfmk/arm/pmap.h:43`). The later `make[1]: *** .../MakeInc.top:524: build_all_bootstrap_DEVELOPMENT^ARM64^BCM2837` is only the propagation of this compile failure.
- No earlier `error:` in 363 MB of log. All other matches are warnings or source text containing the word "error".

**Root cause**
- The pinned source `xnu-8796.121.2` (`c54f35ca7679`) has two padding fields named `reserved10` in mutually exclusive `#if` branches of `struct pmap`:
  - line 418–423: `#if defined(CONFIG_ROSETTA) … #else bool reserved10; #endif`
  - line 442–446: `#if HAS_APPLE_PAC … #else bool reserved10; #endif`
- Apple builds define `HAS_APPLE_PAC`, so the second `reserved10` is compiled out. Live C21Y `/proc/config.gz` has no `PTR_AUTH` (recorded in `HARDWARE_EVIDENCE.md`), and the board config does not define `CONFIG_ROSETTA`. With both macros absent, both `#else` branches are compiled and clang rejects the duplicate member.
- This is independent of the new config fragments: the fields are in the pristine pinned source; earlier runs never reached this compiler pass.

**Fix**
- `patches/xnu/8796-pmap-no-pac-reserved10.patch` renames only the PAC-slot padding field to `reserved10_pac` (old line 445, new line 445). Grep of the pinned tree shows no source reference to `pmap.reserved10`, so the rename is ABI-neutral padding only.
- Do **not** define `HAS_APPLE_PAC` or `CONFIG_ROSETTA` to hide this: C21Y hardware has no pointer authentication and no Rosetta, so either would be a false hardware claim.
- Offline validation: hunk `@@ -442,7 +442,7 @@` replayed against the pinned file with all seven old context lines matching byte-for-byte; seven new lines; patch is 213 bytes, LF-only, ends with `0x0a`.
- Added to `patches/xnu/series` after the sleep-hook patch. A new CI run is required; no compile or boot claim is made until it produces a non-empty `kernel.macho`.

## R21 — Build #143: missing non-Apple PPL/IOMMU guards in xnu-8796 `pmap.c`

**Evidence (run `45565371465`, head `5d6b6e3`)**
- Steps 1–16 all succeeded; step 17 failed after 2m 05s. Artifact `realme-c21y-build-check` id `15002168770`, 44,770,923 bytes, digest `sha256:5f3f171493d70f25946fd8f6f9a1f8d125a8eb0e5041f30deae2d9053e3b3016`, downloaded via `nightly.link`; local SHA-256 matched. `kernel-bootstrap.log` is 558,857,629 bytes.
- First compiler error (log line 2,787,305): `fatal error: 'arm64/ppl/sart.h' file not found`, from `osfmk/arm/pmap/pmap.c:87`. No earlier compiler error in the log; only the same harmless `sysctl`/`sw_vers` lines seen before.
- Pinned source `c54f35ca7679`: `pmap.c:87` includes `arm64/ppl/sart.h`, line 88 includes `arm64/ppl/uat.h`, and `pmap_bootstrap()` calls `uat_bootstrap()` (line 2186) and `sart_bootstrap()` (line 2192). Neither header exists anywhere in that tree (grep: one match, the include itself).
- `pexpert/arm64/board_config.h` defines `XNU_MONITOR` only for T6000/T8101/T8103. The BCM2837 config used by this port (lines 90–98) defines no `XNU_MONITOR`, `XNU_MONITOR_ANS2_SART` or `XNU_MONITOR_UAT_PPL`. So the Apple PPL/IOMMU paths are absent hardware, not missing files to invent.
- UniXNU's arch arm64 series contains `non-apple-iommu-bootstrap.patch`, which adds exactly these four guards. The C21Y OS series for xnu-8796 did not port it (R18 correctly removed the arch series because it targets xnu-10063), so the unguarded 8796 source reached the compiler.

**Fix**
- New `os-profiles/ios-16.5-20F66/patches/xnu-8796/8796-non-apple-iommu-bootstrap.patch`: guards the `sart.h`/`uat.h` includes and the two bootstrap calls with `XNU_MONITOR_ANS2_SART` / `XNU_MONITOR_UAT_PPL`. No stub headers, no macro forced to 1, no invented register or address.
- Offline validation: both hunks replayed byte-for-byte against the pinned `pmap.c` (`@@ -84,8 +84,12 @@` and `@@ -2183,16 +2187,20 @@`); patch 982 bytes, LF-only, ends `0x0a`. Added after `apple-only-cpu-tunables.patch` in the OS series, before the later `pmap.c` hunk in `zzx-pmap-sync-64bit-pa.patch`.
- No compile or boot claim until a new CI run produces a non-empty `kernel.macho`.

## R22 — macOS payload run #1: OS profile never installed into the upstream UniXNU checkout

**Evidence (run `45573253682`, head `9ba7279a`, job `139064823493`)**
- Job failed in 1m 22s at step 9 `defconfig + status`; steps 10–13 (kernel, bindings, bring-up, payload) were skipped. Zero artifacts were produced (`actions/runs/.../artifacts` returned `total_count: 0`), and the `macos-logs` upload found no files (annotation: `No files were found with the provided path: kernel.log ...`).
- Step log (read from the job page): `+ ./unixnu defconfig realme-c21y-rmx3261_defconfig -D .../device` then `unixnu: missing file: .../UniXNU/profiles/os/ios-16.5-20F66/profile.toml`, exit 1.
- Cause: `macos.yml` clones **upstream** UniXNU and injects only `components/SdhciBlock.toml` plus the `AAPL,phandle` fix. It never runs `scripts/install-os-profile.sh`, which the Linux `build.yml` runs before defconfig. `profiles.resolve_path()` looks up `UniXNU/profiles/os/<name>/profile.toml`, so the device-owned OS profile was invisible to the macOS job.

**Fix**
- `.github/workflows/macos.yml`: new step `Install iOS 16.5 OS profile` immediately after `Clone UniXNU core`, calling `bash device/scripts/install-os-profile.sh UniXNU` and asserting `UniXNU/profiles/os/ios-16.5-20F66/profile.toml` exists. Mirrors the Linux workflow exactly; no new files, no guessed paths.
- Note for the next gate: step `Apply BBK A2 bring-up kernel patches` uses `scripts/patch-bringup-kernel.py`; its `0x9e000000` target is the live-tree `logobuffer@9e000000` reservation (`HARDWARE_EVIDENCE.md` §9), not a guessed address. It still has to be re-verified on an actual xnu-8796 `kernel.macho` — pattern misses must be root-caused, not ignored.
- No payload/boot claim until the re-dispatched run produces a verified `kernel.macho` and `payload.img`.

## R23 — macOS payload run #2: `availability.pl` not in Xcode 26.6 SDK

**Evidence (run `45584727801`, head `9e3c883d`, job `139103318340`)**
- R22 fix confirmed: step 10 `defconfig + status` succeeded. Step 11 `Build kernel` failed after 51 s; steps 12–14 skipped, no `kernel.macho`.
- Artifact `macos-logs` id `15008039045`, 6,387 bytes, digest `sha256:1f221c71dca6cbc65b75d37d547b67dbb92d9ff0c054be9745528d079528c0d6`, downloaded via `nightly.link`. First real error in `logs/kernel-bootstrap.log`: `Unable to locate /Applications/Xcode_26.6.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk//usr/local/libexec/availability.pl (or not executable)`, then `make[5]: *** [_symbol_aliasing.h] Error 1` → `installhdrs` Error 2.
- Pinned source `c54f35ca7679`, `bsd/sys/make_symbol_aliasing.sh:37` hardcodes `AVAILABILITY_PL="${SDKROOT}/${DRIVERKITROOT}/usr/local/libexec/availability.pl"`. Xcode 26.6's MacOSX26.5 SDK does not ship that helper.
- UniXNU already solves this: `scripts/build-xnu-4k-baseline.sh:37-45` builds `availability.pl` from the pinned `AvailabilityVersions` feed into `.cache/fakeroot/usr/local/libexec/`, and line 66 exports `XNU_AVAILABILITY_PL`. `patches/xnu/local-availability.patch` makes `make_symbol_aliasing.sh` honour that variable. R18 removed the arch arm64 series (written for xnu-10063), so this generic patch was lost from the OS series.

**Fix**
- New `os-profiles/ios-16.5-20F66/patches/xnu-8796/local-availability.patch`: `AVAILABILITY_PL="${XNU_AVAILABILITY_PL:-${SDKROOT}/${DRIVERKITROOT}/usr/local/libexec/availability.pl}"`. 503 bytes, LF, ends `0x0a`; hunk `@@ -34,7 +34,7 @@` replayed byte-for-byte against the pinned `make_symbol_aliasing.sh`. Added to the OS series after `8796-non-apple-iommu-bootstrap.patch`.
- No new files, no workflow change, no guessed tool path: it uses the feed-built helper the UniXNU script already prepares.
- No payload/boot claim until a re-dispatched run produces a verified `kernel.macho` and `payload.img`.

## R24 — macOS payload run #3: fakeroot kernel headers not on the XNU include path

**Evidence (run `45587004393`, head `f70f9070`, job `139111060165`)**
- R23 fix confirmed: `installhdrs` completed; the build reached ~2.1 M log lines. Step 11 `Build kernel` still failed; steps 12–14 skipped, no `kernel.macho`.
- Artifact `macos-logs` id `15009557293`, 22,466,228 bytes, digest `sha256:f879aeb1412eb6b123e6ce882193ffbfe723aa220e4ad8b99a3a2f40d7e8978c`. `kernel-bootstrap.log` is 304,696,997 bytes.
- First compiler error (line 1,302,485): `libkern/os/log.c:33:10: fatal error: 'os/firehose_buffer_private.h' file not found`. Same error later at `bsd/kern/subr_log.c:77`.
- The header **was** installed correctly at `.cache/fakeroot/usr/local/include/kernel/os/firehose_buffer_private.h` (log lines 3786/3788, `unifdef` from the pinned libdispatch feed). `build-xnu-4k-baseline.sh:119` exports `KERNEL_SDKROOT=$ROOT/.cache/fakeroot`, and line 155 builds `libfirehose_kernel` into that fakeroot.
- Pinned `c54f35ca7679`, `makedefs/MakeInc.def:887`: `INCFLAGS_SDK = -I$(SDKROOT)/usr/local/include/kernel` — SDKROOT is the Xcode SDK, not the fakeroot DSTROOT. UniXNU's `patches/xnu/kernel-sdk-root.patch` fixes this by driving `-I` and `-L` from `KERNEL_SDKROOT`; R18 removed the arch series that carried it.

**Fix**
- New `os-profiles/ios-16.5-20F66/patches/xnu-8796/kernel-sdk-root.patch`: `export KERNEL_SDKROOT ?= $(SDKROOT)`, `LDFLAGS_KERNEL_SDK` from `$(KERNEL_SDKROOT)`, `INCFLAGS_SDK = -I$(KERNEL_SDKROOT)/usr/local/include/kernel -I$(KERNEL_SDKROOT)/usr/local/include`, `INCFLAGS_PLATFORM` from `$(KERNEL_SDKROOT)`. 1,124 bytes, LF, ends `0x0a`; hunks `@@ -642,7 +642,8 @@` and `@@ -884,8 +884,8 @@` replayed byte-for-byte against the pinned `MakeInc.def`. Added after `local-availability.patch`.
- No invented paths: every directory already comes from `build-xnu-4k-baseline.sh` and the pinned feeds.
- No payload/boot claim until a re-dispatched run produces a verified `kernel.macho` and `payload.img`.

## R25 — macOS payload run #4: non-monitor `pmap` calls left undeclared by the R21 port

**Evidence (run `45589564725`, head `226ca69e`, job `139119856889`)**
- R23/R24 fixes confirmed: `installhdrs` and all earlier steps succeeded; `Build kernel` reached ~2.85 M log lines. Step 11 still failed; steps 12–14 skipped, no `kernel.macho`.
- Artifact `macos-logs` id `15010388371`, 28,185,875 bytes, digest `sha256:82eaa6d112e9316a020929cfcb003062216fea462bfa506d8308b77725d5ff84`; `kernel-bootstrap.log` 394,516,869 bytes.
- First compiler error (line 2,273,679): `pmap.c:6323:3: error: call to undeclared function 'pmap_phys_write_disable'`. Then `pmap_ppl_lockdown_pages` (line 2,275,266), `pmap_ppl_unlockdown_pages` (2,275,409) and `static declaration of 'pmap_phys_write_disable' follows non-static declaration` (2,275,427).
- Pinned `c54f35ca7679`: `pmap.c:6315` calls `pmap_phys_write_disable()`; its `static` definition is only at `pmap.c:11938`. `pmap_cs_lockdown_pages()`/`pmap_cs_unlockdown_pages()` (`pmap.c:11620`–`11638`) call `pmap_ppl_{lock,unlock}down_pages()` in the `#else` of `#if XNU_MONITOR`, but those plural functions occur nowhere in the OSS tree. `board_config.h:90-98` defines no `XNU_MONITOR` for `BCM2837`, so the `#else` branches are live.
- UniXNU already has the fix in `patches/xnu/non-apple-iommu-bootstrap.patch` (forward declaration of `pmap_phys_write_disable`) and `patches/xnu-12377/public-pmap-without-monitor.patch` (replace the non-monitor PPL page-range calls with `#pragma unused`). The R21 8796 port copied only the include/bootstrap hunks and dropped both.

**Fix**
- Extended `8796-non-apple-iommu-bootstrap.patch` in place: added `@@ -5815,6 +5815,8 @@` (static forward declaration before `pmap_enter_options_internal`), `@@ -11620,9 +11620,10 @@` and `@@ -11630,9 +11630,10 @@` (non-monitor branches become a comment plus `#pragma unused(kva, size, ppl_writable)`). Now 1,992 bytes, LF, ends `0x0a`; all five hunks replayed byte-for-byte against the pinned `pmap.c`.
- Kept the `#if XNU_MONITOR` branches intact; no PPL behaviour was invented for Apple hardware.
- No payload/boot claim until a re-dispatched run produces a verified `kernel.macho` and `payload.img`.

## R26 — macOS payload run #5 cancelled before starting

**Evidence (run `45592510281`, head `1c7be0e9`)**
- Workflow run `failure`, job `139130078007` `cancelled`: created/started `10:11:06Z`, completed `10:26:07Z`, `steps: []`, `runner_id: 0`, `runner_name: ""`, no artifacts. The head SHA contains the R25 patch (patch commit `f7c2f5f8` is an ancestor).
- `macos.yml` has no `concurrency` group and `timeout-minutes: 360`; the 15-minute gap is not a workflow limit. No compiler ran and no log exists, so this is a runner/cancellation event, not a source failure.
- No code change is justified: re-dispatch the same head with `macos-26`, Xcode `26.6`, `kernel payload`, `upload_images=true`, `skip_bindings_check=true`, `unique_chip_id=0x8015`.

## R27 — macOS run #6 / Linux #144: `ptep_get_iommu` undefined on non-monitor pmap

**Evidence**
- macOS run #6 (`45595558329`, head `bd6839f2`, job `139140589958`): R25 fix confirmed — `pmap_phys_write_disable` and the PPL page-range calls no longer error. Step 11 still failed. Artifact `macos-logs` id `15013662453`, 26,783,842 bytes, digest `sha256:eb291b6f424d4f39f7f423675de6294940b7207837b45c19436ccae84f74132d`; first compiler error (log line 2,278,663): `pmap.c:4688:16: error: call to undeclared function 'ptep_get_iommu'` (build line = pinned 4680 + 8 R21 lines).
- Linux #144 (`45584005675`, head `dc6ddffa`, before R25): artifact `realme-c21y-build-check` id `15013247968`, 48,833,568 bytes, digest `sha256:bd008d27f071bb1d8cd295a91d2b9440f7e3fef7e89081281ba85d55acc7d43f`. Its first pmap error is the same `ptep_get_iommu` case (line 2,864,581) followed by the R25 errors, confirming one root cause across both hosts.
- Pinned `c54f35ca7679`, `pmap.c:4678-4681`: the `PMAP_OPTIONS_COMPRESSOR` panic calls `ptep_get_iommu(pte_p)` outside `#if XNU_MONITOR`; that helper appears nowhere in the OSS tree. UniXNU's `patches/xnu-12377/public-pmap-without-monitor.patch` prints `(void *)pte_p` instead, and `patches/xnu/non-apple-iommu-bootstrap.patch` makes the same substitution.

**Fix**
- Added `@@ -4678,5 +4678,5 @@` to `8796-non-apple-iommu-bootstrap.patch`: `ppnum, (void *)pte_p, pve_p);`. The patch is now 2,288 bytes, LF, ends `0x0a`; all six hunks are ascending and replayed byte-for-byte against pinned `pmap.c`.
- No stub helper, no guessed header, no behaviour change beyond the panic argument.
- No payload/boot claim until a re-dispatched run produces a verified `kernel.macho` and `payload.img`.

## R28 — macOS run #7 cancelled before starting (repeat of R26)

Run `45599346138`, head `d4869f5b`, job `139153789235`: created `10:54:02Z`, cancelled `11:09:03Z`, `steps: []`, `runner_id: 0`, no artifacts. Same 15-minute no-runner cancellation as run #5 (R26). GitHub status showed all systems operational; `macos.yml` has no concurrency group. No compiler ran, so there is no source error to fix. Re-dispatched as run #8 on the same head. A queued macOS job must be left alone until a runner is assigned; cancelling it only resets the queue.

## R29 — macOS run #8 cancelled before starting (third occurrence)

Run `45602086662`, head `d4869f5b`, job `139163320726`: created `11:11:25Z`, cancelled `11:26:26Z`, `steps: []`, `runner_id: 0`, no artifacts. Third identical 15-minute no-runner cancellation (R26, R28, R29). No code change is indicated; further blind re-dispatch is not useful. Need confirmation whether a person or an external automation is cancelling, or switch the dispatch input to `macos-15`.
