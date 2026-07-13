use crate::python::PythonBridge;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct CircuitData {
    pub num_qubits: u32,
    pub gates: Vec<GateData>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GateData {
    pub name: String,
    pub qubits: Vec<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub params: Option<Vec<f64>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct JobInfo {
    pub job_id: String,
    pub status: String,
    pub backend: String,
    pub shots: u32,
    pub result: Option<Value>,
    pub progress: f64,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HardwareInfo {
    pub name: String,
    pub backend_type: String,
    pub num_qubits: u32,
    pub provider: String,
    pub status: String,
    pub gates: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CircuitTemplate {
    pub template_id: String,
    pub name: String,
    pub description: String,
    pub category: String,
    pub num_qubits: u32,
    pub depth: u32,
    pub gates: Vec<GateData>,
    pub tags: Vec<String>,
    pub difficulty: String,
}

fn send_request(bridge: &PythonBridge, action: &str, extra: Value) -> Result<Value, String> {
    let mut request = json!({ "action": action });
    if let Some(obj) = extra.as_object() {
        if let Some(req) = request.as_object_mut() {
            for (k, v) in obj {
                req.insert(k.clone(), v.clone());
            }
        }
    }
    bridge.request(&request)
}

fn parse_job(data: &Value) -> JobInfo {
    JobInfo {
        job_id: data["job_id"].as_str().unwrap_or("").to_string(),
        status: data["status"].as_str().unwrap_or("pending").to_string(),
        backend: data["backend"].as_str().unwrap_or("").to_string(),
        shots: data["shots"].as_u64().unwrap_or(1024) as u32,
        result: data.get("result").cloned(),
        progress: data["progress"].as_f64().unwrap_or(0.0),
        error: data["error"].as_str().map(|s| s.to_string()),
    }
}

fn parse_hardware(data: &Value) -> HardwareInfo {
    HardwareInfo {
        name: data["name"].as_str().unwrap_or("").to_string(),
        backend_type: data["type"].as_str().unwrap_or("simulator").to_string(),
        num_qubits: data["num_qubits"].as_u64().unwrap_or(0) as u32,
        provider: data["provider"].as_str().unwrap_or("").to_string(),
        status: data["status"].as_str().unwrap_or("online").to_string(),
        gates: data["gates"]
            .as_array()
            .map(|a| a.iter().map(|g| g.as_str().unwrap_or("").to_string()).collect())
            .unwrap_or_default(),
    }
}

fn parse_template(data: &Value) -> CircuitTemplate {
    CircuitTemplate {
        template_id: data["template_id"].as_str().unwrap_or("").to_string(),
        name: data["name"].as_str().unwrap_or("").to_string(),
        description: data["description"].as_str().unwrap_or("").to_string(),
        category: data["category"].as_str().unwrap_or("").to_string(),
        num_qubits: data["num_qubits"].as_u64().unwrap_or(0) as u32,
        depth: data["depth"].as_u64().unwrap_or(0) as u32,
        gates: data["gates"]
            .as_array()
            .map(|a| a.iter().map(|g| GateData {
                name: g["name"].as_str().unwrap_or("").to_string(),
                qubits: g["qubits"].as_array()
                    .map(|a| a.iter().map(|q| q.as_u64().unwrap_or(0) as u32).collect())
                    .unwrap_or_default(),
                params: g["params"].as_array()
                    .map(|a| a.iter().map(|p| p.as_f64().unwrap_or(0.0)).collect()),
            }).collect())
            .unwrap_or_default(),
        tags: data["tags"].as_array()
            .map(|a| a.iter().map(|t| t.as_str().unwrap_or("").to_string()).collect())
            .unwrap_or_default(),
        difficulty: data["difficulty"].as_str().unwrap_or("beginner").to_string(),
    }
}

// ─── Commands ────────────────────────────────────────────────

#[tauri::command]
pub async fn start_server(bridge: State<'_, PythonBridge>) -> Result<String, String> {
    bridge.start().map(|_| "started".to_string())
}

#[tauri::command]
pub async fn stop_server(bridge: State<'_, PythonBridge>) -> Result<String, String> {
    bridge.stop().map(|_| "stopped".to_string())
}

#[tauri::command]
pub async fn compile_circuit(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    backend: Option<String>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "compile", json!({
        "circuit": circuit,
        "backend": backend.unwrap_or_else(|| "abirqu_simulator".to_string()),
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn execute_circuit(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    backend: Option<String>,
    shots: Option<u32>,
) -> Result<JobInfo, String> {
    let resp = send_request(&bridge, "execute", json!({
        "circuit": circuit,
        "backend": backend.unwrap_or_else(|| "abirqu_simulator".to_string()),
        "shots": shots.unwrap_or(1024),
    }))?;
    let data = extract_data(resp)?;
    Ok(parse_job(&data))
}

#[tauri::command]
pub async fn get_job_status(
    bridge: State<'_, PythonBridge>,
    job_id: String,
) -> Result<JobInfo, String> {
    let resp = send_request(&bridge, "status", json!({ "job_id": job_id }))?;
    let data = extract_data(resp)?;
    Ok(parse_job(&data))
}

#[tauri::command]
pub async fn get_results(
    bridge: State<'_, PythonBridge>,
    job_id: String,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "result", json!({ "job_id": job_id }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn cancel_job(
    bridge: State<'_, PythonBridge>,
    job_id: String,
) -> Result<String, String> {
    let resp = send_request(&bridge, "cancel", json!({ "job_id": job_id }))?;
    extract_data(resp).map(|_| "cancelled".to_string())
}

#[tauri::command]
pub async fn list_jobs(
    bridge: State<'_, PythonBridge>,
) -> Result<Vec<JobInfo>, String> {
    let resp = send_request(&bridge, "list_jobs", json!({}))?;
    let data = extract_data(resp)?;
    Ok(data["jobs"].as_array()
        .map(|a| a.iter().map(parse_job).collect())
        .unwrap_or_default())
}

#[tauri::command]
pub async fn list_hardware(
    bridge: State<'_, PythonBridge>,
) -> Result<Vec<HardwareInfo>, String> {
    let resp = send_request(&bridge, "hardware", json!({}))?;
    let data = extract_data(resp)?;
    Ok(data["hardware"].as_array()
        .map(|a| a.iter().map(parse_hardware).collect())
        .unwrap_or_default())
}

#[tauri::command]
pub async fn list_library_circuits(
    bridge: State<'_, PythonBridge>,
) -> Result<Vec<CircuitTemplate>, String> {
    let resp = send_request(&bridge, "library", json!({}))?;
    let data = extract_data(resp)?;
    let mut templates = Vec::new();
    if let Some(arr) = data["builtin"].as_array() {
        for t in arr {
            templates.push(parse_template(t));
        }
    }
    Ok(templates)
}

#[tauri::command]
pub async fn load_circuit_from_library(
    bridge: State<'_, PythonBridge>,
    template_id: String,
) -> Result<CircuitData, String> {
    let resp = send_request(&bridge, "get_template", json!({ "template_id": template_id }))?;
    let data = extract_data(resp)?;
    Ok(CircuitData {
        num_qubits: data["num_qubits"].as_u64().unwrap_or(2) as u32,
        gates: data["gates"].as_array()
            .map(|a| a.iter().map(|g| GateData {
                name: g["name"].as_str().unwrap_or("").to_string(),
                qubits: g["qubits"].as_array()
                    .map(|a| a.iter().map(|q| q.as_u64().unwrap_or(0) as u32).collect())
                    .unwrap_or_default(),
                params: g["params"].as_array()
                    .map(|a| a.iter().map(|p| p.as_f64().unwrap_or(0.0)).collect()),
            }).collect())
            .unwrap_or_default(),
    })
}

#[tauri::command]
pub async fn save_circuit_to_library(
    bridge: State<'_, PythonBridge>,
    template: CircuitTemplate,
) -> Result<String, String> {
    let resp = send_request(&bridge, "save_template", json!({ "template": template }))?;
    extract_data(resp).map(|_| "saved".to_string())
}

#[tauri::command]
pub async fn get_server_stats(
    bridge: State<'_, PythonBridge>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "stats", json!({}))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn convert_circuit(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    target: String,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "convert", json!({
        "circuit": circuit,
        "target": target,
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qiskit(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    shots: Option<u32>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_qiskit", json!({
        "circuit": circuit,
        "shots": shots.unwrap_or(1024),
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_cirq(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    shots: Option<u32>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_cirq", json!({
        "circuit": circuit,
        "shots": shots.unwrap_or(1024),
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_oqtopus(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    shots: Option<u32>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_oqtopus", json!({
        "circuit": circuit,
        "shots": shots.unwrap_or(1024),
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_dwave(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    shots: Option<u32>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_dwave", json!({
        "circuit": circuit,
        "shots": shots.unwrap_or(1024),
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn export_circuit(
    bridge: State<'_, PythonBridge>,
    circuit: CircuitData,
    format: String,
    results: Option<Value>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "export", json!({
        "circuit": circuit,
        "format": format,
        "results": results.unwrap_or(json!({})),
    }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn get_frameworks(
    bridge: State<'_, PythonBridge>,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "frameworks", json!({}))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qec(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_qec", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qkd(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_qkd", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_chemistry(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_chemistry", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_shor(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_shor", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_grover(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_grover", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_hhl(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_hhl", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qpinn(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_qpinn", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_crypto(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_crypto", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_agentic(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_agentic", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn ask_quantum(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "ask_quantum", json!({ "params": params }))?;
    extract_data(resp)
}

// ─── Domain module commands (Chemistry / QEC / Quantum Comm / PQC) ────────
// Each wraps a real abirqu_gui.domain_handlers function via the same
// action-dispatch JSON protocol as every other command above — see
// abirqu/gui/domain_handlers.py for the actual SDK calls being made.

#[tauri::command]
pub async fn run_chemistry_vqe(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "chemistry_vqe", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qec_cycle(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qec_cycle", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qec_distill(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qec_distill", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qcomm_bb84(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qcomm_bb84", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_pqc_keygen(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "pqc_keygen", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_pqc_assess(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "pqc_assess", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_osint_graph(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "osint_graph", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qcomm_cvqkd(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qcomm_cvqkd", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qcomm_diqkd(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qcomm_diqkd", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qcomm_satellite(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qcomm_satellite", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qcomm_repeater(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qcomm_repeater", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_qcomm_network(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "qcomm_network", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_circuit_encrypt(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "circuit_encrypt", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_circuit_decrypt(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "circuit_decrypt", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_plugin_list(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "plugin_list", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_ttn(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_ttn", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_autodiff(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_autodiff", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_dd(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_dd", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn run_distributed(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "run_distributed", json!({ "params": params }))?;
    extract_data(resp)
}

#[tauri::command]
pub async fn job_queue_status(
    bridge: State<'_, PythonBridge>,
    params: Value,
) -> Result<Value, String> {
    let resp = send_request(&bridge, "job_queue_status", json!({ "params": params }))?;
    extract_data(resp)
}

fn extract_data(resp: Value) -> Result<Value, String> {
    if resp["status"] == "ok" {
        Ok(resp["data"].clone())
    } else {
        Err(resp["error"].as_str().unwrap_or("Unknown error").to_string())
    }
}
