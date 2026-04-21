import streamlit as st
import plotly.express as px
import pandas as pd
from src.unit_commitment import (
    part_load,
    minimum_up_time,
    minimum_down_time,
    start_up_shut_down_costs,
    ramp_limits
)

# ============================================================================
# Helper Function
# ============================================================================


def transform_load_data(load_data):
    """Duplicate last load value to extend plot to end of last hour."""
    last_row = load_data.iloc[-1:].copy()
    last_row.index = [load_data.index[-1] +
                      (load_data.index[-1] - load_data.index[-2])]
    return pd.concat([load_data, last_row])


# ============================================================================
# PAGE HEADER
# ============================================================================
st.title("🎛️ Unit Commitment")

st.markdown("""
### Understanding Unit Commitment

**Unit Commitment (UC)** determines which conventional generators should be ON or OFF at each time step,
given a load profile. Unlike renewables (whose availability is dictated by weather), conventional plants
can be controlled, but turning them on and off has operational constraints and costs.

This creates a trade-off: *Should we keep a generator running even when not needed, or turn it off to save fuel
and risk high startup costs when demand returns?*

We explore five key operational constraints that make UC realistic:
1. **Part-load operation** — Generators cannot run below a minimum threshold
2. **Minimum up time** — Generators must stay on for a minimum duration once started
3. **Minimum down time** — Generators must stay off for a minimum duration once stopped
4. **Startup and shutdown costs** — Fixed costs for turning units on/off
5. **Ramping constraints** — Limits on how fast generators can change output
""")

# ============================================================================
# INITIALIZATION: Cache all optimizations in session state
# ============================================================================
with st.spinner("Initializing optimizations..."):
    # Define default parameters for each scenario
    DEFAULTS = {
        "part_load": {"p_min_coal": 0.3, "p_min_gas": 0.1},
        "min_up_time": {"min_ut": 3, "utb": 0},
        "min_down_time": {"min_dt": 2, "dtb": 1},
        "startup_shutdown": {"min_dt": 2, "start_up_cost_coal": 5_000, "shut_down_cost_gas": 25},
        "ramp_limits": {"ramp_limit_up_coal": 0.1, "ramp_limit_down_coal": 0.2},
    }

    # Initialize session state for all scenarios with defaults
    if "uc_part_load" not in st.session_state:
        st.session_state.uc_part_load = part_load(
            **DEFAULTS["part_load"])
    if "uc_part_load_params" not in st.session_state:
        st.session_state.uc_part_load_params = dict(DEFAULTS["part_load"])
    
    if "uc_min_up_time" not in st.session_state:
        st.session_state.uc_min_up_time = minimum_up_time(
            **DEFAULTS["min_up_time"])
    if "uc_min_up_time_params" not in st.session_state:
        st.session_state.uc_min_up_time_params = dict(DEFAULTS["min_up_time"])
    
    if "uc_min_down_time" not in st.session_state:
        st.session_state.uc_min_down_time = minimum_down_time(
            **DEFAULTS["min_down_time"])
    if "uc_min_down_time_params" not in st.session_state:
        st.session_state.uc_min_down_time_params = dict(DEFAULTS["min_down_time"])
    
    if "uc_startup_shutdown" not in st.session_state:
        st.session_state.uc_startup_shutdown = start_up_shut_down_costs(
            **DEFAULTS["startup_shutdown"])
    if "uc_startup_shutdown_params" not in st.session_state:
        st.session_state.uc_startup_shutdown_params = dict(DEFAULTS["startup_shutdown"])
    
    if "uc_ramp_limits" not in st.session_state:
        st.session_state.uc_ramp_limits = ramp_limits(
            **DEFAULTS["ramp_limits"])
    if "uc_ramp_limits_params" not in st.session_state:
        st.session_state.uc_ramp_limits_params = dict(DEFAULTS["ramp_limits"])

# ============================================================================
# SECTION 1: PART-LOAD OPERATION
# ============================================================================

st.markdown("---")
st.markdown("## Part 1: Part-Load Operation")

