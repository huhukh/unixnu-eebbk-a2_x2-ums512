# BUILD_HISTORY — Realme C21Y XNU build-check runs

Source: GitHub Actions REST API for `huhukh/unixnu-eebbk-a2_x2-ums512`, branch `port/realme-c21y-rmx3261`. Only API-observed facts are recorded here. A successful kernel compile has **not** happened yet.

## Recent runs observed in this session

| Run | ID | Head SHA | Display title | Conclusion |
| --- | --- | --- | --- | --- |
| #121 | `45305273328` | `000f23f23736405b9b9c4ab4c06437011f54ca74` | `Fix physmap patch hunk line count` | `failure` |
| #122 | `45321064707` | `742af57f07a9cd7a453b2eb9b7fa15a3a2b88163` | `Fix malformed physmap patch hunk counts` | `failure` |
| #123 | `45332697780` | `5b980178e31e2f3fa514b376210611014b478dc7` | `Correct physmap patch hunk context counts` | `failure` |
| #124 | `45357899006` | `8d914b2f3dd35cefd09e123b67ea7a41e51864b4` | `ci: retain full XNU bootstrap logs on failure` | `failure` |
| #125 | `45384765823` | `7e1155fc266ced5837b387083bab6ee38e14fdc8` | `xnu: fix Build #124 unifdef installhdrs parse failure` | `cancelled` (PR check superseded by #126) |
| #126 | `45385291507` | `100a64ccee1d153b2baa7432a47a2b5877f09ed6` | `Merge pull request #2 from huhukh/tmp/c21y-unifdef-fix` | `failure` (step 17 link) |
| #127 | `45387172638` | `d1ef1f45a5ae11e5cb803c7addaa590c2eeaea4d` | `Create progres.md` | `cancelled` (docs-only push) |
| #128 | `45413693437` | `5c39de471823b72081f5afc6e1490ca3ccf199ff` | `xnu: define arm64_platform_sleep_hook for static kernel link` | `failure` (step 17 corrupt patch) |
| #129 | `45426457426` | `c7c6de6` | `xnu: fix missing trailing newline in platform-sleep hook patch` | `failure` (step 17 missing `[kernel.prelink]`) |
| #130-#133 | — | — | intermediate patch-series edits | `failure` |
| #134 | `45468918045` | `fbb7160`… | `os/ios-16.5: remove armvirt-platform-personality.patch duplicate` | `failure` (duplicate patch) |
| #135 | `45473909907` | `fbb71605` | `os/ios-16.5: remove all arch: patches (duplicates from soc profile)` | `failure` (step 17 `apple-only-cpu-tunables.patch`) |
| #136 | `45490266645` | `e189b2d9` | `os/ios-16.5: fix apple-only-cpu-tunables.patch line numbers` | `failure` (step 17 same patch, still wrong context) |
| #137 | `45514291870` | `0a22314e` | `fix: align CPU tunables patch with XNU 8796 source` | `failure` (step 17 same patch; hunks authored against a different `start.s`) |
| #138 | `45525087213` | `0c12f50d` | `xnu: fix apple-only-cpu-tunables hunks against xnu-8796.121.2` | in progress — EDK2 job success; Linux steps 1-15 success (step 15 compiled the then-current DTS), step 16 toolchain running |

## Build #136 detail (measured)

| Field | Value |
| --- | --- |
| Job | `138869627199` `Linux - C21Y XNU 8796 build and DTS` |
| Duration | `1h 18m 29s`; step 16 `Build Linux XNU toolchain` alone `1h 15m 33s` |
| Failed step | 17 `Build native XNU kernel`, 2 s after start |
| Command | `python3 ./unixnu build kernel --skip-prelink -D <ws> --out <ws>/out` |
| Failing patcher | `== kernel: patch apple-only-cpu-tunables.patch` → `error: patch failed: osfmk/arm64/start.s:33` / `patch does not apply` |
| Steps 1-15 | all success (`Fetch build sources` 26 s, `Compile C21Y device tree` 0 s) |
| EDK2 job `138869626702` | success, 2m 18s, artifact `realme-c21y-edk2-scaffold` produced |
| `kernel.macho` | not produced; link stage never reached |

The `1h 15m` toolchain step dominates every iteration. Any change that only affects XNU patching still costs ~78 min of wall clock, so patches must be validated before pushing (see R17).

## Build #124 detail

| Field | Value |
| --- | --- |
| URL | `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45357899006` |
| Event | `push` |
| Created / updated | `2026-11-24T08:38:32Z` / `2026-11-24T10:21:02Z` |
| Check suite | `122731926230` |
| PR | #1, base `main` `7149f64a91cbfc8ef3cbe84c75d42c8f5050f7f2` |
| Job `138320222000` | `Linux - C21Y XNU 8796 build and DTS` — **failure**, failed in step 17 `Build native XNU kernel` after about 13 s |
| Job `138320222584` | `EDK2 - C21Y firmware-volume compile (scaffold)` — **success** |
| Steps before failure | checkout, disk free, Python/tomllib, dependencies, file checks, UEFI audit, clone UniXNU, install OS profile, defconfig, fetch, tree, status, DTS compile, Linux XNU toolchain — all succeeded |
| Observed failure text | `Parse failure for .../libkern/libkern/c++/OSEndianTypes.h` |
| Root cause | Host `unifdef 2.10` parse exit 2 on two XNU 8796 headers; see `RESEARCH_LOG.md` R5-R11 |
| Artifact `realme-c21y-build-check` | ID `14909948672`, 11,318 bytes, digest `sha256:c352060104fd378c8f2933d51f264d60a55db81f3ace481c6d4f1eef811cc11c`, expires `2026-12-01T10:20:58Z` |
| Artifact `realme-c21y-edk2-scaffold` | ID `14902598505`, 70,590 bytes |
| `kernel.macho` in #124 | Not produced by the failing job; artifact contents could not be downloaded without authentication |
| Public log body | Not retrievable: job HTML requires sign-in and the log/artifact APIs return `401`/`403` unauthenticated |

