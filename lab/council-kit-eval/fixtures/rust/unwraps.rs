// Labeled fixture: unwrap / expect safety.
pub fn guarded_unwrap(v: Option<u32>) -> u32 {
    if v.is_some() {
        return v.unwrap();
    }
    0
}
pub fn guarded_if_let(v: Option<u32>) -> u32 {
    if let Some(x) = v {
        return x;
    }
    0
}
pub fn unguarded_unwrap(v: Option<u32>) -> u32 {
    v.unwrap()
}
pub fn unguarded_result(r: Result<u32, String>) -> u32 {
    r.unwrap()
}
pub fn uses_expect(r: Result<u32, String>) -> u32 {
    r.expect("boom")
}
pub fn uses_unwrap_or(v: Option<u32>) -> u32 {
    v.unwrap_or(0)
}
pub fn uses_unwrap_or_else(v: Option<u32>) -> u32 {
    v.unwrap_or_else(|| 0)
}
#[test]
fn test_idiomatic_unwrap() {
    let v: Option<u32> = Some(1);
    assert_eq!(v.unwrap(), 1);
}
// this comment mentions .unwrap() but is not code
pub fn doc_mentions_unwrap() {}
