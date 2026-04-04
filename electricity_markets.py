import numpy as np
import pypsa


# Marginal generation costs in EUR/MWh
GENERATION_COSTS = {"Wind": 0, "Hydro": 0, "Coal": 30, "Gas": 60, "Oil": 80}

# Generation capacity by country and technology (MW)
GENERATION_CAPACITY = {
    "South Africa": {"Coal": 35000, "Wind": 3000, "Gas": 8000, "Oil": 2000},
    "Mozambique": {"Hydro": 1200},
    "Eswatini": {"Hydro": 600},
}

# Transmission capacities between countries (MW)
TRANSMISSION_CAPACITY = {
    "South Africa": {"Mozambique": 500, "Eswatini": 250},
    "Mozambique": {"Eswatini": 100},
}

# Electrical demand by country (MW)
DEMAND = {"South Africa": 42000, "Mozambique": 650, "Eswatini": 250}


def add_components(n, countries):
    """Add buses, generators, loads, and transmission links to network."""
    countries = [countries] if isinstance(countries, str) else countries
    for country in countries:
        n.add("Bus", country, carrier="AC")
        for tech in GENERATION_CAPACITY[country]:
            n.add(
                "Generator",
                f"{country}-{tech}",
                bus=country,
                p_nom=GENERATION_CAPACITY[country][tech],
                marginal_cost=GENERATION_COSTS.get(tech)
            )
        n.add("Load", f"{country}-load", bus=country, p_set=DEMAND.get(country))

        if len(countries) > 1:
            if country not in TRANSMISSION_CAPACITY:
                continue
            for neighbor in countries:
                if neighbor not in TRANSMISSION_CAPACITY[country]:
                    continue
                capacity = TRANSMISSION_CAPACITY[country][neighbor]
                n.add("Link", f"{country}-{neighbor} link", bus0=country,
                      bus1=neighbor, p_nom=capacity, p_min_pu=-1)


def simulate_single_zone():
    """Simulate electricity market in a single zone (South Africa)."""
    n = pypsa.Network()
    add_components(n, "South Africa")
    n.optimize()
    return n


def simulate_multizone():
    """Simulate electricity market across three zones with transmission constraints."""
    n = pypsa.Network()
    add_components(n, ["South Africa", "Mozambique", "Eswatini"])
    n.optimize()
    return n


def simulate_multizone_with_transmission(transmission_capacity_dict):
    """Simulate multizone market with custom transmission capacities."""
    n = pypsa.Network()
    add_components(n, ["South Africa", "Mozambique", "Eswatini"])
    
    # Update transmission capacities based on input
    for link_name, capacity in transmission_capacity_dict.items():
        if link_name in n.links.index:
            n.links.loc[link_name, "p_nom"] = capacity
    
    n.optimize()
    return n

def simulate_multizone_with_transmission_and_generation(transmission_capacity_dict, generation_capacity_dict):
    """Simulate multizone market with custom transmission and generation capacities."""
    n = pypsa.Network()
    add_components(n, ["South Africa", "Mozambique", "Eswatini"])
    
    # Update transmission capacities
    for link_name, capacity in transmission_capacity_dict.items():
        if link_name in n.links.index:
            n.links.loc[link_name, "p_nom"] = capacity
    
    # Update generation capacities
    for country, tech_dict in generation_capacity_dict.items():
        for tech, capacity in tech_dict.items():
            gen_name = f"{country}-{tech}"
            if gen_name in n.generators.index:
                n.generators.loc[gen_name, "p_nom"] = capacity
    
    n.optimize()
    return n    
