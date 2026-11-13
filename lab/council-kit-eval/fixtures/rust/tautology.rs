// Labeled fixture: tautological comparisons and legitimate look-alikes.
pub fn simple_tautology(a: u32) -> bool {
    a == a
}
pub fn nested_tautology(a: u32, b: u32) -> bool {
    a == b && b == b
}
pub fn NOTATAUT(a: u32, b: u32) -> bool {
    a == b
}
pub fn inequality_is_fine(a: u32, b: u32) -> bool {
    a != b
}
pub fn string_containing_marker() -> &'static str {
    "a == a is printed, not evaluated"
}
// a == a appears in this comment only
pub fn multiline_tautology(alpha: u32) -> bool {
    alpha
        == alpha
}
pub fn method_chain(a: Vec<u32>) -> bool {
    a.len() == a.len()
}
