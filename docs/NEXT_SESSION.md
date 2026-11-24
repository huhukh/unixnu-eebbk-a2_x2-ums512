# NEXT_SESSION — exact continuation packet

## 0. Start here

Read in this order:

1. `PROJECT_STATE.md`
2. `docs/RESEARCH_LOG.md` R5–R12
3. `docs/BUILD_HISTORY.md`
4. `docs/HARDWARE_EVIDENCE.md`
5. `patches/xnu/8796-unifdef-headers.patch` and `patches/xnu/series`

Do not repeat the BCM2837 hypothesis or the completed unifdef investigation. The root cause is established; the next work is push + CI verification.

## 1. Current local delta

Files changed/created in the local branch snapshot:

- `patches/xnu/8796-unifdef-headers.patch` — new, full blob hashes verified against pinned XNU `c54f35ca...`.
- `patches/xnu/series` — patch added before `sdhci-block-personality.patch`.
- `PROJECT_STATE.md` — new.
- `docs/RESEARCH_LOG.md` — new.
- `docs/BUILD_HISTORY.md` — new.
- `docs/HARDWARE_EVIDENCE.md` — new.
- `docs/NEXT_SESSION.md` — new (this file).

No workflow, defconfig, board, DTS, ADT, memory-map or EDK2 file was changed.

## 2. Environment blocker

The current shell has **no `git` executable, no `gh` executable and no `GH_TOKEN`/`GITHUB_TOKEN`**. Therefore the local delta has not been committed, pushed, or used to trigger a workflow. Unauthenticated log and artifact APIs are also unavailable (`401`/`403`).

To proceed, one of the following must be available:

- a Git installation plus a GitHub credential with write access to `huhukh/unixnu-eebbk-a2_x2-ums512`; or
- a `GH_TOKEN`/`GITHUB_TOKEN` with `repo` scope; or
- an authenticated browser session used to commit the files through the GitHub web UI.

Do not ask the user to re-explain the investigation. Ask only for write access/token if it is genuinely absent.

## 3. Commit and push (when Git/token exists)

From the device repository snapshot:

```sh
git status --short
git diff -- patches/xnu/series
git diff --no-index /dev/null patches/xnu/8796-unifdef-headers.patch || true

git add patches/xnu/8796-unifdef-headers.patch \
        patches/xnu/series \
        PROJECT_STATE.md \
        docs/RESEARCH_LOG.md \
        docs/BUILD_HISTORY.md \
        docs/HARDWARE_EVIDENCE.md \
        docs/NEXT_SESSION.md

git commit -m "xnu: fix installhdrs unifdef 2.10 parse failure"
git push origin port/realme-c21y-rmx3261
```

Record the new commit SHA. It must become the head SHA of the next Actions run.

If using the REST API instead of `git`, create a blob/tree/commit/update-ref via the authenticated GitHub API and verify the branch HEAD afterwards. Do not fabricate a SHA.

## 4. Trigger and verify the new run

The push itself triggers `.github/workflows/build.yml` (the workflow listens to `push` on this branch). If a manual trigger is needed:

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/workflows/421430805/dispatches \
  -d '{"ref":"port/realme-c21y-rmx3261"}'
```

Then poll only the public/authorized API for the new run:

```sh
curl -sS https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs?branch=port%2Frealme-c21y-rmx3261\&per_page=3
curl -sS https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/<NEW_RUN_ID>/jobs
curl -sS https://api.github.com/repos/huhukh/unixnu-eebbk-a2_x2-ums512/actions/runs/<NEW_RUN_ID>/artifacts
```

Verify all of:

1. new run head SHA equals the push commit;
2. job `Linux - C21Y XNU 8796 build and DTS` has `conclusion: success`;
3. artifact `realme-c21y-build-check` exists;
4. artifact contains a non-empty `out/**/kernel/kernel.macho`;
5. record the file size and SHA-256;
6. record a Mach-O/ARM64 header check (for example `file`, `otool -h`, or a Python Mach-O header parse), not merely existence.

Only after those checks may the state be updated to "compiled ARM64 kernel achieved". The EDK2 scaffold job succeeding is not sufficient.

## 5. If the next run fails

1. Get the new failing step and job ID from the jobs API.
2. Download the artifact/logs with authentication if available.
3. Root-cause the new failure from the actual command and source.
4. Add a new `Rxx` entry to `docs/RESEARCH_LOG.md` and a new row to `docs/BUILD_HISTORY.md`.
5. Apply only a minimal, evidence-backed change. Do not guess addresses or configs.

Likely next classes of failure, based only on existing audit notes and not assumed to occur: other XNU patch-context mismatches (`native-aes-personality.patch`, `ios-sweet-0011-physmap-alignment.patch`), archive/compile-record differences, or link-time undefined symbols. Treat them as hypotheses only until logs prove them.

## 6. Checkpoint workflow

Use these commands in the session when a milestone is reached:

- `STATUS` — report the current state without editing.
- `SAVE` — refresh `PROJECT_STATE.md` and evidence logs.
- `CHECKPOINT` — write a durable packet with exact SHAs, run IDs and artifact hashes.
- `CONTINUE` — resume from the first unverified gate.
- `HANDOFF` — emit this file plus the current delta for another session.

## 7. Hard restrictions

- No flashing, rebooting, partition writes or device commands without explicit approval.
- Do not treat the iPhone10,3/D22AP identity as real C21Y hardware identity.
- Do not treat the EDK2 `.fd` scaffold as flashable firmware.
- Do not fill memory maps with estimates.
- Do not claim boot or hardware support from a compile artifact.
