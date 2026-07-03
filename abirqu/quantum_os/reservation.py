"""
Reservation System
==================
Reserve QPU time slots in advance.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ReservationState(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"
    EXPIRED = "expired"


@dataclass
class Reservation:
    """A QPU time reservation."""
    reservation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    backend_name: str = ""
    tenant_id: str = "default"
    start_time: float = 0.0
    end_time: float = 0.0
    state: ReservationState = ReservationState.PENDING
    max_shots: int = 10000
    shots_used: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def shots_remaining(self) -> int:
        return max(0, self.max_shots - self.shots_used)

    @property
    def is_active(self) -> bool:
        now = time.time()
        return (
            self.state == ReservationState.CONFIRMED
            and self.start_time <= now <= self.end_time
        )

    def to_dict(self) -> Dict:
        return {
            "reservation_id": self.reservation_id,
            "backend": self.backend_name,
            "tenant": self.tenant_id,
            "start": self.start_time,
            "end": self.end_time,
            "state": self.state.value,
            "max_shots": self.max_shots,
            "shots_used": self.shots_used,
            "shots_remaining": self.shots_remaining,
        }


class ReservationSystem:
    """Manage QPU time reservations.

    Parameters
    ----------
    max_advance_days : int
        How far in advance reservations can be made.
    min_reservation_minutes : int
        Minimum reservation duration in minutes.
    """

    def __init__(
        self,
        max_advance_days: int = 30,
        min_reservation_minutes: int = 5,
    ):
        self.max_advance_days = max_advance_days
        self.min_reservation_minutes = min_reservation_minutes
        self._reservations: Dict[str, Reservation] = {}
        self._backend_reservations: Dict[str, List[str]] = {}

    def reserve(
        self,
        backend_name: str,
        start_time: float,
        end_time: float,
        tenant_id: str = "default",
        max_shots: int = 10000,
        **metadata,
    ) -> Reservation:
        """Create a reservation."""
        if end_time <= start_time:
            raise ValueError("end_time must be after start_time")

        duration_min = (end_time - start_time) / 60.0
        if duration_min < self.min_reservation_minutes:
            raise ValueError(f"Minimum reservation is {self.min_reservation_minutes} minutes")

        max_advance = self.max_advance_days * 86400
        if start_time - time.time() > max_advance:
            raise ValueError(f"Cannot reserve more than {self.max_advance_days} days ahead")

        # Check for conflicts
        if self._has_conflict(backend_name, start_time, end_time):
            raise ValueError(f"Time slot already reserved for {backend_name}")

        reservation = Reservation(
            backend_name=backend_name,
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            max_shots=max_shots,
            state=ReservationState.CONFIRMED,
            metadata=metadata,
        )

        self._reservations[reservation.reservation_id] = reservation
        self._backend_reservations.setdefault(backend_name, []).append(reservation.reservation_id)
        return reservation

    def cancel(self, reservation_id: str) -> bool:
        """Cancel a reservation."""
        res = self._reservations.get(reservation_id)
        if res and res.state in (ReservationState.PENDING, ReservationState.CONFIRMED):
            res.state = ReservationState.CANCELED
            return True
        return False

    def get_reservation(self, reservation_id: str) -> Optional[Reservation]:
        return self._reservations.get(reservation_id)

    def get_backend_reservations(
        self,
        backend_name: str,
        start: Optional[float] = None,
        end: Optional[float] = None,
    ) -> List[Reservation]:
        """Get reservations for a backend in a time range."""
        ids = self._backend_reservations.get(backend_name, [])
        reservations = [self._reservations[rid] for rid in ids if rid in self._reservations]
        if start is not None:
            reservations = [r for r in reservations if r.end_time > start]
        if end is not None:
            reservations = [r for r in reservations if r.start_time < end]
        return sorted(reservations, key=lambda r: r.start_time)

    def get_available_slots(
        self,
        backend_name: str,
        date_start: float,
        date_end: float,
        slot_minutes: int = 60,
    ) -> List[Dict]:
        """Find available time slots."""
        reserved = self.get_backend_reservations(backend_name, date_start, date_end)
        reserved_intervals = [(r.start_time, r.end_time) for r in reserved]
        reserved_intervals.sort()

        slots = []
        current = date_start
        slot_sec = slot_minutes * 60

        for rs, re in reserved_intervals:
            while current + slot_sec <= rs:
                slots.append({"start": current, "end": current + slot_sec})
                current += slot_sec
            current = max(current, re)

        while current + slot_sec <= date_end:
            slots.append({"start": current, "end": current + slot_sec})
            current += slot_sec

        return slots

    def _has_conflict(self, backend_name: str, start: float, end: float) -> bool:
        for r in self.get_backend_reservations(backend_name, start, end):
            if r.state in (ReservationState.CONFIRMED, ReservationState.ACTIVE):
                if r.start_time < end and r.end_time > start:
                    return True
        return False

    def cleanup_expired(self) -> int:
        """Mark expired reservations. Returns count cleaned."""
        now = time.time()
        count = 0
        for res in self._reservations.values():
            if res.state == ReservationState.CONFIRMED and res.end_time < now:
                res.state = ReservationState.EXPIRED
                count += 1
        return count
