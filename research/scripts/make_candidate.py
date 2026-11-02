#!/usr/bin/env python3
"""Generate an UNAPPLIED default-off native focus-depth patch from the pinned base.

This does not compile or execute Rust. Native validation remains a separate gate.
"""
from pathlib import Path
import difflib
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = "e5608cd053be5376a54a806129a332952dfabcef"


def source(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT, text=True)


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Pinned source context changed; refuse candidate generation")
    return text.replace(old, new, 1)


def main():
    main_rs = source("src/main.rs")
    view_rs = source("src/view.rs")
    main_new = replace_once(main_rs, "mod font;\n", "mod focus_experiment;\nmod font;\n")
    old = '''    out.shadow(
        rect,
        19.2,
        if focused { 34. } else { 22. },
        if focused { 14. } else { 9. },
        if focused { 0.4 } else { 0.165 },
    );'''
    new = '''    let shadow = crate::focus_experiment::card_shadow(
        crate::focus_experiment::enabled(),
        focused,
    );
    out.shadow(rect, 19.2, shadow.blur, shadow.offset_y, shadow.alpha);'''
    view_new = replace_once(view_rs, old, new)
    module = '''//! Default-OFF focus-depth experiment. Presentation only: no layout, input,
//! persistent preference, texture, timer or platform lifecycle changes.
use std::sync::OnceLock;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CardShadow {
    pub blur: f32,
    pub offset_y: f32,
    pub alpha: f32,
}

pub fn from_environment(value: Option<&str>) -> bool {
    value == Some("1")
}

pub fn enabled() -> bool {
    static ENABLED: OnceLock<bool> = OnceLock::new();
    *ENABLED.get_or_init(|| from_environment(std::env::var("LUMA_FOCUS_DEPTH").ok().as_deref()))
}

pub fn card_shadow(experiment: bool, focused: bool) -> CardShadow {
    if experiment && focused {
        CardShadow { blur: 42., offset_y: 20., alpha: 0.5 }
    } else if focused {
        CardShadow { blur: 34., offset_y: 14., alpha: 0.4 }
    } else {
        CardShadow { blur: 22., offset_y: 9., alpha: 0.165 }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{damage, renderer::Draw, state::Rect};

    #[test]
    fn opt_in_requires_exact_one_and_defaults_off() {
        assert!(!from_environment(None));
        assert!(from_environment(Some("1")));
        for value in ["", "0", "true", "yes", "01", "1 ", "2"] {
            assert!(!from_environment(Some(value)), "{value:?}");
        }
    }

    #[test]
    fn disabled_matches_existing_focus_and_press_shadow_parameters() {
        assert_eq!(card_shadow(false, true), CardShadow { blur: 34., offset_y: 14., alpha: 0.4 });
        assert_eq!(card_shadow(false, false), CardShadow { blur: 22., offset_y: 9., alpha: 0.165 });
    }

    #[test]
    /// Only focused shadow depth changes; unfocused cards stay byte-equivalent.
    fn enabled_only_changes_focused_shadow() {
        assert_eq!(card_shadow(true, false), card_shadow(false, false));
        assert_ne!(card_shadow(true, true), card_shadow(false, true));
    }

    #[test]
    fn enlarged_damage_contains_the_old_shadow_and_card_face() {
        let face = Rect::new(84., 544.8, 256., 154.4);
        let shadow = |experiment| {
            let s = card_shadow(experiment, true);
            Draw::Shadow(Rect::new(face.x, face.y + s.offset_y, face.w, face.h), 19.2, s.blur, [0., 0., 0., s.alpha])
        };
        let old = damage::bounds(&shadow(false)).unwrap();
        let new = damage::bounds(&shadow(true)).unwrap();
        for contained in [old, face] {
            assert!(new.x <= contained.x && new.y <= contained.y);
            assert!(new.x + new.w >= contained.x + contained.w);
            assert!(new.y + new.h >= contained.y + contained.h);
        }
    }
}
'''
    chunks = []
    for path, before, after in (("src/main.rs",main_rs,main_new),("src/view.rs",view_rs,view_new),("src/focus_experiment.rs","",module)):
        diff = difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                    fromfile="a/"+path if before else "/dev/null",
                                    tofile="b/"+path, n=3)
        mode_header = "new file mode 100644\n" if not before else ""
        chunks.append(f"diff --git a/{path} b/{path}\n" + mode_header + "".join(diff))
    out = ROOT / "delivery/patches/focus-depth.patch"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(chunks))
    print(out)

if __name__ == "__main__":
    main()