st.markdown("""
Conventional generators cannot run at any arbitrary power level. Each unit has a **minimum stable generation**
level (minimum power output), below which it must be turned off entirely. This is modeled as `p_min_pu`
(minimum power as a fraction of rated capacity).

Adjust the minimum power thresholds to see how this constraint affects dispatch and costs.
""")

col1, col2 = st.columns(2)
with col1:
    p_min_coal_pl = st.slider(
        "Coal Min Power Output (pu)",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULTS["part_load"]["p_min_coal"],
        step=0.1,
        key="p_min_coal_pl",
    )
with col2:
    p_min_gas_pl = st.slider(
        "Gas Min Power Output (pu)",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULTS["part_load"]["p_min_gas"],
        step=0.1,
        key="p_min_gas_pl",
    )

# Recompute if sliders changed from the last values used to build the result
current_part_load_params = {
    "p_min_coal": p_min_coal_pl, "p_min_gas": p_min_gas_pl}
last_part_load_params = st.session_state.get("uc_part_load_params")
if ("uc_part_load" not in st.session_state or last_part_load_params != current_part_load_params):
    with st.spinner("Optimizing dispatch..."):
        st.session_state.uc_part_load = part_load(
            p_min_coal=p_min_coal_pl, p_min_gas=p_min_gas_pl)
        st.session_state.uc_part_load_params = current_part_load_params

nu_pl = st.session_state.uc_part_load

if nu_pl.model.status != "ok":
    st.error("Optimization infeasible. Change minimum power thresholds.")
    st.stop()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.metric("System Cost", f"€{nu_pl.objective:,.0f}")
    st.dataframe(nu_pl.generators[[
                 "p_nom", "p_min_pu", "marginal_cost"]], width="stretch")
    st.write("**Generator Status**")
    st.dataframe(nu_pl.generators_t.status, width="stretch")
    st.write("**Generator Output**")
    st.dataframe(nu_pl.generators_t.p, width="stretch")

with col2:
    load_data_pl = nu_pl.loads_t.p_set.copy()
    load_data_pl = transform_load_data(load_data_pl)

    fig_pl = px.line(
        load_data_pl,
        title="Load Profile",
        labels={"index": "Time (h)", "value": "Load (MW)"},
        line_shape="hv"
    )
    fig_pl.update_layout(height=400)
    st.plotly_chart(fig_pl, width="stretch")

    st.info(
        "**💡Insight (default scenario example):**\n"
        "- Coal(€20/MWh) has lower marginal cost but higher minimum output (30 %= 3,000 MW).\n"
        f"- At t=3, load drops below coal's minimum, forcing coal off and gas on despite higher cost (€70/MWh)."
    )
    st.warning("""
    ⚠️ **Important:** If minimum power thresholds are set too high, the system may not be able to meet demand. 
    For example, if both coal and gas minimum outputs exceed total load, no feasible solution exists. 
    The optimizer will return an error, adjust the sliders to ensure demand can be met.

    Adjust the minimum power thresholds to see how this constraint affects dispatch and costs.
    """)

# ============================================================================
# SECTION 2: MINIMUM UP TIME
# ============================================================================

st.markdown("---")
st.markdown("## Part 2: Minimum Up Time")
st.markdown("""
**Minimum up time** constraints prevent frequent cycling. Once a generator starts, it must stay online
for a minimum duration. This reflects real equipment constraints (thermal stress, startup/shutdown costs).

Adjust the gas generator's minimum up time to see how it trades off between startup costs and dispatch flexibility.
""")

col1, col2 = st.columns(2)
with col1:
    min_ut_val = st.slider(
        "Gas Min Up Time (hours)",
        min_value=0,
        max_value=3,
        value=DEFAULTS["min_up_time"]["min_ut"],
        step=1,
        key="min_ut_slider",
    )
with col2:
    utb_val = st.slider(
        "Gas Prior Up Time (hours)",
        min_value=0,
        max_value=1,
        value=DEFAULTS["min_up_time"]["utb"],
        step=1,
        key="utb_slider",
    )

