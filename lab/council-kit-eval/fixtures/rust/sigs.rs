// Labeled fixture: signature extraction.
pub fn plain(a: u32, b: u32) -> u32 { a + b }
pub fn snake_case_params(content_target: &str, app_id: &str) -> bool { true }
pub fn mixed(first: u32, second_arg: u32, third: u32) -> u32 { 0 }
pub async fn async_fn(a: u32) -> u32 { a }
pub fn with_self(&self, other: u32) -> u32 { other }
