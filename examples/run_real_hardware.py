#!/usr/bin/env python3
"""Run a Bell circuit on real quantum hardware (or local fallback).

Usage examples:
  PYTHONPATH=. python3 examples/run_real_hardware.py --provider local
  PYTHONPATH=. python3 examples/run_real_hardware.py --provider ibm
  PYTHONPATH=. python3 examples/run_real_hardware.py --provider aws

Environment variables (provider-specific):
  IBM:   IBM_QUANTUM_TOKEN
  AWS:   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (+ S3 settings if needed)
  Azure: AZURE_QUANTUM_RESOURCE_ID
  IonQ:  IONQ_API_KEY
  Google: GOOGLE_CLOUD_PROJECT (plus cirq-google credentials)
"""

import argparse
import json

from abirqu.circuit import Circuit
from abirqu.phases import HardwareExecutionManager


def bell() -> Circuit:
    c = Circuit(2, name="bell_real_hardware")
    c.h(0)
    c.cnot(0, 1)
    return c


def main() -> int:
    parser = argparse.ArgumentParser(description="AbirQu real hardware runner")
    parser.add_argument("--provider", default="local", choices=["local", "ibm", "aws", "azure", "ionq", "google"])
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--dry-run", action="store_true", help="Force local execution while validating provider route")
    args = parser.parse_args()

    mgr = HardwareExecutionManager()

    try:
        result = mgr.run(
            bell(),
            provider=args.provider,
            shots=args.shots,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(json.dumps({"success": False, "provider": args.provider, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({
        "success": result.get("success", False),
        "provider": result.get("provider", args.provider),
        "backend": result.get("backend"),
        "shots": result.get("shots"),
        "counts": result.get("counts", {}),
        "dry_run": result.get("dry_run", False),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
