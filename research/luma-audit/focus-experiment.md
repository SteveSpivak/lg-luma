# Default-OFF native focus-depth candidate

**Status: PROPOSED / UNAPPLIED. Native execution BLOCKED.** Artifact: `../../delivery/patches/focus-depth.patch`, generated deterministically from base `e5608cd053be5376a54a806129a332952dfabcef` by `../scripts/make_candidate.py`.

## Bounded behavior

Only `LUMA_FOCUS_DEPTH=1` enables a deeper focused-card shadow: blur 34→42, vertical offset 14→20, alpha 0.4→0.5. Unfocused shadows remain 22/9/0.165. Unset, empty, `0`, `true`, `01`, whitespace and other values stay off. The flag is read once, is not serialized and adds no Settings preference/migration.

The card face, caption, ring, control rectangle, navigation, press behavior and texture/text caches are unchanged. There is no new animation, so reduced motion does not need a new moving fallback; the depth change is instantaneous like the existing focus state. This is a depth experiment, not a claim to reproduce Apple's implementation.

The patch touches only `src/main.rs` (module registration), `src/view.rs` (existing shadow parameters) and new `src/focus_experiment.rs` (pure policy + native tests). It does not touch Home, platform, helper, boot hooks, firmware, DNS, services or TV configuration.

## Geometry/damage rationale

A 256×154.4 face retains its 281.6 pitch and 25.6 nominal gap. Existing focused shadow bounds are 326×224.4; candidate bounds are 342×240.4, about 1.124× the shadow bounding-box area. This is arithmetic, not measured GPU cost. The added horizontal extent is 8 logical pixels per side, less than the nominal gap; vertical extent grows downward by 14 and upward by 3. Existing `damage::bounds` includes blur, so old/new shadows can be redrawn without changing hit geometry. Text damage may still dominate a focus frame because caption weight changes.

## Validation receipts and stop rule

- Intentional pre-generation static red test: exit **1** because the patch did not exist.
- First `git apply --check`: exit **1**, `error: dev/null: No such file or directory`; generated new-file diff lacked its Git mode header.
- The combined research suite exposed the same apply failure again: 17 passed, 1 failed. **Stopped repeated apply validation after two failures.**
- Generator now emits `new file mode 100644`; corrected artifact passed the bounded/default-off static contract (exit **0**). Its apply check was **NOT_RUN after correction**, and the earlier failure remains in receipts. Do not describe the corrected patch as apply-verified.
- Independent offline evidence/arithmetic suite: **16 passed**, exit **0**. This does not compile Rust.
- Native tests in the patch: `opt_in_requires_exact_one_and_defaults_off`, `disabled_matches_existing_focus_and_press_shadow_parameters`, `enabled_only_changes_focused_shadow`, `enlarged_damage_contains_the_old_shadow_and_card_face` — **NOT_RUN**.

Next gate: inspect the corrected patch, then explicitly resume its apply/reverse-apply validation and run Rust/SDL tests when the toolchain exists. Do not hide the earlier failure or claim a native PASS.

## Future desktop-only use after validation/applicability review

Apply the patch on the dedicated Arena branch, build with the documented toolchain, then compare unset versus `LUMA_FOCUS_DEPTH=1` using isolated preferences and identical scripts. Do not use `pnpm deploy`, package/install or TV commands. Suggested existing diagnostics: `--profile-frames`, `--diagnostics`, `LUMA_DAMAGE_VERIFY=1` in a correctness run (not a performance run), and `LUMA_PARTIAL=0` as full-redraw control. Actual commands and acceptance remain gated by restored tooling.

Rollback: do not apply it (current state), or unset the environment for a running validated experiment; reverse the patch to remove source changes. No preference migration or TV rollback is involved.
