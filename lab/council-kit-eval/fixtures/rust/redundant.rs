// Labeled fixture: redundant booleans and Rust-specific && look-alikes.
pub fn real_redundant_and(a: bool) -> bool {
    a && a
}
pub fn real_redundant_or(a: bool) -> bool {
    a || a
}
pub fn fine_and(a: bool, b: bool) -> bool {
    a && b
}
pub fn double_ref_type(v: &&str) -> &str {
    let &&inner = v;
    inner
}