## Build #126 detail

| Field | Value |
| --- | --- |
| URL | `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45385291507` |
| Event | `push` (merge commit of PR #2) |
| Created / updated | `2026-11-24T11:33:39Z` / `2026-11-24T13:00:20Z` |
| Job `138414510202` | `Linux - C21Y XNU 8796 build and DTS` — **failure**, step 17 `Build native XNU kernel` |
| Job `138414509792` | `EDK2 - C21Y firmware-volume compile (scaffold)` — **success** |
| Steps before failure | 1–16 all `success`, including step 13 `Assemble build tree` (unifdef patch applied) and step 16 `Build Linux XNU toolchain` |
| Observed failure text | `Undefined symbols for architecture arm64: "_arm64_platform_sleep_hook", referenced from: __ZN6ArmCpu5startEP9IOService in libArmCpu.a(ArmCpu.o)`; `ld: symbol(s) not found for architecture arm64` |
| Parse failure | **Absent** — the unifdef fix worked |
| Root cause | `ArmCpu.cpp` declares the board sleep hook `weak_import`; a static kernel link requires it defined, and the C21Y series had no board XNU patch defining it. See `RESEARCH_LOG.md` R13 |
| Artifact `realme-c21y-build-check` | ID `14922332850`, 71,555,458 bytes, digest `sha256:f9380b35bf0b303f80009cd3076998060f611db981bde788b1efe42d871166bc` |
| Artifact `realme-c21y-edk2-scaffold` | ID `14915378514`, 70,594 bytes, digest `sha256:147fb256917c9218e76109efc1806b2355823fac3a00e139d7d198de69f21d1b` |
| `kernel.macho` in #126 | **Not produced**: the link failed before the `find ... kernel.macho` gate. The 71.5 MB artifact holds `build/`, logs and `status.json`, not a kernel |

## Fix state after Build #126

| Item | State |
| --- | --- |
| Unifdef fix | `patches/xnu/8796-unifdef-headers.patch` merged at `100a64ccee`; step 13 applied it; no `Parse failure` in #126 |
| Link fix | `patches/xnu/8796-arm64-platform-sleep-hook.patch` created; pre-image blob `94e91306…` matches the pinned tree, post-image `9a43e588…` reproduced locally; added to `patches/xnu/series` |
| Commit/push of link fix | Pending the next commit on `port/realme-c21y-rmx3261` |
| New CI run after link fix | Not started |
| Compiled ARM64 kernel | **Not verified** |

## Build #128 detail

| Field | Value |
| --- | --- |
| URL | `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45413693437` |
| Event | `push` (commit `5c39de471823b72081f5afc6e1490ca3ccf199ff`) |
| Created / updated | `2026-11-24T14:24:15Z` / `2026-11-24T15:27:56Z` (~1h 3m) |
| Job | `Linux - C21Y XNU 8796 build and DTS` — **failure** at step 17 (`Build native XNU kernel`) instantly (1s) |
| Observed failure text | `unixnu: git failed (128): error: corrupt patch at .../patches/xnu/8796-arm64-platform-sleep-hook.patch:18` |
| Root cause | The new patch file lacked a trailing newline (EOF at line 18 without LF), causing `git apply` to reject it as corrupt. See `RESEARCH_LOG.md` R15 |
| Fix | Added trailing LF to `patches/xnu/8796-arm64-platform-sleep-hook.patch` (now 749 bytes), committed as `c7c6de6` (Build #129 in progress) |

## Build #129 detail

| Field | Value |
| --- | --- |
| URL | `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45426457426` |
| Event | `push` (commit `c7c6de6`) |
| Created / updated | `2026-11-24T18:00Z` / `2026-11-24T19:24Z` (~1h 24m) |
| Job | `Linux - C21Y XNU 8796 build and DTS` — **failure** at step 17 (`Build native XNU kernel`) during `build-xnu-4k-baseline.sh` |
| Observed failure text | `unixnu: board.toml has no [kernel.prelink]` |
| Root cause | The build harness checks for a `[kernel.prelink]` section in `board.toml` before prelinking components (`DarwinBoot`, `XnuPrelink`), which was missing. See `RESEARCH_LOG.md` R16 |
| Fix | Added `[kernel.prelink]` to `board.toml`, committed and pushed to trigger Build #130 |

## Success criteria for the next run

Do not claim compile success unless all of the following are true:

1. A new workflow run on branch `port/realme-c21y-rmx3261` exists with head SHA equal to the commit containing the patch.
2. Job `Linux - C21Y XNU 8796 build and DTS` has `conclusion: success`.
3. The `realme-c21y-build-check` artifact contains a non-empty path matching `out/**/kernel/kernel.macho`.
4. The artifact's SHA-256 is recorded and the file is checked as a Mach-O ARM64 kernel (not just a nonzero file).
5. Any new failure is root-caused and recorded here before another change is made.

Boot and hardware support are separate gates and are not satisfied by a successful kernel compile.