# Recompute if sliders changed from the last values used to build the result
current_min_up_time_params = {"min_ut": min_ut_val, "utb": utb_val}
last_min_up_time_params = st.session_state.get("uc_min_up_time_params")
if ("uc_min_up_time" not in st.session_state or last_min_up_time_params != current_min_up_time_params):
    with st.spinner("Optimizing dispatch..."):
        st.session_state.uc_min_up_time = minimum_up_time(
            min_ut=min_ut_val, utb=utb_val)
        st.session_state.uc_min_up_time_params = current_min_up_time_params

nu_ut = st.session_state.uc_min_up_time

if nu_ut.model.status != "ok":
    st.error("Optimization infeasible. Change minimum up time.")
    st.stop()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.metric("System Cost", f"€{nu_ut.objective:,.0f}")
    st.dataframe(
        nu_ut.generators[["p_nom", "p_min_pu",
                          "marginal_cost", "stand_by_cost", "min_up_time"]],
        width="stretch"
    )
    st.write("**Generator Status**")
    st.dataframe(nu_ut.generators_t.status, width="stretch")
    st.write("**Generator Output**")
    st.dataframe(nu_ut.generators_t.p, width="stretch")

with col2:
    load_data_ut = nu_ut.loads_t.p_set.copy()
    load_data_ut = transform_load_data(load_data_ut)
    fig_ut = px.line(
        load_data_ut,
        title="Load Profile",
        labels={"index": "Time (h)", "value": "Load (MW)"},
        line_shape="hv"
    )
    fig_ut.update_layout(height=400)
    st.plotly_chart(fig_ut, width="stretch")
    st.info(
        "**💡Insight:**\n"
        "- Minimum up time forces generators to stay online longer than economically optimal.\n"
        "- This increases system cost but improves reliability by reducing rapid on/off cycling."
    )

# ============================================================================
# SECTION 3: MINIMUM DOWN TIME
# ============================================================================

st.markdown("---")
st.markdown("## Part 3: Minimum Down Time")

st.markdown("""
**Minimum down time** prevents frequent restarts. Once a generator stops, it must remain offline 
for a minimum duration. This protects equipment and reduces cumulative stress.

Adjust the coal generator's minimum down time to see how it affects dispatch when demand returns.
""")
col1, col2 = st.columns(2)
with col1:
    min_dt_val = st.slider(
        "Coal Min Down Time (hours)",
        min_value=0,
        max_value=3,
        value=DEFAULTS["min_down_time"]["min_dt"],
        step=1,
        key="min_dt_slider",
    )
with col2:
    dtb_val = st.slider(
        "Coal Prior Down Time (hours)",
        min_value=0,
        max_value=1,
        value=DEFAULTS["min_down_time"]["dtb"],
        step=1,
        key="dtb_slider",
    )

# Recompute if sliders changed from the last values used to build the result
current_min_down_time_params = {"min_dt": min_dt_val, "dtb": dtb_val}
last_min_down_time_params = st.session_state.get("uc_min_down_time_params")
if ("uc_min_down_time" not in st.session_state or last_min_down_time_params != current_min_down_time_params):
    with st.spinner("Optimizing dispatch..."):
        st.session_state.uc_min_down_time = minimum_down_time(
            min_dt=min_dt_val, dtb=dtb_val)
        st.session_state.uc_min_down_time_params = current_min_down_time_params

nu_dt = st.session_state.uc_min_down_time

if nu_dt.model.status != "ok":
    st.error("Optimization infeasible. Change minimum down time.")
    st.stop()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.metric("System Cost", f"€{nu_dt.objective:,.0f}")
    st.dataframe(
        nu_dt.generators[["p_nom", "p_min_pu",
                          "marginal_cost", "min_down_time"]],
        width="stretch"
    )
    st.write("**Generator Status**")
    st.dataframe(nu_dt.generators_t.status, width="stretch")
    st.write("**Generator Output**")
    st.dataframe(nu_dt.generators_t.p, width="stretch")

