# NEXT_SESSION — exact continuation packet

## 0. Start here

Read in this order:

1. `PROJECT_STATE.md` §0 (current gate) and §1
2. `docs/RESEARCH_LOG.md` **R21** (active root cause), then R20/R19/R18 (closed gates), R17 and R9–R13
3. `docs/BUILD_HISTORY.md` Build #143 detail and the run table
4. `docs/HARDWARE_EVIDENCE.md` §2.1, §3, §4.1, §8
5. `board.toml` `[kernel]` and the three `patch_series` files

Do not re-investigate the unifdef failure (closed, R9–R12), the
`arm64_platform_sleep_hook` link failure (closed, R13), or the R17 patch context
(fixed in `0c12f50d` and replayed with zero mismatches), or the BOM gate (R19).
**Immediate action:** commit the R21 patch and trigger CI without `[skip ci]`.
Build #143 confirmed R20 fixed and died on xnu-8796's unguarded Apple PPL
SART/UAT include/calls; R21's fix is in CI as build #144 (`45584005675`).
macOS run #1 (`45573253682`) failed on a missing OS profile (R22, fixed);
runs #2–#4 failed at `Build kernel`: R23 (Xcode's missing `availability.pl`),
R24 (fakeroot kernel headers off the `-I` path), then R25 (the R21 8796 port
dropped the `pmap_phys_write_disable` forward declaration and the no-monitor
no-op branches). All three fixes are validated; run #5 must be dispatched.

## 1. Current state

| Item | Value |
| --- | --- |
| Branch | `port/realme-c21y-rmx3261` |
| Build #136 | run `45490266645`, head `e189b2d9`, `failure` — step 17, 2 s after start |
| Build #137 | run `45514291870`, head `0a22314e`, same patch defect; do not wait on it |
| Build #143 | run `45565371465`, head `5d6b6e3`, steps 1–16 success, step 17 compile failure `'arm64/ppl/sart.h' file not found` (R21); R20 fix confirmed |
| Failing command | `python3 ./unixnu build kernel --skip-prelink -D <ws> --out <ws>/out` |
| `kernel.macho` | Never produced. Link stage has never been reached. |
| Step 16 cost | 1 h 45 m 14 s in #142 (dominates every iteration) |

## 2. Local delta (ready to commit)

**(a) The R21 XNU patch — new, validated offline, not yet committed:**

- `os-profiles/ios-16.5-20F66/patches/xnu-8796/8796-non-apple-iommu-bootstrap.patch` — guard the `arm64/ppl/sart.h` / `uat.h` includes and the `sart_bootstrap()` / `uat_bootstrap()` calls in `pmap.c` with `XNU_MONITOR_ANS2_SART` / `XNU_MONITOR_UAT_PPL`. 982 bytes, LF, both hunks replayed byte-for-byte against `c54f35ca7679`.
- `os-profiles/ios-16.5-20F66/patches/xnu/series` — adds it after `apple-only-cpu-tunables.patch`.
- R20's `8796-pmap-no-pac-reserved10.patch` is already committed; build #143 proves that error is gone.

**(b) Device-tree / ADT corrections — already committed and validated by `dtc` in #139/#140:**

- `dts/realme-c21y-rmx3261.dts` — rewritten (was a 681-byte stub with no memory node). Adds `/memory@80000000 reg = <0 0x80000000 0 0xfffff000>`, the full 17-region `/reserved-memory` from the live tree (`tos-mem` corrected to `0x94060000`/`0x4fa0000`), `compatible = "sprd,ums512"` only, `stdout-path`.
- `soc/UniXNU-ums512-common/dts/ums512.dtsi` — `psci` reduced to `"arm,psci-0.2"`; invented `/timer` `clock-frequency` removed; GIC `#address-cells`/`#size-cells` = 2, `interrupts = <1 9 4>` added, `AAPL,phandle` → `phandle`; UART compatible order `"sprd,ums518-uart"`, `"sprd,sc9836-uart"`.
- `board.toml` — `[payload.adt] chip_id = "0x8015"` added (profile-derived, see `docs/HARDWARE_EVIDENCE.md` §8.4; without it `devicetree.py:313` raises `KeyError`).
- `docs/HARDWARE_EVIDENCE.md` §8, `progres.md` — the byte-level evidence and the 8 proven DTS defects.

Rationale for each value is in `docs/HARDWARE_EVIDENCE.md` §8; nothing was guessed.

Verification already performed offline, against `apple-oss-distributions/xnu` commit `c54f35ca767986246321eb901baf8f5ff7923f6a` (`osfmk/arm64/start.s`, 873 lines, fetched during this session):

- hunk 1 context matches lines 33-39 exactly;
- hunk 2 context matches lines 775-783 exactly;
- all 60 hunks across all 12 OS-series patches were replayed; the only genuine mismatch was this patch;
- `clang-uio-stackbuf` (`sys_generic.c`, `vfs_lookup.c`), `native-aes-personality`, `zzx-pmap-sync-64bit-pa` report offsets because earlier patches shift text — `git apply` tolerates that.

## 3. Environment

The shell still has **no `git`, no `gh`, no `python`, no local XNU toolchain** and no token. GitHub writes go through the authenticated browser session (`huhukh`).

Reliable read paths found this session:

