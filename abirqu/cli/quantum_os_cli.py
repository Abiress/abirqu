"""
Quantum OS CLI
==============
Command-line interface for the Quantum OS.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import List, Optional

from ..quantum_os import (
    QuantumJob, QuantumScheduler, SchedulingPolicy,
    JobQueue, ResourceManager, VirtualQPU, CostEstimator,
)
from ..quantum_os.tenant import TenantManager, TenantTier
from ..quantum_os.access import AccessController, Role
from ..quantum_os.monitor import JobMonitor
from ..quantum_os.reservation import ReservationSystem


def cmd_status(args):
    """Show quantum OS status."""
    rm = ResourceManager()
    pool_status = rm.get_pool_status()

    print("Quantum OS Status")
    print("=" * 50)
    for name, info in pool_status.items():
        available = info["available"]
        total = info["max_concurrent"]
        bar = "█" * (total - available) + "░" * available
        print(f"  {name:15s} [{bar}] {total - available}/{total} active")
        print(f"    Backends: {', '.join(info['backends'])}")
        print(f"    Cost/shot: ${info['credits_per_shot']:.4f}")
    print()

    scheduler = QuantumScheduler(policy=SchedulingPolicy.PRIORITY)
    print(f"  Queue depth: {scheduler.queue_depth}")
    print(f"  Running jobs: {scheduler.running_count}")


def cmd_backends(args):
    """List available backends."""
    rm = ResourceManager()
    backends = rm.list_backends()

    print(f"{'Backend':25s} {'Pool':12s} {'Available':10s} {'Cost/Shot':10s}")
    print("-" * 60)
    for b in backends:
        avail = "Yes" if b["available"] else "No"
        print(f"{b['backend']:25s} {b['pool']:12s} {avail:10s} ${b['credits_per_shot']:.4f}")


def cmd_jobs(args):
    """List jobs."""
    queue = JobQueue()
    jobs = queue.list_jobs(status_filter=args.status)

    if not jobs:
        print("No jobs found.")
        return

    print(f"{'Job ID':14s} {'Backend':20s} {'State':12s} {'Shots':8s} {'Priority':8s}")
    print("-" * 65)
    for j in jobs:
        print(f"{j['job_id']:14s} {j['backend']:20s} {j['state']:12s} {j['shots']:8d} {j['priority']:8d}")


def cmd_cost(args):
    """Estimate cost."""
    from ..circuit import Circuit
    from ..gates import H, CNOT

    c = Circuit(args.qubits)
    for i in range(args.qubits - 1):
        c.h(i)
        c.cnot(i, i + 1)

    estimator = CostEstimator()
    est = estimator.estimate(c, args.backend, shots=args.shots)

    print(f"Cost Estimate for {args.backend}")
    print(f"  Circuit: {args.qubits} qubits, Bell state")
    print(f"  Shots: {est['shots']}")
    print(f"  Cost/shot: ${est['cost_per_shot']:.4f}")
    print(f"  Total cost: ${est['total_cost']:.4f}")
    print(f"  Est. time: {est['estimated_time_us']:.1f} μs")


def cmd_tenants(args):
    """List tenants."""
    tm = TenantManager()
    tenants = tm.list_tenants()

    print(f"{'ID':10s} {'Name':20s} {'Tier':12s} {'Environments':12s} {'Enabled':8s}")
    print("-" * 65)
    for t in tenants:
        env_count = len(t["environments"])
        print(f"{t['tenant_id']:10s} {t['name']:20s} {t['tier']:12s} {env_count:12d} {'Yes' if t['enabled'] else 'No':8s}")


def cmd_monitor(args):
    """Monitor jobs."""
    monitor = JobMonitor()
    print("Monitoring... (press Ctrl+C to stop)")
    try:
        while True:
            summary = monitor.get_summary()
            print(f"\r  Tracked: {summary['total_tracked']} | Snapshots: {summary['total_snapshots']}", end="", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped monitoring.")


def cmd_reservations(args):
    """List reservations."""
    rs = ReservationSystem()
    print("No reservations found." if True else "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantum-os",
        description="AbirQu Quantum OS command-line interface",
    )
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Show quantum OS status")

    # backends
    sub.add_parser("backends", help="List available backends")

    # jobs
    jobs_p = sub.add_parser("jobs", help="List jobs")
    jobs_p.add_argument("--status", help="Filter by status")

    # cost
    cost_p = sub.add_parser("cost", help="Estimate cost")
    cost_p.add_argument("--qubits", type=int, default=5, help="Number of qubits")
    cost_p.add_argument("--backend", default="fast", help="Backend name")
    cost_p.add_argument("--shots", type=int, default=1024, help="Number of shots")

    # tenants
    sub.add_parser("tenants", help="List tenants")

    # monitor
    mon_p = sub.add_parser("monitor", help="Monitor jobs")
    mon_p.add_argument("--interval", type=float, default=1.0, help="Poll interval (seconds)")

    # reservations
    sub.add_parser("reservations", help="List reservations")

    return parser


def main(argv: Optional[List[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "status": cmd_status,
        "backends": cmd_backends,
        "jobs": cmd_jobs,
        "cost": cmd_cost,
        "tenants": cmd_tenants,
        "monitor": cmd_monitor,
        "reservations": cmd_reservations,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()
    return 0
