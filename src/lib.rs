mod simulator;

use pyo3::prelude::*;
use simulator::Simulator;

/// High-performance Rust backend module for AbirQu
#[pymodule]
fn abirqu_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Simulator>()?;
    Ok(())
}
