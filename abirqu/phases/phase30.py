from typing import Any, Dict, List, Sequence

import numpy as np

from ..industry import (
    AirlineCrewScheduling,
    BatteryDegradationAnalysis,
    DerivativePricingQAE,
    HubbardModelSimulation,
    PortfolioOptimizationQAOA,
    VehicleRoutingAnnealer,
)


class IndustryWorkloadSuite:
    def finance(self) -> Dict[str, Any]:
        price = DerivativePricingQAE().price_european_call()
        portfolio = PortfolioOptimizationQAOA().solve()
        return {"derivatives": price, "portfolio": portfolio}

    def logistics(self) -> Dict[str, Any]:
        vrp = VehicleRoutingAnnealer().solve()
        crew = AirlineCrewScheduling().solve()
        return {"vehicle_routing": vrp, "crew_scheduling": crew}

    def science(self) -> Dict[str, Any]:
        hubbard = HubbardModelSimulation().ground_state_energy()
        battery = BatteryDegradationAnalysis().simulate_degradation_pathway()
        return {"hubbard": hubbard, "battery": battery}


class PortfolioRiskEngine:
    def risk(self, weights: Sequence[float], covariance: np.ndarray) -> float:
        w = np.asarray(weights, dtype=float)
        cov = np.asarray(covariance, dtype=float)
        return float(np.sqrt(w.T @ cov @ w))


class RoutingCostModel:
    def total_distance(self, routes: Sequence[Sequence[int]], distance_matrix: np.ndarray) -> float:
        d = np.asarray(distance_matrix, dtype=float)
        total = 0.0
        for r in routes:
            for i in range(len(r) - 1):
                total += d[int(r[i]), int(r[i + 1])]
        return float(total)
