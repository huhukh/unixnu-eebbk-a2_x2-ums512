# PROJECT_STATE — Realme C21Y RMX3261 / UMS512 XNU 16.5 port

_Last updated: 2026-11-24 (continuation session). All statements below are evidence-bound. Compile, boot and hardware support are separate claims._

## 1. Exact source state

| Item | Verified value |
| --- | --- |
| Repository | `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512` |
| Branch | `port/realme-c21y-rmx3261` |
| Branch HEAD | `8d914b2f3dd35cefd09e123b67ea7a41e51864b4` (`ci: retain full XNU bootstrap logs on failure`) |
| PR | #1, base `main` at `7149f64a91cbfc8ef3cbe84c75d42c8f5050f7f2` |
| Latest workflow run | Build #124, `https://github.com/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/45357899006`, `failure` |
| Failing job | `138320222000`, `Linux - C21Y XNU 8796 build and DTS`, step 17 `Build native XNU kernel` |
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

## 3. Fix applied locally (not yet pushed)

| File | Change |
| --- | --- |
| `patches/xnu/8796-unifdef-headers.patch` | New patch. Adds a message to bare `#error`; collapses two multi-line `#endif` comments to single lines. |
| `patches/xnu/series` | Adds the patch before `sdhci-block-personality.patch`, with the evidence note. |
| `PROJECT_STATE.md`, `docs/RESEARCH_LOG.md`, `docs/BUILD_HISTORY.md`, `docs/HARDWARE_EVIDENCE.md`, `docs/NEXT_SESSION.md` | New checkpoint records. |

Why this fix: it is the smallest change that removes the exact constructs unifdef 2.10 misparses, it matches a proven upstream device-port fix, and its blob hashes prove it applies to the exact pinned XNU source. No guessed address, register, memory map, config value or toolchain assumption is introduced.

Local verification performed:
- `unifdef 2.10` on unpatched `OSEndianTypes.h`: exit `2`.
- `unifdef 2.10` on patched `OSEndianTypes.h`: exit `0`.
- `unifdef 2.10` on unpatched `pfvar.h`: exit `2`, `Premature EOF (#if line 63 depth 1)`.
- `unifdef 2.10` on patched `pfvar.h`: exit `1` (normal "some changes made" status for unifdef).
- `unifdef 2.12` on unpatched `OSEndianTypes.h`: exit `0`.
- Git blob pre/post hashes match the Nuwa patch post-images exactly.

## 4. Claim boundaries

| Claim | Status |
| --- | --- |
| Host reproduction of the parser failure | **Done** |
| Minimal source fix identified and locally verified | **Done** |
| Fix committed and pushed to GitHub | **Not done** — no `git`, `gh`, or token in the current environment |
| GitHub Actions XNU kernel compile success | **Not yet** — requires push and a new run |
| Non-empty `kernel.macho` artifact verified | **Not yet** |
| Boot success on Realme C21Y | **Not claimed** |
| Full hardware support | **Not claimed**; only the evidence in `docs/HARDWARE_EVIDENCE.md` is established |
| Device writes / flashing / reboot | **None** in this session |

## 5. Immediate next action

Push the local changes, then let CI produce Build #125. Success requires the `Linux - C21Y XNU 8796 build and DTS` job to finish with `conclusion: success` and a non-empty `kernel.macho` artifact whose SHA-256 and Mach-O header are verified. Details and commands are in `docs/NEXT_SESSION.md`.

## 6. Checkpoint commands

- `STATUS` — print this state without changing files.
- `SAVE` — refresh these checkpoint files after a new measurement.
- `CHECKPOINT` — write the current state and record the evidence IDs.
- `CONTINUE` — resume from the unresolved build step.
- `HANDOFF` — prepare the exact next-session packet from `docs/NEXT_SESSION.md`.
