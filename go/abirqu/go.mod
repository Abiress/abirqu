module github.com/abirqu/abirqu

go 1.21

// This module requires libabirqu_core.so to be built first:
//   cd ../.. && cargo build --release --no-default-features
//   export LD_LIBRARY_PATH=$PWD/target/release:$LD_LIBRARY_PATH
