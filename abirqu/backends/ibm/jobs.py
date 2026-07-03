"""
IBM Quantum Job Manager
=======================
Manage IBM Quantum jobs: submit, poll, cancel, retrieve.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from ...backend import JobStatus


class IBMJobManager:
    """Manage IBM Quantum job lifecycle.

    Parameters
    ----------
    token : str, optional
        IBM Quantum API token.
    instance : str
        Hub/group/project.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        instance: str = "ibm-q/open/main",
    ):
        self.token = token or os.getenv("IBM_QUANTUM_TOKEN", os.getenv("QISKIT_IBM_TOKEN", ""))
        self.instance = instance
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            QiskitRuntimeService.save_account(
                channel="ibm_quantum",
                token=self.token,
                instance=self.instance,
                overwrite=True,
            )
            self._service = QiskitRuntimeService(
                channel="ibm_quantum",
                instance=self.instance,
            )
            return self._service
        except ImportError as exc:
            raise RuntimeError("qiskit-ibm-runtime required.") from exc

    def submit(
        self,
        qiskit_circuit,
        backend_name: str,
        shots: int = 1024,
    ) -> str:
        """Submit a Qiskit circuit and return job_id."""
        from qiskit import transpile
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        service = self._get_service()
        backend = service.backend(backend_name)
        tqc = transpile(qiskit_circuit, backend)
        sampler = Sampler(mode=backend)
        job = sampler.run([tqc], shots=shots)
        return job.job_id()

    def status(self, job_id: str) -> JobStatus:
        """Query job status."""
        try:
            service = self._get_service()
            job = service.job(job_id)
            status = str(job.status())
            status_map = {
                "QUEUED": JobStatus.QUEUED,
                "RUNNING": JobStatus.RUNNING,
                "DONE": JobStatus.COMPLETED,
                "ERROR": JobStatus.FAILED,
                "CANCELLED": JobStatus.CANCELED,
                "CANCELED": JobStatus.CANCELED,
            }
            return status_map.get(status, JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def result(self, job_id: str) -> Dict[str, Any]:
        """Fetch job result."""
        service = self._get_service()
        job = service.job(job_id)
        pub_result = job.result()[0]
        raw_counts = pub_result.data.meas.get_counts()
        total = sum(raw_counts.values())
        probs = {k: v / total for k, v in raw_counts.items()}
        return {
            "success": True,
            "job_id": job_id,
            "shots": total,
            "counts": dict(raw_counts),
            "probabilities": probs,
        }

    def cancel(self, job_id: str) -> bool:
        """Cancel a running job."""
        try:
            service = self._get_service()
            job = service.job(job_id)
            job.cancel()
            return True
        except Exception:
            return False

    def list_jobs(
        self,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List recent jobs."""
        service = self._get_service()
        # This is a simplified version — real API may differ
        return []

    def wait_for_completion(
        self,
        job_id: str,
        timeout: float = 600.0,
        poll_interval: float = 2.0,
    ) -> JobStatus:
        """Wait for a job to complete."""
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            status = self.status(job_id)
            if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED):
                return status
            time.sleep(poll_interval)
        return JobStatus.UNKNOWN