- `fetch()` from the Code Mode runtime reaches `api.github.com` and `raw.githubusercontent.com` directly. This is far faster and more reliable than driving the Actions UI: runs, jobs, steps and commit trees are all readable that way.
- `curl`/`Invoke-WebRequest` work from PowerShell for `raw.githubusercontent.com`.
- `adb` at `C:\Users\Randika Aryasatya\AppData\Local\Android\Sdk\platform-tools\adb.exe` reaches the device read-only as root (Magisk).

Do not fabricate a commit SHA; read it back from the API after committing.

## 4. Commit and trigger the next run

Two separate pushes, in this order:

1. **Do not touch anything while #138 runs.** It is the proof run for the patch fix.
2. When #138 finishes, commit the DTS + `board.toml` + docs delta **without**
   `[skip ci]`, so the next run's step 15 (`Compile C21Y device tree`) validates
   the DTS with the real `dtc` — the only `dtc` available in this environment.

Recommended messages:

```
dts: rebuild C21Y board tree from live /proc/device-tree bytes
```

```
adt: declare payload.adt chip_id and document live-DT reconciliation
```

Then confirm from the API that a new run exists with that head SHA:

```
https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs?branch=port%2Frealme-c21y-rmx3261&per_page=3
```

## 5. Verify the new run

```
https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/<ID>/jobs
https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/<ID>/artifacts
```

Require all of:

1. new run head SHA equals the push commit;
2. `Build Linux XNU toolchain` completes (about 75 min — expect it, do not abort);
3. `Build native XNU kernel` passes the patch phase and reaches the link;
4. job conclusion `success`;
5. artifact `realme-c21y-build-check` contains a non-empty `kernel.macho`;
6. record its size and SHA-256, and show a Mach-O ARM64 header (`file` output or a header parse), not merely its existence.

Only then may the state read "compiled ARM64 kernel achieved".

## 6. If it still fails

Expected failure classes, in order of likelihood, all still unproven:

- **`dtc` rejects the new DTS** (step 15, fails ~4 min into the Linux job). Classes: duplicate labels, a `reg` whose cell count does not match the parent's `#address-cells`/`#size-cells`, or a phandle that never resolves. This is cheap to iterate: step 15 runs before the 75-minute toolchain step.
- **Another OS-series patch that only applies with an offset larger than `git apply` tolerates**, or a later patch whose context was built on top of this one. Fix by replaying the hunk against the pinned tree before pushing, as done here.
- **`APPLY_TUNABLES` or `arm64/tunables/tunables.s` reached anyway.** If `APPLE_ARM64_ARCH_FAMILY` turns out to be defined by the actual build flags, the guard is a no-op and assemble fails on a missing file. Evidence to collect first: the exact `-D` flags in the failing compile line.
- **A later `weak_import` with no strong definition** — the #126 log listed exactly one symbol, but later objects can add more.
- **`VA_BITS=39` vs XNU expectations**: the stock kernel is 39-bit VA / 4 KiB granule (measured, `docs/HARDWARE_EVIDENCE.md` §4.1). If XNU's arm64 tables assume otherwise, expect a pmap assertion, not a compile error — that would be a boot-stage finding, not a build fix.

For each: get the failing step from the jobs API, read the step log, root-cause from the command and source, add an `Rxx` entry, then make the smallest evidence-backed change.

## 7. What not to do

- Do not add `-Wl,-undefined,dynamic_lookup` or any linker relaxation.
- Do not port `xnu-12377` sleep call sites: they call `arm_init_cpu()`, absent in 8796.
- Do not set `platform-sleep=1`.
- Do not "fix" the reported offsets in `clang-uio-stackbuf`, `native-aes-personality` or `zzx-pmap-sync-64bit-pa` — they apply correctly.
- Do not re-add any `arch:` patch to the OS series or let `board.toml` fall back to `arch:patches/xnu/series`: that series targets xnu-10063 and fails at `start.s:33` on xnu-8796 (R18). Keep `[kernel].patch_series = soc → os → device` and keep `[kernel.prelink]` at the end of the file.
- Do not add UART `clocks` phandles until a UMS512 clock-controller node with proven register data exists: `devicetree.py` hard-fails on an unresolved reference, and a fake provider is worse than a missing one.
- Do not split `/memory@80000000` into banks or "restore" the static 2 GiB `0x80000000` size from the old notes: the ADT generator requires one contiguous range and the live tree says `0xfffff000`.
- Do not write `AAPL,phandle` by hand in the DTS. `dtc` needs the standard `phandle` to resolve `&gic`; the macOS workflow rewrites `phandle` → `AAPL,phandle` when it emits the ADT.

## 8. Hard restrictions

- No flashing, rebooting, partition writes or mutating device commands without explicit approval. Read-only ADB is allowed and was used again on 2026-11-25 (`/proc/config.gz`, `/proc/timer_list`, `/proc/interrupts`, `/proc/iomem`, `/sys/devices/system/clocksource`, `/proc/device-tree` listing).
- Do not treat the iPhone10,3/D22AP identity as real C21Y hardware identity.
- Do not treat the EDK2 `.fd` scaffold as flashable firmware.
- Do not fill memory maps with estimates.
- Do not claim boot or hardware support from a compile artifact.
