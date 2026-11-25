# NEXT_SESSION — exact continuation packet

## 0. Start here

Read in this order:

1. `PROJECT_STATE.md` §0 (current gate) and §1
2. `docs/RESEARCH_LOG.md` R17 (the active root cause) and R9–R13 (closed history)
3. `docs/BUILD_HISTORY.md` Build #136 detail
4. `docs/HARDWARE_EVIDENCE.md` §2.1, §3, §4.1
5. `os-profiles/ios-16.5-20F66/patches/xnu/series` and the 12 files under `os-profiles/ios-16.5-20F66/patches/xnu-8796/`

Do not re-investigate the unifdef failure (closed, R9–R12) or the
`arm64_platform_sleep_hook` link failure (closed, R13). The active gate is the
`apple-only-cpu-tunables.patch` context mismatch (R17).

## 1. Current state

| Item | Value |
| --- | --- |
| Branch | `port/realme-c21y-rmx3261` |
| Build #136 | run `45490266645`, head `e189b2d9`, `failure` — step 17, 2 s after start |
| Build #137 | run `45514291870`, head `0a22314e`, same patch defect; do not wait on it |
| Failing command | `python3 ./unixnu build kernel --skip-prelink -D <ws> --out <ws>/out` |
| Failing patcher | `== kernel: patch apple-only-cpu-tunables.patch` |
| `kernel.macho` | Never produced. The link stage has never been reached. |
| Step 16 cost | `Build Linux XNU toolchain` = 1 h 15 m 33 s of the 1 h 18 m 29 s job |

## 2. Local delta (ready to commit, unverified in CI)

- `os-profiles/ios-16.5-20F66/patches/xnu-8796/apple-only-cpu-tunables.patch` — rewritten. Hunks `@@ -33,7 +33,9 @@` and `@@ -775,9 +777,11 @@`. `index` line removed. 572 bytes, LF only, trailing newline present, leading space preserved on tab-indented context lines.
- `PROJECT_STATE.md`, `docs/RESEARCH_LOG.md` (R17), `docs/BUILD_HISTORY.md` (build table + #136 detail), `docs/HARDWARE_EVIDENCE.md` (§4.1, safety ledger), `docs/NEXT_SESSION.md`, `progres.md` — updated.

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

Commit the single patch file (plus the docs) **without** `[skip ci]`.

Recommended message:

```
xnu: fix apple-only-cpu-tunables hunks against xnu-8796.121.2
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
- Do not re-add any `arch:` patch to the OS series; the SOC profile already applies `arch:patches/xnu/series`.

## 8. Hard restrictions

- No flashing, rebooting, partition writes or mutating device commands without explicit approval. Read-only ADB is allowed and was used again on 2026-11-25 (`/proc/config.gz`, `/proc/timer_list`, `/proc/interrupts`, `/proc/iomem`, `/sys/devices/system/clocksource`, `/proc/device-tree` listing).
- Do not treat the iPhone10,3/D22AP identity as real C21Y hardware identity.
- Do not treat the EDK2 `.fd` scaffold as flashable firmware.
- Do not fill memory maps with estimates.
- Do not claim boot or hardware support from a compile artifact.
