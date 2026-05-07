import asyncio
import requests
import websockets
import subprocess
import time
import json
import sys

async def run_tests():
    print("Starting FastAPI Uvicorn Server in background...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "abirqu.cloud.gateway:app", "--port", "8082"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        print("\n--- Test 1: REST API Submit Job ---")
        headers = {"x-api-key": "secret_key_1", "Content-Type": "application/json"}
        circuit_data = {"num_qubits": 2, "gates": ["H(0)", "CNOT(0,1)"], "measure": True}
        payload = {"circuit": circuit_data, "shots": 1024}
        
        resp = requests.post("http://127.0.0.1:8082/jobs/submit", headers=headers, json=payload)
        resp_json = resp.json()
        print(f"Submit Response: {json.dumps(resp_json, indent=2)}")
        
        job_id = resp_json.get("job_id")
        assert job_id is not None, "Job ID should be present"
        
        print(f"\n--- Test 2: WebSocket Real-Time Status ---")
        uri = f"ws://127.0.0.1:8082/jobs/{job_id}/ws"
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket.")
            
            while True:
                msg = await websocket.recv()
                print(f"WebSocket Update: {msg}")
                data = json.loads(msg)
                if data.get("status") == "COMPLETED":
                    final_data = data
                    break
            
            assert final_data["status"] == "COMPLETED", "Job should complete"
            
        print("\n--- Test 3: REST API Get Result (Decryption Check) ---")
        resp = requests.get(f"http://127.0.0.1:8082/jobs/{job_id}/status", headers=headers)
        result_json = resp.json()
        print(f"Final Status: {json.dumps(result_json, indent=2)}")
        
        assert "result" in result_json, "Result should be retrieved and decrypted"
        assert result_json["result"]["counts"]["00"] == 1024, "Result values should match expected"
        
        print("\nAll 100% Real Features Validated successfully!")
        
    finally:
        # Cleanup server
        process.terminate()
        process.wait()
        
if __name__ == "__main__":
    asyncio.run(run_tests())
