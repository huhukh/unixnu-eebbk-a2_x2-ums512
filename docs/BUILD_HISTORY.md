# BUILD_HISTORY — Realme C21Y XNU build-check runs

Source: GitHub Actions REST API for `huhukh/unixnu-eebbk-a2_x2-ums512`, branch `port/realme-c21y-rmx3261`. Only API-observed facts are recorded here. A successful kernel compile has **not** happened yet.

## Recent runs observed in this session

| Run | ID | Head SHA | Display title | Conclusion |
| --- | --- | --- | --- | --- |
| #121 | `45305273328` | `000f23f23736405b9b9c4ab4c06437011f54ca74` | `Fix physmap patch hunk line count` | `failure` |
| #122 | `45321064707` | `742af57f07a9cd7a453b2eb9b7fa15a3a2b88163` | `Fix malformed physmap patch hunk counts` | `failure` |
| #123 | `45332697780` | `5b980178e31e2f3fa514b376210611014b478dc7` | `Correct physmap patch hunk context counts` | `failure` |
| #124 | `45357899006` | `8d914b2f3dd35cefd09e123b67ea7a41e51864b4` | `ci: retain full XNU bootstrap logs on failure` | `failure` |

Run #124 is the current branch HEAD and the run analysed in `RESEARCH_LOG.md`.

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

## Fix state after this session

| Item | State |
| --- | --- |
| Local patch | `patches/xnu/8796-unifdef-headers.patch` created and added to `patches/xnu/series` |
| Local parser reproduction | Fixed under unifdef 2.10 for both headers; see `RESEARCH_LOG.md` R10 |
| Commit/push | **Not done** (no `git`, `gh` or token in the current environment) |
| New CI run | **Not started** |
| Compiled ARM64 kernel | **Not verified** |

## Success criteria for the next run

Do not claim compile success unless all of the following are true:

1. A new workflow run on branch `port/realme-c21y-rmx3261` exists with head SHA equal to the commit containing the patch.
2. Job `Linux - C21Y XNU 8796 build and DTS` has `conclusion: success`.
3. The `realme-c21y-build-check` artifact contains a non-empty path matching `out/**/kernel/kernel.macho`.
4. The artifact's SHA-256 is recorded and the file is checked as a Mach-O ARM64 kernel (not just a nonzero file).
5. Any new failure is root-caused and recorded here before another change is made.

Boot and hardware support are separate gates and are not satisfied by a successful kernel compile.
