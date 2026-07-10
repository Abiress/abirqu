use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

/// Manages the Python backend subprocess.
pub struct PythonBridge {
    child: Mutex<Option<Child>>,
}

impl PythonBridge {
    pub fn new() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }

    /// Start the Python backend server and consume the "ready" event.
    pub fn start(&self) -> Result<(), String> {
        let mut child_lock = self.child.lock().map_err(|e| e.to_string())?;
        if child_lock.is_some() {
            return Ok(());
        }

        let python = if cfg!(target_os = "windows") {
            "python"
        } else {
            "python3"
        };

        let mut child = Command::new(python)
            .args(["-m", "abirqu.gui.server_headless", "--stdio"])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start Python backend: {}", e))?;

        // Consume the "ready" event Python sends on startup
        {
            let stdout = child.stdout.as_mut().ok_or("Failed to open stdout for ready event")?;
            let mut reader = BufReader::new(stdout);
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
                    // Got something else — store it? For now just log
                    eprintln!("Unexpected first line from Python: {}", val);
                }
                Err(e) => {
                    eprintln!("Failed to parse ready event '{}': {}", line.trim(), e);
                }
            }
        }

        *child_lock = Some(child);
        Ok(())
    }

    /// Stop the Python backend server.
    pub fn stop(&self) -> Result<(), String> {
        let mut child_lock = self.child.lock().map_err(|e| e.to_string())?;
        if let Some(mut child) = child_lock.take() {
            child.kill().map_err(|e| e.to_string())?;
        }
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

        // Read response (skip any non-response lines)
        let stdout = child.stdout.as_mut().ok_or("Failed to open stdout")?;
        let mut reader = BufReader::new(stdout);

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
    pub fn is_running(&self) -> bool {
        self.child
            .lock()
            .map(|lock| lock.is_some())
            .unwrap_or(false)
    }
}
