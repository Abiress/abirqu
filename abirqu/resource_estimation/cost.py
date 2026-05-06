"""
Task 11.4 — Cost Estimation Engine

Per-backend cost estimation, comparison, budget optimization, and tracking.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class ProviderType(Enum):
    """Quantum cloud providers."""
    IBM = "ibm"
    AWS_BRACKET = "aws_braket"
    GOOGLE = "google"
    AZURE = "azure"
    IONQ = "ionq"
    RIGETTI = "rigetti"
    QUERA = "quera"


@dataclass
class ProviderPricing:
    """Pricing structure for a quantum cloud provider."""
    provider: ProviderType
    name: str
    
    # Pricing model
    price_per_shot: float = 0.0  # Per circuit execution
    price_per_minute: float = 0.0  # Per minute of queue/execution time
    price_per_credit: float = 1.0  # Per credit (IBM)
    credits_per_shot: int = 1
    
    # Subscription/setup
    monthly_fee: float = 0.0
    free_shots_monthly: int = 0
    
    # Hardware-specific
    hardware_rates: Dict[str, float] = field(default_factory=dict)  # Per hardware name
    
    def estimate_cost(self, shots: int, hardware: Optional[str] = None,
                     estimated_time_min: float = 1.0) -> float:
        """
        Estimate cost for a job.
        
        Args:
            shots: Number of circuit shots
            hardware: Hardware name (uses hardware_rates if available)
            estimated_time_min: Estimated execution time in minutes
            
        Returns:
            Estimated cost in USD
        """
        cost = 0.0
        
        # Shot-based pricing
        if hardware and hardware in self.hardware_rates:
            cost += shots * self.hardware_rates[hardware]
        else:
            cost += shots * self.price_per_shot
        
        # Time-based pricing
        cost += estimated_time_min * self.price_per_minute
        
        # Credit-based (IBM)
        if self.credits_per_shot > 0:
            credits = shots * self.credits_per_shot
            cost += credits * self.price_per_credit
        
        # Subtract free shots
        effective_shots = max(0, shots - self.free_shots_monthly)
        if shots > self.free_shots_monthly:
            cost = (effective_shots / shots) * cost
        
        return cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider.value,
            'name': self.name,
            'price_per_shot': self.price_per_shot,
            'price_per_minute': self.price_per_minute,
            'monthly_fee': self.monthly_fee,
            'free_shots_monthly': self.free_shots_monthly,
            'hardware_rates': self.hardware_rates,
        }


@dataclass
class CostEstimate:
    """Cost estimate result."""
    provider: str
    hardware: str
    shots: int
    estimated_cost_usd: float
    estimated_time_min: float
    cost_per_shot: float
    breakdown: Dict[str, float]  # Detailed cost breakdown
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'hardware': self.hardware,
            'shots': self.shots,
            'estimated_cost_usd': self.estimated_cost_usd,
            'estimated_time_min': self.estimated_time_min,
            'cost_per_shot': self.cost_per_shot,
            'breakdown': self.breakdown,
        }


class CostEstimationEngine:
    """
    Engine for estimating quantum computing costs across providers.
    
    Features:
    - Per-backend cost estimation
    - Cost comparison across providers
    - Budget-constrained optimization
    - Historical cost tracking
    """
    
    # Default pricing (simplified, may not reflect actual current pricing)
    DEFAULT_PRICING = {
        ProviderType.IBM: ProviderPricing(
            provider=ProviderType.IBM,
            name="IBM Quantum",
            price_per_credit=0.01,  # $0.01 per credit
            credits_per_shot=3,  # ~3 credits per shot on 127-qubit
            free_shots_monthly=100,
            hardware_rates={
                'Brisbane': 0.03,
                'Kyoto': 0.05,
                'Condor': 0.15,
            }
        ),
        ProviderType.AWS_BRACKET: ProviderPricing(
            provider=ProviderType.AWS_BRACKET,
            name="AWS Braket",
            price_per_shot=0.05,  # $0.05 per shot (simulated)
            price_per_minute=0.15,  # $0.15 per minute queue time
            hardware_rates={
                'IonQ': 0.30,  # $0.30 per shot on IonQ
                'Rigetti': 0.10,
                'QuEra': 0.25,
            }
        ),
        ProviderType.GOOGLE: ProviderPricing(
            provider=ProviderType.GOOGLE,
            name="Google Quantum AI",
            price_per_shot=0.04,
            monthly_fee=100.0,  # C1 access fee
        ),
        ProviderType.IONQ: ProviderPricing(
            provider=ProviderType.IONQ,
            name="IonQ",
            price_per_shot=0.30,  # Forte
            hardware_rates={
                'Forte': 0.30,
                'Aria': 0.50,
            }
        ),
    }
    
    def __init__(self, pricing: Optional[Dict[ProviderType, ProviderPricing]] = None):
        """
        Initialize cost estimation engine.
        
        Args:
            pricing: Custom pricing dict (uses DEFAULT_PRICING if None)
        """
        self.pricing = pricing or self.DEFAULT_PRICING
        self.cost_history: List[CostEstimate] = []
    
    def estimate_cost(self, provider: ProviderType, hardware: str,
                     shots: int, estimated_time_min: float = 1.0) -> CostEstimate:
        """
        Estimate cost for a specific provider/hardware.
        
        Args:
            provider: Provider type
            hardware: Hardware name
            shots: Number of shots
            estimated_time_min: Estimated execution time
            
        Returns:
            CostEstimate with detailed breakdown
        """
        if provider not in self.pricing:
            raise ValueError(f"Unknown provider: {provider}")
        
        pricing = self.pricing[provider]
        cost = pricing.estimate_cost(shots, hardware, estimated_time_min)
        
        # Detailed breakdown
        breakdown = {
            'shot_cost': shots * pricing.price_per_shot if pricing.price_per_shot > 0 else shots * pricing.credits_per_shot * pricing.price_per_credit,
            'time_cost': estimated_time_min * pricing.price_per_minute,
            'monthly_fee_amortized': pricing.monthly_fee / 30.0,  # Amortize over month
        }
        
        estimate = CostEstimate(
            provider=pricing.name,
            hardware=hardware,
            shots=shots,
            estimated_cost_usd=cost,
            estimated_time_min=estimated_time_min,
            cost_per_shot=cost / max(shots, 1),
            breakdown=breakdown,
        )
        
        # Track history
        self.cost_history.append(estimate)
        
        return estimate
    
    def compare_providers(self, hardware_shots: List[Tuple[ProviderType, str, int]],
                          estimated_time_min: float = 1.0) -> List[CostEstimate]:
        """
        Compare costs across multiple providers for the same circuit.
        
        Args:
            hardware_shots: List of (provider, hardware, shots) tuples
            estimated_time_min: Estimated execution time
            
        Returns:
            List of CostEstimates, sorted by cost (ascending)
        """
        estimates = []
        for provider, hardware, shots in hardware_shots:
            try:
                estimate = self.estimate_cost(provider, hardware, shots, estimated_time_min)
                estimates.append(estimate)
            except ValueError as e:
                print(f"Warning: {e}")
        
        # Sort by cost
        estimates.sort(key=lambda x: x.estimated_cost_usd)
        return estimates
    
    def optimize_for_budget(self, budget: float,
                            options: List[Tuple[ProviderType, str, int]],
                            estimated_time_min: float = 1.0) -> Optional[CostEstimate]:
        """
        Find best option within a budget constraint.
        
        Args:
            budget: Maximum budget in USD
            options: List of (provider, hardware, shots) to consider
            estimated_time_min: Estimated execution time
            
        Returns:
            CostEstimate for best option within budget, or None
        """
        valid_options = []
        for provider, hardware, shots in options:
            try:
                estimate = self.estimate_cost(provider, hardware, shots, estimated_time_min)
                if estimate.estimated_cost_usd <= budget:
                    valid_options.append(estimate)
            except ValueError:
                pass
        
        if not valid_options:
            return None
        
        # Return option with highest shots (most data) within budget
        valid_options.sort(key=lambda x: x.shots, reverse=True)
        return valid_options[0]
    
    def track_historical_costs(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze historical cost data.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with historical analysis
        """
        if not self.cost_history:
            return {'message': 'No cost history available'}
        
        costs = [e.estimated_cost_usd for e in self.cost_history]
        shots = [e.shots for e in self.cost_history]
        
        return {
            'total_jobs': len(self.cost_history),
            'total_cost_usd': sum(costs),
            'average_cost_per_job': np.mean(costs),
            'average_shots_per_job': np.mean(shots),
            'cost_trend': 'increasing' if len(costs) > 1 and costs[-1] > costs[0] else 'decreasing',
            'most_expensive_provider': max(set(e.provider for e in self.cost_history), 
                                          key=lambda p: sum(e.estimated_cost_usd for e in self.cost_history if e.provider == p)),
        }
    
    def project_monthly_cost(self, daily_shots: int,
                             provider: ProviderType, hardware: str) -> Dict[str, float]:
        """
        Project monthly cost based on daily usage.
        
        Args:
            daily_shots: Average shots per day
            provider: Provider type
            hardware: Hardware name
            
        Returns:
            Dict with monthly cost projections
        """
        daily_cost = self.estimate_cost(provider, hardware, daily_shots)
        monthly_shots = daily_shots * 30
        monthly_cost = daily_cost.estimated_cost_usd * 30
        
        return {
            'daily_shots': daily_shots,
            'monthly_shots': monthly_shots,
            'daily_cost_usd': daily_cost.estimated_cost_usd,
            'monthly_cost_usd': monthly_cost,
            'yearly_cost_usd': monthly_cost * 12,
        }
