import pypsa


def part_load(p_min_coal=0.3, p_min_gas=0.1):
    """Unit commitment without startup/shutdown or time-coupling constraints."""
    nu = pypsa.Network(snapshots=range(4))
    nu.add("Bus", "bus")
    nu.add(
        "Generator",
        "coal",
        bus="bus",
        committable=True,
        p_nom=10_000,
        p_min_pu=p_min_coal,
        marginal_cost=20,
    )
    nu.add(
        "Generator",
        "gas",
        bus="bus",
        committable=True,
        p_nom=1_200,
        p_min_pu=p_min_gas,
        marginal_cost=70,
    )
    nu.add("Load", "load", bus="bus", p_set=[4_000, 6_000, 5_000, 1_000])
    nu.optimize()
    return nu


def minimum_up_time(min_ut=3, utb=0):
    """Unit commitment with minimum up time constraint on gas generator."""
    nu = pypsa.Network(snapshots=range(4))
    nu.add("Bus", "bus")
    nu.add(
        "Generator",
        "coal",
        bus="bus",
        committable=True,
        p_min_pu=0.3,
        marginal_cost=20,
        p_nom=10_000,
    )
    nu.add(
        "Generator",
        "gas",
        bus="bus",
        committable=True,
        stand_by_cost=50,
        marginal_cost=70,
        p_min_pu=0.1,
        p_nom=1_200,
        up_time_before=utb,
        min_up_time=min_ut
    )
    nu.add("Load", "load", bus="bus", p_set=[4_000, 1_000, 5_000, 3_000])
    nu.optimize()
    return nu


def minimum_down_time(min_dt=2, dtb=1):
    """Unit commitment with minimum down time constraint on coal generator."""
    nu = pypsa.Network(snapshots=range(4))
    nu.add("Bus", "bus")
    nu.add(
        "Generator",
        "coal",
        bus="bus",
        committable=True,
        p_min_pu=0.3,
        marginal_cost=20,
        min_down_time=min_dt,
        down_time_before=dtb,
        up_time_before=0 if dtb > 0 else 1,  # Ensure mutually exclusive initial state
        p_nom=10_000,
    )
    nu.add(
        "Generator",
        "gas",
        bus="bus",
        committable=True,
        marginal_cost=70,
        p_min_pu=0.1,
        p_nom=4_000,
    )
    nu.add("Load", "load", bus="bus", p_set=[3_000, 1_000, 3_000, 8_000])
    nu.optimize()
    return nu


def start_up_shut_down_costs(min_dt, start_up_cost_coal=5_000, shut_down_cost_gas=25):
    """Unit commitment with startup and shutdown costs."""
    nu = pypsa.Network(snapshots=range(4))
    nu.add("Bus", "bus")
    nu.add(
        "Generator",
        "coal",
        bus="bus",
        committable=True,
        p_min_pu=0.3,
        marginal_cost=20,
        p_nom=10_000,
        start_up_cost=start_up_cost_coal,
        min_down_time=min_dt
    )
    nu.add(
        "Generator",
        "gas",
        bus="bus",
        committable=True,
        marginal_cost=70,
        p_min_pu=0.1,
        p_nom=4_000,
        shut_down_cost=shut_down_cost_gas,
    )
    nu.add("Load", "load", bus="bus", p_set=[3_000, 1_000, 3_000, 8_000])
    nu.optimize()
    return nu


def ramp_limits(ramp_limit_up_coal=0.1, ramp_limit_down_coal=0.2):
    """Unit commitment with ramping rate constraints on coal generator."""
    nu = pypsa.Network(snapshots=range(6))
    nu.add("Bus", "bus")
    nu.add(
        "Generator",
        "coal",
        bus="bus",
        committable=True,
        marginal_cost=20,
        p_nom=10_000,
        ramp_limit_up=ramp_limit_up_coal,
        ramp_limit_down=ramp_limit_down_coal
    )
    nu.add(
        "Generator",
        "gas",
        bus="bus",
        committable=True,
        marginal_cost=70,
        p_nom=4_000,
    )
    nu.add("Load", "load", bus="bus", p_set=[
           4_000, 7_000, 7_000, 7_000, 7_000, 3_000])
    nu.optimize()
    return nu
