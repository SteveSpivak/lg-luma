# Default-OFF native focus-depth candidate

**Status: GIT-INTEGRITY VERIFIED / UNAPPLIED / NATIVE BLOCKED.** Artifact: `../../delivery/patches/focus-depth.patch`, generated deterministically from base `e5608cd053be5376a54a806129a332952dfabcef`. SHA-256 `8230cce60f85db4965f0731e702216dbb5fe7442ee0a33ba4768f9dc0b24a257`.

## Bounded behavior

Only exact `LUMA_FOCUS_DEPTH=1` enables a deeper focused-card shadow: blur 34→42, vertical offset 14→20, alpha 0.4→0.5. Unfocused shadows remain 22/9/0.165. Unset/empty/`0`/`true`/`01`/whitespace/other values stay off. The flag is read once, is not serialized and adds no Settings preference/migration.

Card face, caption, ring, control rectangle, navigation, press behavior and texture/text caches are unchanged. No new animation or timer. The patch touches only `src/main.rs`, `src/view.rs` and new `src/focus_experiment.rs`; no Home/platform/helper/boot/TV configuration changes.

## Integrity gate (completed)

See `../../delivery/PATCH-INTEGRITY.md` and `../audit/patch-integrity.json`. In a temporary directory outside every Git worktree, populated from the pinned base `src/` tree:

- forward check/apply: exit **0/0**; exactly the three allowed paths changed;
- reverse check/apply: exit **0/0**; every source byte restored;
- reverse-on-baseline, double-apply and stale-context negative controls: exit **1/1/1**, as expected;
- application `src/` remained byte-identical throughout.

Historical failures remain recorded: the original malformed new-file diff lacked `new file mode 100644` and produced `error: dev/null: No such file or directory`; exact malformed bytes were not retained. Two follow-up harness failures (tar directory member; ignored `.build` scratch no-op) were diagnosed and fixed before the final isolated PASS. No native compilation or behavior was tested.

## Native tests supplied but NOT_RUN

`opt_in_requires_exact_one_and_defaults_off`, `disabled_matches_existing_focus_and_press_shadow_parameters`, `enabled_only_changes_focused_shadow`, `enlarged_damage_contains_the_old_shadow_and_card_face`.

Next gate: restore the manual reference environment, run original baselines unchanged, then these Rust tests plus existing focus/damage/pointer/Back regressions. Compare unset versus exact `LUMA_FOCUS_DEPTH=1` on desktop with isolated preferences and identical assets/scripts. Acceptance: default scene unchanged, only focused shadow changes, controls/hit rects unchanged, old/new shadow damage covered, no new cache/timer/persistent setting. Physical TV remains separately approval-gated and NOT_RUN.

Rollback: do not apply it (current state), or unset the environment for a running validated experiment; reverse the patch to remove source changes. Reverse application is now proven at Git/source level. No preference migration or TV rollback is involved.
