fn main() {
	// Keep a tiny CLI entrypoint so cargo can build the binary target.
	println!("abirqu-core {}", env!("CARGO_PKG_VERSION"));
}
