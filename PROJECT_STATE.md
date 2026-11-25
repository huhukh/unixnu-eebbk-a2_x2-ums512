# PROJECT_STATE — Realme C21Y RMX3261 / UMS512 XNU 16.5 port

_Last updated: 2026-11-25 (Build #143 root cause R21). All statements below are evidence-bound. Compile, boot and hardware support are separate claims._

## 0. Current gate (read this first)

Builds #138/#139/#140 all failed step 17 because of a **TOML table-scope bug**, not the R17 patch. At head `0c12f50d`, `board.toml` put `[kernel.prelink]` before its `config_fragments`/`patch_series`/`archives`, so those arrays belonged to `[kernel.prelink]`. The resolved `status.json` in run #138 proves `[kernel].patch_series` still came from the arch profile: `arch → soc → os → device`. The **first** patch applied was therefore UniXNU's xnu-10063-era `patches/xnu/apple-only-cpu-tunables.patch`, which fails at `start.s:33`; our fixed OS patch (`f94c73d2`) was never reached and replays cleanly offline.

Commit `3614a701` moved `[kernel.prelink]` to the end of `board.toml`, so the board resolves `patch_series = soc → os → device` and adds the missing SoC/OS config fragments. Build #141 failed at step 11 on a UTF-8 BOM written by that upload (R19); `4b3a42e3` removed it. Build #142 (`45542624841`) reached real XNU compilation and failed on the duplicate `reserved10` field (R20). **Build #143 (`45565371465`, head `5d6b6e3`) confirms R20 fixed**: steps 1–16 green, step 17 failed after 2m 05s on the missing Apple PPL header `arm64/ppl/sart.h` (R21). The fix is `8796-non-apple-iommu-bootstrap.patch`, validated offline. Compile, boot and hardware claims remain unproven.

While #138 runs, the device tree was rebuilt from the live hardware and separately validated:

- `3f4c55d0` — `soc/UniXNU-ums512-common/dts/ums512.dtsi` corrected against live `/proc/device-tree` bytes (PSCI 0.2 only, no `/timer` clock-frequency, GIC 2/2 cells + maintenance PPI 9 + standard `phandle`, UART `sprd,ums518-uart` first).
- `f09d4fa1` — `dts/realme-c21y-rmx3261.dts` rebuilt (was a 681-byte stub with **no** `device_type = "memory"` node, which the ADT generator hard-rejects): one contiguous DRAM range `0x80000000`/`0xfffff000`, the 17 live reserved-memory regions, `sprd,ums512`-only compatible, `stdout-path`.
- `3614a701` — `[payload.adt] chip_id = "0x8015"` (mandatory: `devicetree.py:313` reads it whenever `--unique-chip-id` is passed); profile-derived OS identity, not a Unisoc hardware ID.
- Builds #139 (head `3f4c55d0`) and #140 (head `f09d4fa1`) both **passed step 15 `Compile C21Y device tree`**, so `dtc` accepts the new DTS and DTSI. That is a syntax/cell-count proof only, not an ADT or hardware proof.

The earlier root cause, kept for the record (docs/RESEARCH_LOG.md R17): the patch's second hunk was authored for a different `start.s`. It declared `@@ -783,10 +785,13 @@` and closed with `#if HAS_CLUSTER && !NO_CPU_OVRD`; the pinned release `xnu-8796.121.2` / commit `c54f35ca7679` has `#endif // APPLE_ARM64_ARCH_FAMILY` at line 775, the MIDR block at 777-780, and `#if HAS_CLUSTER` (no `&& !NO_CPU_OVRD`) at 783. The same two defects existed in upstream `zus12873/UniXNU:patches/xnu/apple-only-cpu-tunables.patch`.

The patch now carries hunks `@@ -33,7 +33,9 @@` and `@@ -775,9 +777,11 @@`, verified byte-for-byte against the CI-pinned file. All 60 hunks of the 12 OS-series patches were replayed against the pinned tree; this was the only genuine mismatch.

Secondary finding: `osfmk/arm64/tunables/tunables.s` and the `APPLY_TUNABLES` macro do **not** exist in `xnu-8796.121.2` nor `xnu-10063.141.1`, and `APPLE_ARM64_ARCH_FAMILY` is undefined for this board, so the guard added by the patch is what keeps assemble working. The patch is mandatory, not cosmetic.

## 1. Exact source state

| Item | Verified value |
| --- | --- |
| Repository | `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512` |
| Branch | `port/realme-c21y-rmx3261` |
| Branch HEAD at Build #126 | `100a64ccee1d153b2baa7432a47a2b5877f09ed6` (merge of PR #2) |
| Docs commits after #126 | `355ac68429`, `632d60beb1`, `425233e627` — all `[skip ci]`, no new run |
| PR | #2, `tmp/c21y-unifdef-fix` -> `port/realme-c21y-rmx3261`, merged |
| Latest workflow run | #143 (`45565371465`, `5d6b6e3`) — steps 1–16 success, step 17 compile failure `'arm64/ppl/sart.h' file not found` (R21); #142 R20, #141 BOM (R19), #138–#140 arch patch (R18) |
| Build #127 | `45387172638`, cancelled (docs-only `progres.md` push) |
| Previous failure | Build #124, step 17 `Build native XNU kernel`, `Parse failure` (unifdef 2.10) |
| Local snapshot | `C:\Users\Randika Aryasatya\Documents\Default Project\unixnu-eebbk-a2_x2-ums512-8d914b2f3dd35cefd09e123b67ea7a41e51864b4` |
| XNU source | `apple-oss-distributions/xnu` tag `xnu-8796.121.2` → commit `c54f35ca767986246321eb901baf8f5ff7923f6a`, equal to the OS-profile pin |
| UniXNU core | `main` snapshot at `8542980d02b4d2cc5c32ee3542de1760b2562aac` (latest before Build #124 completed) |

The requested checkpoint documents were absent from the branch snapshot at the start of this session. They are now created in this repository.

## 2. Root cause of Build #124 `Parse failure`

The failing message is emitted by XNU's own installhdrs rule, not by the C21Y source, the DTS, the EDK2 job, or the device configuration:

- `xnu-8796.121.2/makedefs/MakeInc.rule:78-82` runs `$(UNIFDEF)` and, when its exit status is `2`, prints `Parse failure for $<` and exits.
- The failing header is `libkern/libkern/c++/OSEndianTypes.h`, a `DATAFILES` entry in `libkern/libkern/c++/Makefile:23`.
- The CI runner is `ubuntu-22.04`; Ubuntu jammy ships `unifdef 2.10-1.1build0.2`. UniXNU's Linux toolchain installer lists apt `unifdef` as a dependency and does not override its version.
- Local reproduction with an independently built `unifdef 2.10` using XNU's `DATA_UNIFDEF`-style flags produced exit `2`:
  `Premature EOF (#if line 125 depth 1)`.
- The same source with `unifdef 2.12` exits `0`.
- UniXNU's own device records document the same class of failure: `enuma.md` required system `unifdef 2.10` → `2.12` because 2.10 fails `installhdrs`; `nuwa.md` records an `8796-unifdef-headers` patch for "two headers the host unifdef 2.10 rejects".
- The upstream Nuwa patch fixes exactly these two headers: `bsd/net/pfvar.h` and `libkern/libkern/c++/OSEndianTypes.h`. Its pre-image git blob hashes match the pinned C21Y XNU revision byte-for-byte, and its post-image hashes were reproduced locally.
- Debug output shows the mechanism: the bare `#error` at `pfvar.h:148` leaves unifdef 2.10's directive state dirty, so the following `#endif` at line 149 is parsed as `PLAIN`; giving `#error` a message restores `ENDIF`. The two multi-line `#endif /* ...` comments in `OSEndianTypes.h` are the other dodgy directives.

`MACHINE_CONFIGS=BCM2837` is **not** the root cause. It is passed by UniXNU `scripts/build-xnu-4k-baseline.sh:147-148` to every Linux baseline build and is unrelated to the unifdef parser exit.

## 3. Fix merged and pushed

| File | Change |
| --- | --- |
| `patches/xnu/8796-unifdef-headers.patch` | New patch. Adds a message to bare `#error`; collapses two multi-line `#endif` comments to single lines. |
| `patches/xnu/series` | Adds the patch before `sdhci-block-personality.patch`, with the evidence note. |
| `PROJECT_STATE.md`, `docs/RESEARCH_LOG.md`, `docs/BUILD_HISTORY.md`, `docs/HARDWARE_EVIDENCE.md`, `docs/NEXT_SESSION.md` | Checkpoint records. |
| Merge | PR #2 merged to `port/realme-c21y-rmx3261` at `100a64ccee1d153b2baa7432a47a2b5877f09ed6`. |

Why this fix: it is the smallest change that removes the exact constructs unifdef 2.10 misparses, it matches a proven upstream device-port fix, and its blob hashes prove it applies to the exact pinned XNU source. No guessed address, register, memory map, config value or toolchain assumption is introduced.

Local verification performed:
- `unifdef 2.10` on unpatched `OSEndianTypes.h`: exit `2`.
- `unifdef 2.10` on patched `OSEndianTypes.h`: exit `0`.
- `unifdef 2.10` on unpatched `pfvar.h`: exit `2`, `Premature EOF (#if line 63 depth 1)`.
- `unifdef 2.10` on patched `pfvar.h`: exit `1` (normal "some changes made" status for unifdef).
- `unifdef 2.12` on unpatched `OSEndianTypes.h`: exit `0`.
- Git blob pre/post hashes match the Nuwa patch post-images exactly.

## 3a. Build #126 link failure and fix

Build #126 proved the unifdef fix: step 13 applied the patch, no `Parse failure` appears, step 16 built the toolchain, and step 17 reached the kernel link. It then failed with exactly one undefined symbol:

```
Undefined symbols for architecture arm64:
  "_arm64_platform_sleep_hook", referenced from:
      __ZN6ArmCpu5startEP9IOService in libArmCpu.a(ArmCpu.o)
ld: symbol(s) not found for architecture arm64
```

Root cause, from source:

- `UniXNU/ArmCpu` revision `5f370269…`, `ArmCpu.cpp:65`, declares the board sleep hook `weak_import`.
- The pinned XNU `osfmk/arm64/cpu.c` (blob `94e91306b14364f720ea80e46d853035aabd78e6`) never defines it.
- UniXNU's device records state that a **static** kernel link refuses to leave any `weak_import` undefined. `weak_import` only defers resolution for Darwin dynamic linking.
- The newer-XNU reference patch defines the hook and calls it from `ml_arm_sleep`, but it also calls `arm_init_cpu()`, which does not exist in xnu-8796.

Fix: `patches/xnu/8796-arm64-platform-sleep-hook.patch` defines

```c
void (*arm64_platform_sleep_hook)(boolean_t boot_cpu) = NULL;
```

in `osfmk/arm64/cpu.c`, and is added to `patches/xnu/series`. The pre-image blob hash matches GitHub's tree entry for the pinned commit; the hunk reproduces post-image `9a43e588…`. No call site is added on 8796, and the kernel args do not set `platform-sleep=1`, so sleep behaviour is unchanged. This is a link fix only; sleep support remains a separate, unverified feature.

## 4. Claim boundaries

| Claim | Status |
| --- | --- |
| Host reproduction of the parser failure | **Done** |
| Minimal source fix identified and locally verified | **Done** |
| Fix committed and pushed to GitHub | **Done** — PR #2 merged at `100a64ccee1d153b2baa7432a47a2b5877f09ed6` |
| Unifdef fix proven in CI | **Done** — Build #126 applied the patch, no `Parse failure` |
| Build #126 kernel link | **Failed** — one undefined symbol, `_arm64_platform_sleep_hook` |
| Link fix committed | **Done** — Build #126's undefined symbol was resolved; no such error in #142 |
| GitHub Actions XNU kernel compile success | **Not yet** |
| Non-empty `kernel.macho` artifact verified | **Not yet** — Build #126 failed before the `kernel.macho` gate; its artifact holds logs/build output only |
| Live hardware evidence over ADB (read-only) | **Done** — memory map, GIC, PSCI, CPU, storage; see `docs/HARDWARE_EVIDENCE.md` |
| Boot success on Realme C21Y | **Not claimed** |
| Full hardware support | **Not claimed**; only the evidence in `docs/HARDWARE_EVIDENCE.md` is established |
| Device writes / flashing / reboot | **None** in this session |

## 5. Immediate next action

Commit `os-profiles/ios-16.5-20F66/patches/xnu-8796/8796-non-apple-iommu-bootstrap.patch`, its OS `series` entry, and these records to `port/realme-c21y-rmx3261` **without** `[skip ci]`, so CI runs again. Success requires the `Linux - C21Y XNU 8796 build and DTS` job to finish `success` with a non-empty `kernel.macho` whose SHA-256 and Mach-O ARM64 header are verified. Linux rerun #144 (`45584005675`, head `dc6ddffa`) is active. macOS runs #2/#3 failed at `Build kernel`: R23 (Xcode lacks `availability.pl`) fixed by `local-availability.patch`; R24 (fakeroot kernel headers off the XNU `-I` path) fixed by `kernel-sdk-root.patch`. Both validated against `c54f35ca7679` and queued in the OS series. Run #4 (`45589564725`) failed on R25: the R21 8796 port omitted the `pmap_phys_write_disable` forward declaration and the non-monitor no-op branches; both were restored in `8796-non-apple-iommu-bootstrap.patch` and validated byte-for-byte. Run #5 (`45592510281`) was cancelled before any step ran (R26); run #6 (`45595558329`) reached the kernel and failed on `ptep_get_iommu` (R27). Linux #144 (`45584005675`) showed the same pmap errors. R27 fix added to `8796-non-apple-iommu-bootstrap.patch` (6 hunks validated). Run #7 (`45599346138`) was cancelled before any step ran (R28); run #8 (`45602086662`) was also cancelled before a runner was assigned (R29). Paused: need to know who cancels, or dispatch with `macos-15`. Linux build #146 is still running. Do not flash/boot until both produce verified artifacts.

## 6. Checkpoint commands

- `STATUS` — print this state without changing files.
- `SAVE` — refresh these checkpoint files after a new measurement.
- `CHECKPOINT` — write the current state and record the evidence IDs.
- `CONTINUE` — resume from the unresolved build step.
- `HANDOFF` — prepare the exact next-session packet from `docs/NEXT_SESSION.md`.
