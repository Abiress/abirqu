use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdout, Command, Stdio};
use std::sync::Mutex;

/// Manages the Python backend subprocess.
pub struct PythonBridge {
    child: Mutex<Option<Child>>,
    stdout: Mutex<Option<BufReader<ChildStdout>>>,
    /// Absolute path of the bundled interpreter, set at app startup when the
    /// self-contained Python runtime shipped as a Tauri resource exists.
    python_path: Mutex<Option<PathBuf>>,
}

impl PythonBridge {
    pub fn new() -> Self {
        Self {
            child: Mutex::new(None),
            stdout: Mutex::new(None),
            python_path: Mutex::new(None),
        }
    }

    /// Remember the bundled interpreter discovered at startup.
    pub fn set_python_path(&self, path: PathBuf) {
        if let Ok(mut p) = self.python_path.lock() {
            *p = Some(path);
        }
    }

    /// Interpreter to launch: the bundled runtime if present, else the
    /// system Python (PATH lookup).
    fn resolve_python(&self) -> String {
        if let Ok(p) = self.python_path.lock() {
            if let Some(path) = p.as_ref() {
                return path.to_string_lossy().into_owned();
            }
        }
        if cfg!(target_os = "windows") {
            "python".to_string()
        } else {
            "python3".to_string()
        }
    }

    /// Start the Python backend server and consume the "ready" event.
    pub fn start(&self) -> Result<(), String> {
        let mut child_lock = self.child.lock().map_err(|e| e.to_string())?;
        if child_lock.is_some() {
            return Ok(());
        }

        let mut child = Command::new(self.resolve_python())
            .args(["-m", "abirqu.gui.server_headless", "--stdio"])
            // Keep the subprocess isolated from any user/ambient site-packages
            // so the bundled runtime stays fully self-contained.
            .env_remove("PYTHONPATH")
            .env_remove("PYTHONHOME")
            .env("PYTHONNOUSERSITE", "1")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start Python backend: {}", e))?;

        // Take ownership of stdout and wrap in a persistent BufReader
        let child_stdout = child.stdout.take().ok_or("Failed to open stdout")?;
        let mut reader = BufReader::new(child_stdout);

        // Consume the "ready" event Python sends on startup
        let mut line = String::new();
        reader
            .read_line(&mut line)
            .map_err(|e| format!("Failed to read ready event: {}", e))?;

        let parsed: Result<Value, _> = serde_json::from_str(line.trim());
        match parsed {
            Ok(val) if val.get("event").and_then(|v| v.as_str()) == Some("ready") => {
                // Ready event consumed, good
            }
            Ok(val) => {
                eprintln!("Unexpected first line from Python: {}", val);
            }
            Err(e) => {
                eprintln!("Failed to parse ready event '{}': {}", line.trim(), e);
            }
        }

        // Store the persistent BufReader and child
        let mut stdout_lock = self.stdout.lock().map_err(|e| e.to_string())?;
        *stdout_lock = Some(reader);
        *child_lock = Some(child);
        Ok(())
    }

    /// Stop the Python backend server.
    pub fn stop(&self) -> Result<(), String> {
        let mut child_lock = self.child.lock().map_err(|e| e.to_string())?;
        if let Some(mut child) = child_lock.take() {
            child.kill().map_err(|e| e.to_string())?;
        }
        // Clear the stdout reader
        let mut stdout_lock = self.stdout.lock().map_err(|e| e.to_string())?;
        *stdout_lock = None;
        Ok(())
    }

    /// Send a request to Python and get the response.
    pub fn request(&self, request: &Value) -> Result<Value, String> {
        let mut child_lock = self.child.lock().map_err(|e| e.to_string())?;
        let child = child_lock.as_mut().ok_or("Python backend not running")?;

        // Write request
        {
            let stdin = child.stdin.as_mut().ok_or("Failed to open stdin")?;
            let request_str = serde_json::to_string(request).map_err(|e| e.to_string())?;
            writeln!(stdin, "{}", request_str).map_err(|e| e.to_string())?;
            stdin.flush().map_err(|e| e.to_string())?;
        }

        // Drop child lock before reading from stdout (avoids deadlock)
        drop(child_lock);

        // Read response from persistent BufReader
        let mut stdout_lock = self.stdout.lock().map_err(|e| e.to_string())?;
        let reader = stdout_lock
            .as_mut()
            .ok_or("Python backend stdout not available")?;

        loop {
            let mut line = String::new();
            reader
                .read_line(&mut line)
                .map_err(|e| format!("Failed to read response: {}", e))?;

            if line.trim().is_empty() {
                continue;
            }

            let parsed: Value = serde_json::from_str(line.trim())
                .map_err(|e| format!("Invalid JSON response '{}': {}", line.trim(), e))?;

            // Skip event messages, return status responses
            if parsed.get("event").is_some() {
                continue;
            }

            return Ok(parsed);
        }
    }

    /// Check if the backend is running.
    #[allow(dead_code)]
    pub fn is_running(&self) -> bool {
        self.child
            .lock()
            .map(|lock| lock.is_some())
            .unwrap_or(false)
    }
}
