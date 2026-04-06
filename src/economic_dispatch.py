import pypsa
import pandas as pd

# Generation data
GENERATION_COSTS = {"A": 7.5, "B": 6, "C": 14, "D": 10}  # €/MWh
GENERATION_CAPACITY = {"A": 140, "B": 285, "C": 90, "D": 85}  # MW
GENERATOR_BUS_MAPPING = {"A": "1", "B": "1", "C": "2", "D": "3"}  # Generator locations

# Transmission data
TRANSMISSION_REACTANCE = {"LINE_1_2": 0.2, "LINE_1_3": 0.2, "LINE_2_3": 0.1}  # pu
TRANSMISSION_CAPACITY_BASE = {"LINE_1_2": 126, "LINE_1_3": 250, "LINE_2_3": 130}  # MVA

# Demand data
BUS_DEMAND = {"1": 50, "2": 60, "3": 300}  # MW


def build_network():
    """Build network without transmission constraints (Economic Dispatch problem)."""
    n = pypsa.Network()
    
    # Add buses and loads
    for bus in BUS_DEMAND:
        n.add("Bus", bus)
        n.add("Load", f"Load_Bus_{bus}", bus=bus, p_set=BUS_DEMAND[bus])
    
    # Add generators
    for gen, capacity in GENERATION_CAPACITY.items():
        n.add(
            "Generator",
            f"Gen_{gen}",
            bus=GENERATOR_BUS_MAPPING[gen],
            p_nom=capacity,
            marginal_cost=GENERATION_COSTS[gen]
        )
    
    # Add transmission lines (unconstrained - large capacity)
    n.add("Line", "LINE_1_2", bus0="1", bus1="2", r=0.0001, x=0.2, s_nom=500)
    n.add("Line", "LINE_1_3", bus0="1", bus1="3", r=0.0001, x=0.2, s_nom=500)
    n.add("Line", "LINE_2_3", bus0="2", bus1="3", r=0.0001, x=0.1, s_nom=500)
    
    return n


def optimize_unconstrained_dispatch():
    """Optimize network without transmission constraints."""
    n = build_network()
    n.optimize(include_objective_constant=False)
    return n


def optimize_constrained_dispatch(transmission_limits):
    """Optimize network with transmission constraints."""
    n = build_network()
    # Update transmission line capacities based on input limits
    for line_name, limit in transmission_limits.items():
        n.lines.loc[line_name, "s_nom"] = limit
    n.optimize(include_objective_constant=False)
    return n

