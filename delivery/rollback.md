# Rollback and non-mutation proof

## Current delivery

- Native/application paths are unchanged from base `e5608cd053be5376a54a806129a332952dfabcef`; see `../research/audit/source-protection.json` and `receipts/protected-source-diff.json`.
- No TV was contacted, no package installed, no Home hook/boot identity changed, no firmware/DNS/media-protection/system service/TV configuration touched.
- The focus candidate exists only as `patches/focus-depth.patch`; it is **not applied**. There is no runtime feature flag active on any device and no persistent preference to migrate or roll back.
- Research/delivery files are additive on the dedicated Arena branch. They do not alter the native build graph.

## Immediate rollback if desired

Do not apply the patch. To discard the proposed experiment only, remove `delivery/patches/focus-depth.patch` and its generator/report references; keep the audit. To discard all audit delivery work, revert the dedicated delivery commit(s) on the Arena branch, never the base or handoff branch. No TV action is required because none occurred.

## Future validated desktop experiment

Only after apply/reverse checks and native tests pass:

1. Unset `LUMA_FOCUS_DEPTH` (or set any value other than exact `1`) and restart the experimental process. Baseline shadow parameters are selected by the pure policy.
2. Reverse the patch on the same branch with `git apply --reverse delivery/patches/focus-depth.patch` after confirming the working tree matches the candidate.
3. Re-run default-off scene equality, focus/damage/pointer/Back regressions and source-protection diff.
4. No preferences file migration is involved. Do not delete user preferences to simulate rollback.

## Future TV canary rollback (not authorized now)

Use only the owner-approved isolated canary procedure: stop the experimental process, unset its environment, restore isolated test preferences if used, and verify the predeclared known-good package/Home route. Do not run reference recovery scripts automatically or mutate system services. If Home/LAN/recovery is uncertain, stop before deployment rather than improvising recovery.

Apply/reverse validation of the corrected patch was stopped after two repeated failures and remains OPEN (`BLOCKERS.json:B05`). Therefore no claim is made that reverse application has been proven.
