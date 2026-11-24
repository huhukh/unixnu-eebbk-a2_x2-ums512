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
