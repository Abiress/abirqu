#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod python;

use python::PythonBridge;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(PythonBridge::new())
        .invoke_handler(tauri::generate_handler![
            commands::compile_circuit,
            commands::execute_circuit,
            commands::get_job_status,
            commands::get_results,
            commands::cancel_job,
            commands::list_jobs,
            commands::list_hardware,
            commands::list_library_circuits,
            commands::load_circuit_from_library,
            commands::save_circuit_to_library,
            commands::get_server_stats,
            commands::start_server,
            commands::stop_server,
            commands::convert_circuit,
            commands::run_qiskit,
            commands::run_cirq,
            commands::run_oqtopus,
            commands::run_dwave,
            commands::export_circuit,
            commands::get_frameworks,
            commands::run_qec,
            commands::run_qkd,
            commands::run_chemistry,
            commands::run_shor,
            commands::run_grover,
            commands::run_hhl,
            commands::run_qpinn,
            commands::run_crypto,
            commands::run_agentic,
            commands::ask_quantum,
            commands::run_chemistry_vqe,
            commands::run_qec_cycle,
            commands::run_qec_distill,
            commands::run_qcomm_bb84,
            commands::run_pqc_keygen,
            commands::run_pqc_assess,
            commands::run_osint_graph,
            commands::run_qcomm_cvqkd,
            commands::run_qcomm_diqkd,
            commands::run_qcomm_satellite,
            commands::run_qcomm_repeater,
            commands::run_qcomm_network,
            commands::run_circuit_encrypt,
            commands::run_circuit_decrypt,
            commands::run_plugin_list,
            commands::run_ttn,
            commands::run_autodiff,
            commands::run_dd,
            commands::run_distributed,
            commands::job_queue_status,
        ])
        .run(tauri::generate_context!())
        .expect("error while running AbirQu");
}