with col2:
    load_data_dt = nu_dt.loads_t.p_set.copy()
    load_data_dt = transform_load_data(load_data_dt)

    fig_dt = px.line(
        load_data_dt,
        title="Load Profile",
        labels={"index": "Time (h)", "value": "Load (MW)"},
        line_shape="hv"
    )
    fig_dt.update_layout(height=400)
    st.plotly_chart(fig_dt, width="stretch")

    st.info(
        "**💡Insight:**\n"
        "- When coal is forced offline, it cannot quickly restart due to minimum down time.\n"
        "- Gas must meet demand at higher cost, increasing system expenses."
    )

# ============================================================================
# SECTION 4: STARTUP AND SHUTDOWN COSTS
# ============================================================================

st.markdown("---")
st.markdown("## Part 4: Startup and Shutdown Costs")

st.markdown("""
Starting and stopping generators incurs real costs: fuel waste during startup, wear and tear, and emissions. 
These **fixed startup/shutdown costs** make it economically attractive to avoid unnecessary cycling.

Adjust the startup and shutdown costs to see how they influence on/off decisions.
""")

col1, col2 = st.columns(2)
with col1:
    start_cost_val = st.slider(
        "Coal Startup Cost (€/start)",
        min_value=0,
        max_value=10_000,
        value=DEFAULTS["startup_shutdown"]["start_up_cost_coal"],
        step=500,
        key="start_cost_slider",
    )
    min_dt_susc_val = st.slider(
        "Coal Min Down Time (hours)",
        min_value=0,
        max_value=3,
        value=DEFAULTS["startup_shutdown"]["min_dt"],
        step=1,
        key="min_dt_susc_slider",
    )
with col2:
    shut_cost_val = st.slider(
        "Gas Shutdown Cost (€/stop)",
        min_value=0,
        max_value=200,
        value=DEFAULTS["startup_shutdown"]["shut_down_cost_gas"],
        step=5,
        key="shut_cost_slider",
    )

# Recompute if sliders changed from the last values used to build the result
current_startup_shutdown_params = {"min_dt": min_dt_susc_val,
                                   "start_up_cost_coal": start_cost_val, "shut_down_cost_gas": shut_cost_val}
last_startup_shutdown_params = st.session_state.get(
    "uc_startup_shutdown_params")
if ("uc_startup_shutdown" not in st.session_state or last_startup_shutdown_params != current_startup_shutdown_params):
    with st.spinner("Optimizing dispatch..."):
        st.session_state.uc_startup_shutdown = start_up_shut_down_costs(
            min_dt=min_dt_susc_val,
            start_up_cost_coal=start_cost_val,
            shut_down_cost_gas=shut_cost_val
        )
        st.session_state.uc_startup_shutdown_params = current_startup_shutdown_params

nu_susc = st.session_state.uc_startup_shutdown

if nu_susc.model.status != "ok":
    st.error("Optimization infeasible. Change startup/shutdown costs or constraints.")
    st.stop()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.metric("System Cost", f"€{nu_susc.objective:,.0f}")
    st.dataframe(
        nu_susc.generators[["p_nom", "p_min_pu", "marginal_cost",
                            "start_up_cost", "shut_down_cost", "min_down_time"]],
        width="stretch"
    )
    st.write("**Generator Status**")
    st.dataframe(nu_susc.generators_t.status, width="stretch")
    st.write("**Generator Output**")
    st.dataframe(nu_susc.generators_t.p, width="stretch")

with col2:
    load_data_susc = nu_susc.loads_t.p_set.copy()
    load_data_susc = transform_load_data(load_data_susc)
    fig_susc = px.line(
        load_data_susc,
        title="Load Profile",
        labels={"index": "Time (h)", "value": "Load (MW)"},
        line_shape="hv"
    )
    fig_susc.update_layout(height=400)
    st.plotly_chart(fig_susc, width="stretch", key="susc_load_plot")

    st.info(
        "**💡Insight:**\n"
        "- High startup costs make it expensive to turn generators on; high shutdown costs make it expensive to turn them off.\n"
        "- The optimizer balances these costs against the savings from avoiding unnecessary running."
    )
    st.warning(
        "⚠️ **Note (default scenario example):** The gas generator shuts down at t=0, starts at t=1, and shuts down again at t=2. "
        "The shutdown cost is therefore incurred twice in this scenario."
    )

