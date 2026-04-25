import pypsa

# Default 5-timestep load profile (MW): peaks at noon, drops during off-peak
load_profile_mw = [50, 120, 50, 20, 50]


def negative_prices_dispatch(load_profile_mw=load_profile_mw, luc=True):
    """
    Simulate a two-generator dispatch system demonstrating negative electricity prices.

    This function creates a simple power system with two generators facing a time-varying load.
    The base generator has high startup/shutdown costs and minimum output constraints, while 
    the peak generator is more flexible but more expensive. By comparing linearized vs binary 
    unit commitment formulations, we can observe when and why negative prices emerge.

    Parameters
    ----------
    load_profile_mw : list, optional
        Time-series load demand in MW. Default: [50, 120, 50, 20, 50] representing 5 timesteps.
    luc : bool, optional
        If True, use linearized unit commitment (relaxed LP) producing convex problem with 
        interpretable prices. If False, use binary unit commitment (MILP) producing non-convex 
        problem where prices are not economically meaningful. Default: True

    Returns
    -------
    pypsa.Network
        Optimized network with solved dispatch, commitment status, and marginal prices.
    """
    # Create network with one snapshot per load profile entry
    n = pypsa.Network(snapshots=range(len(load_profile_mw)))
    n.add("Bus", "bus", carrier="AC")

    # Add time-varying demand
    n.add("Load", "load", bus="bus", p_set=load_profile_mw)

    # Base generator: expensive startup/shutdown but cheap to run (baseload plant)
    n.add(
        "Generator",
        "base",
        bus="bus",
        marginal_cost=20,
        committable=True,
        p_nom=100,
        p_min_pu=0.4,  # Minimum output: 40% of capacity when online
        start_up_cost=4_000,
        shut_down_cost=2_000
    )

    # Peak generator: cheap startup but expensive to run (peaker plant)
    n.add(
        "Generator",
        "peak",
        bus="bus",
        marginal_cost=70,
        committable=True,
        p_nom=50,
        p_min_pu=0.2,  # Minimum output: 20% of capacity when online
        start_up_cost=250
    )

    # Optimize with specified unit commitment formulation
    n.optimize(linearized_unit_commitment=luc)
    return n
