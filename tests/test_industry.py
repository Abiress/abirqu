import json
from abirqu.industry import (
    DerivativePricingQAE, 
    PortfolioOptimizationQAOA, 
    VehicleRoutingAnnealer, 
    AirlineCrewScheduling, 
    HubbardModelSimulation, 
    BatteryDegradationAnalysis
)

print("--- Testing Phase 30: Industry-Specific Workloads ---\n")

# ---------------------------------------------------------
# Test 30.1: Quantitative Finance
# ---------------------------------------------------------
print("Test 30.1a: Derivative Pricing (QAE)")
qae = DerivativePricingQAE(spot_price=100.0, strike_price=105.0, volatility=0.2, risk_free_rate=0.05, maturity=1.0)
call_price = qae.price_european_call(num_evaluation_qubits=8)
print(f"European Call Price: {json.dumps(call_price, indent=2)}")

print("\nTest 30.1b: Portfolio Optimization (QAOA)")
qaoa = PortfolioOptimizationQAOA(
    expected_returns=[0.1, 0.2, 0.15], 
    covariance_matrix=[[0.05, 0.01, 0.02], [0.01, 0.08, 0.03], [0.02, 0.03, 0.06]],
    risk_aversion=0.5
)
portfolio = qaoa.solve()
print(f"Optimal Portfolio: {json.dumps(portfolio, indent=2)}")
print("-" * 60)

# ---------------------------------------------------------
# Test 30.2: Logistics & Supply Chain
# ---------------------------------------------------------
print("\nTest 30.2a: Vehicle Routing Problem (Quantum Annealing)")
vrp = VehicleRoutingAnnealer(
    num_vehicles=2,
    distances=[
        [0.0, 2.0, 3.0, 4.0],
        [2.0, 0.0, 1.5, 2.5],
        [3.0, 1.5, 0.0, 2.0],
        [4.0, 2.5, 2.0, 0.0]
    ]
)
routing = vrp.solve()
print(f"Routing Solution: {json.dumps(routing, indent=2)}")

print("\nTest 30.2b: Airline Crew Scheduling")
crew = AirlineCrewScheduling(
    flights=["FL101", "FL102", "FL103"],
    crew_rosters=[["FL101", "FL102"], ["FL103"], ["FL101", "FL103"]],
    roster_costs=[1500.0, 800.0, 1600.0]
)
schedule = crew.solve()
print(f"Crew Schedule: {json.dumps(schedule, indent=2)}")
print("-" * 60)

# ---------------------------------------------------------
# Test 30.3: Materials Science
# ---------------------------------------------------------
print("\nTest 30.3a: Hubbard Model Simulation")
hubbard = HubbardModelSimulation(sites=4, u=4.0, t=1.0)
energy = hubbard.ground_state_energy()
print(f"Hubbard Ground State: {json.dumps(energy, indent=2)}")

print("\nTest 30.3b: Battery Degradation Analysis")
battery = BatteryDegradationAnalysis(molecules=["Li2CO3", "LiF", "LEDC"])
degradation = battery.simulate_degradation_pathway()
print(f"Degradation Analysis: {json.dumps(degradation, indent=2)}")
print("-" * 60)

print("\nPhase 30 Industry Workloads Tests Completed Successfully!")