# ============================================================================
# SECTION 5: RAMPING CONSTRAINTS
# ============================================================================

st.markdown("---")
st.markdown("## Part 5: Ramping Constraints")

st.markdown("""
Generators cannot instantaneously change their output, equipment has physical limits on how fast it can ramp up or down. 
These **ramping rate constraints** are expressed as maximum change per hour (as a fraction of rated capacity).

Adjust the coal generator's ramping rates to see how physical limits force more expensive dispatch patterns.
""")

col1, col2 = st.columns(2)
with col1:
    ramp_up_val = st.slider(
        "Coal Ramp Up Rate (pu/h)",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULTS["ramp_limits"]["ramp_limit_up_coal"],
        step=0.1,
        key="ramp_up_slider",
    )
with col2:
    ramp_down_val = st.slider(
        "Coal Ramp Down Rate (pu/h)",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULTS["ramp_limits"]["ramp_limit_down_coal"],
        step=0.1,
        key="ramp_down_slider",
    )

# Recompute if sliders changed from the last values used to build the result
current_ramp_limits_params = {
    "ramp_limit_up_coal": ramp_up_val, "ramp_limit_down_coal": ramp_down_val}
last_ramp_limits_params = st.session_state.get("uc_ramp_limits_params")
if ("uc_ramp_limits" not in st.session_state or last_ramp_limits_params != current_ramp_limits_params):
    with st.spinner("Optimizing dispatch..."):
        st.session_state.uc_ramp_limits = ramp_limits(
            ramp_limit_up_coal=ramp_up_val,
            ramp_limit_down_coal=ramp_down_val
        )
        st.session_state.uc_ramp_limits_params = current_ramp_limits_params

nu_ramp = st.session_state.uc_ramp_limits

if nu_ramp.model.status != "ok":
    st.error("Optimization infeasible. Increase ramping rates.")
    st.stop()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.metric("System Cost", f"€{nu_ramp.objective:,.0f}")
    st.dataframe(
        nu_ramp.generators[["p_nom", "p_min_pu",
                            "marginal_cost", "ramp_limit_up", "ramp_limit_down"]],
        width="stretch"
    )
    st.write("**Generator Status**")
    st.dataframe(nu_ramp.generators_t.status, width="stretch")
    st.write("**Generator Output**")
    st.dataframe(nu_ramp.generators_t.p, width="stretch")

with col2:
    load_data_ramp = nu_ramp.loads_t.p_set.copy()
    load_data_ramp = transform_load_data(load_data_ramp)
    fig_ramp = px.line(
        load_data_ramp,
        title="Load Profile",
        labels={"index": "Time (h)", "value": "Load (MW)"},
        line_shape="hv"
    )
    fig_ramp.update_layout(height=400)
    st.plotly_chart(fig_ramp, width="stretch", key="ramp_load_plot")

    st.info(
        "**💡Insight:**\n"
        "- Tight ramping limits prevent rapid changes. Coal cannot instantly meet load spikes, forcing gas to ramp up quickly (at higher cost).\n"
        "- Even uneconomical dispatch patterns may be necessary to respect physical constraints."
    )
    st.warning(
        "⚠️ **Ramping Trade-off Example:** If you increase the coal ramp-up rate to 0.3 pu/h:\n"
        "- **At t=4:** Coal ramps down to 5,000 MW, gas ramps up to 2,000 MW, seemingly uneconomical.\n"
        "- **Why?** At t=5, demand drops to 3,000 MW. Coal cannot ramp directly from 7,000 MW to 3,000 MW (exceeds ramp-down limit).\n"
        "- **Result:** Coal must ramp down gradually, forcing the uneconomical pattern at t=4.\n"
        "- **Takeaway:** Physical constraints override economic optimization."
    )
