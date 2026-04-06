import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from src.economic_dispatch import (
    optimize_unconstrained_dispatch,
    optimize_constrained_dispatch,
    TRANSMISSION_CAPACITY_BASE,
    BUS_DEMAND,
)

# Page configuration
st.set_page_config(page_title="Economic Dispatch Analysis", layout="wide")

# Initialize session state for caching
if "network_unconstrained" not in st.session_state:
    st.session_state.network_unconstrained = None

# ============================================================================
# SECTION 1: INTRODUCTION
# ============================================================================
st.title("⚡ Economic vs Operational Dispatch")

st.markdown("""
### Understanding Dispatch Constraints

**Economic Dispatch** seeks the minimum-cost generation schedule to meet demand, considering only 
the generation capacity of each unit. The problem assumes electricity can be transported freely 
across the network without physical constraints.

**Operational Dispatch** (AC-OPF) adds **transmission constraints**, recognizing that:
- Power flows follow physical laws (Ohm's law, Kirchhoff's laws)
- Transmission lines have limited capacity
- Congestion can prevent low-cost generation from reaching demand centers

**Key Insight:** Even though economically optimal, the cheapest generator might not be able to 
export power to demand centers due to transmission bottlenecks. This forces us to dispatch more 
expensive local generation, increasing system costs.

This simulation demonstrates this tension by comparing unconstrained (economic) vs constrained 
(operational) dispatch on a simple 3-bus network. We will start with the unconstrained case, then interactively add transmission limits to see how costs and locational prices change. In the following figure, the network setup is shown, with generators, loads, and transmission lines. The transmission lines have enough capacity (for the given demand) in the economic dispatch case, but later the capacities will be reduced to illustrate congestion effects.
""")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("images/economic_dispatch.png", caption="3-Bus Network for Economic Dispatch Simulation")

# ============================================================================
# SECTION 2: BASE CASE (Static - Cached)
# ============================================================================
st.markdown("---")
st.markdown("## Part 1: Economic Dispatch (No Transmission Constraints)")

if st.session_state.network_unconstrained is None:
    with st.spinner("Computing unconstrained economic dispatch..."):
        st.session_state.network_unconstrained = optimize_unconstrained_dispatch()

n_unconstrained = st.session_state.network_unconstrained

# Key metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Total System Cost",
        f"€{n_unconstrained.objective:,.0f}/h",
        help="Minimum cost to serve all demand"
    )
with col2:
    st.metric(
        "Total Demand",
        f"{BUS_DEMAND['1'] + BUS_DEMAND['2'] + BUS_DEMAND['3']:.0f} MW",
        help="Sum of demand across all buses"
    )
with col3:
    st.metric(
        "Dispatch Efficiency",
        "100%",
        help="All economically optimal"
    )

# Generator dispatch
st.markdown("### Generator Dispatch & Utilization")
gen_dispatch_unconstrained = []
for gen_name in n_unconstrained.generators.index:
    gen_data = n_unconstrained.generators.loc[gen_name]
    dispatch = n_unconstrained.generators_t.p[gen_name].iloc[0]
    utilization = (dispatch / gen_data.p_nom * 100) if gen_data.p_nom > 0 else 0
    
    gen_dispatch_unconstrained.append({
        "Generator": gen_name,
        "Bus": gen_data.bus,
        "Capacity (MW)": gen_data.p_nom,
        "Dispatch (MW)": round(dispatch, 2),
        "Utilization (%)": round(utilization, 1),
        "Cost (€/MWh)": gen_data.marginal_cost,
        "Total Cost (€/h)": round(gen_data.marginal_cost * dispatch, 2),
    })

gen_df_unconstrained = pd.DataFrame(gen_dispatch_unconstrained).sort_values("Cost (€/MWh)")
st.dataframe(
    gen_df_unconstrained.set_index("Generator"),
    use_container_width=True,
    hide_index=False
)

# Transmission flows
st.markdown("### Transmission Line Flows")
line_flows_unconstrained = []
for line_name in n_unconstrained.lines.index:
    line_data = n_unconstrained.lines.loc[line_name]
    flow = n_unconstrained.lines_t.p0[line_name].iloc[0]
    utilization = (abs(flow) / line_data.s_nom * 100) if line_data.s_nom > 0 else 0
    
    line_flows_unconstrained.append({
        "Line": line_name,
        "From Bus": line_data.bus0,
        "To Bus": line_data.bus1,
        "Capacity (MVA)": line_data.s_nom,
        "Flow (MW)": round(flow, 2),
        "Utilization (%)": round(utilization, 1),
    })

line_df_unconstrained = pd.DataFrame(line_flows_unconstrained)
st.dataframe(line_df_unconstrained.set_index("Line"), use_container_width=True, hide_index=False)

# Locational Marginal Prices
st.markdown("### Locational Marginal Prices (LMPs)")
lmp_unconstrained = []
for bus in n_unconstrained.buses.index:
    lmp = n_unconstrained.buses_t.marginal_price[bus].iloc[0] if not n_unconstrained.buses_t.marginal_price.empty else 0
    demand = n_unconstrained.loads[n_unconstrained.loads.bus == bus].p_set.sum()
    
    lmp_unconstrained.append({
        "Bus": bus,
        "LMP (€/MWh)": round(lmp, 2),
        "Demand (MW)": demand,
    })

lmp_df_unconstrained = pd.DataFrame(lmp_unconstrained)
st.dataframe(lmp_df_unconstrained.set_index("Bus"), use_container_width=True, hide_index=False)

st.info(
    "**Observation:** Without transmission constraints, all buses have the same LMP (€7.5/MWh), "
    "reflecting the marginal cost of the cheapest generator that fulfills demand. Dispatch follows pure merit order: "
    "Gen B (€6/MWh) supplies as much as possible, then Gen A (€7.5/MWh)."
)

# ============================================================================
# SECTION 3: INTERACTIVE CONSTRAINED DISPATCH
# ============================================================================
st.markdown("---")
st.markdown("## Part 2: Operational Dispatch (With Transmission Constraints)")

st.markdown("""
Now we add **transmission constraints**. Adjust the line capacities below to see how physical 
network limits force us to dispatch more expensive generators, increasing total system cost.
""")

col1, col2, col3 = st.columns(3)
with col1:
    line_1_2_capacity = st.slider(
        "LINE 1-2 Capacity (MVA)",
        min_value=50,
        max_value=300,
        value=TRANSMISSION_CAPACITY_BASE["LINE_1_2"],
        step=10,
        key="line_1_2_capacity",
    )
with col2:
    line_1_3_capacity = st.slider(
        "LINE 1-3 Capacity (MVA)",
        min_value=50,
        max_value=300,
        value=TRANSMISSION_CAPACITY_BASE["LINE_1_3"],
        step=10,
        key="line_1_3_capacity",
    )
with col3:
    line_2_3_capacity = st.slider(
        "LINE 2-3 Capacity (MVA)",
        min_value=50,
        max_value=300,
        value=TRANSMISSION_CAPACITY_BASE["LINE_2_3"],
        step=10,
        key="line_2_3_capacity",
    )

transmission_limits = {
    "LINE_1_2": line_1_2_capacity,
    "LINE_1_3": line_1_3_capacity,
    "LINE_2_3": line_2_3_capacity,
}

# Optimize with constraints
with st.spinner("Computing constrained dispatch..."):
    n_constrained = optimize_constrained_dispatch(transmission_limits)
    st.write(n_constrained.model.status)
    if n_constrained.model.status != "ok":
        st.error("Optimization failed! Please increase the line capacities.")
        st.stop()

# Key metrics with comparison
col1, col2, col3 = st.columns(3)
with col1:
    cost_increase = n_constrained.objective - n_unconstrained.objective
    st.metric(
        "Total System Cost",
        f"€{n_constrained.objective:,.0f}/h",
        delta=f"+€{cost_increase:,.0f}" if cost_increase > 0 else f"€{cost_increase:,.0f}",
        help="Cost with transmission constraints"
    )
with col2:
    st.metric(
        "Congestion Cost",
        f"€{cost_increase:,.0f}/h",
        help="Additional cost due to transmission limits"
    )
with col3:
    cost_pct_increase = (cost_increase / n_unconstrained.objective * 100) if n_unconstrained.objective > 0 else 0
    st.metric(
        "Cost Increase",
        f"{cost_pct_increase:.1f}%",
        help="Percentage increase vs unconstrained"
    )

# Generator dispatch comparison
st.markdown("### Generator Dispatch Comparison")
gen_dispatch_constrained = []
for gen_name in n_constrained.generators.index:
    gen_data = n_constrained.generators.loc[gen_name]
    dispatch_unc = n_unconstrained.generators_t.p[gen_name].iloc[0]
    dispatch_con = n_constrained.generators_t.p[gen_name].iloc[0]
    utilization = (dispatch_con / gen_data.p_nom * 100) if gen_data.p_nom > 0 else 0
    
    gen_dispatch_constrained.append({
        "Generator": gen_name,
        "Bus": gen_data.bus,
        "Capacity (MW)": gen_data.p_nom,
        "Unconstrained (MW)": round(dispatch_unc, 2),
        "Constrained (MW)": round(dispatch_con, 2),
        "Change (MW)": round(dispatch_con - dispatch_unc, 2),
        "Utilization (%)": round(utilization, 1),
        "Cost (€/MWh)": gen_data.marginal_cost,
    })

gen_df_constrained = pd.DataFrame(gen_dispatch_constrained).sort_values("Cost (€/MWh)")

# Visualization: Generator dispatch comparison
fig_gen = px.bar(
    gen_df_constrained,
    x="Generator",
    y=["Unconstrained (MW)", "Constrained (MW)"],
    barmode="group",
    title="Generator Dispatch: Unconstrained vs Constrained",
    labels={"value": "Dispatch (MW)"},
    color_discrete_map={
        "Unconstrained (MW)": "lightblue",
        "Constrained (MW)": "darkblue"
    }
)
fig_gen.update_layout(height=400)
st.plotly_chart(fig_gen, use_container_width=True)

st.dataframe(gen_df_constrained.set_index("Generator"), use_container_width=True, hide_index=False)

# Transmission flows
st.markdown("### Transmission Line Flows (Constrained)")
line_flows_constrained = []
for line_name in n_constrained.lines.index:
    line_data = n_constrained.lines.loc[line_name]
    flow = n_constrained.lines_t.p0[line_name].iloc[0]
    utilization = (abs(flow) / line_data.s_nom * 100) if line_data.s_nom > 0 else 0
    
    line_flows_constrained.append({
        "Line": line_name,
        "Capacity (MVA)": line_data.s_nom,
        "Flow (MW)": round(flow, 2),
        "Utilization (%)": round(utilization, 1),
        "Binding": "YES ⚠️" if utilization > 95 else "No",
    })

line_df_constrained = pd.DataFrame(line_flows_constrained)
st.dataframe(line_df_constrained.set_index("Line"), use_container_width=True, hide_index=False)

# Locational Marginal Prices
st.markdown("### Locational Marginal Prices (Constrained)")
lmp_constrained = []
for bus in n_constrained.buses.index:
    lmp = n_constrained.buses_t.marginal_price[bus].iloc[0] if not n_constrained.buses_t.marginal_price.empty else 0
    demand = n_constrained.loads[n_constrained.loads.bus == bus].p_set.sum()
    
    lmp_constrained.append({
        "Bus": bus,
        "LMP (€/MWh)": round(lmp, 2),
        "Demand (MW)": demand,
    })

lmp_df_constrained = pd.DataFrame(lmp_constrained)

# Visualization: LMP comparison
fig_lmp = px.bar(
    lmp_df_constrained,
    x="Bus",
    y="LMP (€/MWh)",
    title="Locational Marginal Prices (Constrained)",
    color="LMP (€/MWh)",
    color_continuous_scale="RdYlGn_r",
    text="LMP (€/MWh)",
)
fig_lmp.update_traces(textposition="auto")
fig_lmp.update_layout(height=400, showlegend=False)
st.plotly_chart(fig_lmp, use_container_width=True)

st.dataframe(lmp_df_constrained.set_index("Bus"), use_container_width=True, hide_index=False)

# ============================================================================
# SECTION 4: KEY INSIGHTS
# ============================================================================
st.markdown("---")
st.markdown("## 📊 Key Insights & Implications")

st.markdown("""
### Why Does Cost Increase?

1. **Transmission Bottlenecks:** The cheap generator (Gen B on Bus 1) cannot export enough power 
   to Bus 3 due to line capacity limits.

2. **Expensive Local Generation:** Bus 3 must rely on Gen D (€10/MWh), which is more expensive 
   than the optimal dispatch would use.

3. **Locational Price Differences:** With constraints, each bus develops a different LMP:
   - Buses importing power (high demand, low local generation) have **higher LMPs**
   - Buses exporting power (low demand, cheap generation) have **lower LMPs**

4. **Congestion Rent:** The price difference reflects the value of adding transmission capacity.

### Practical Applications

- **Grid Investment:** Should utilities expand Line 1-3 if it saves €X/h?
- **Market Design:** LMPs guide efficient investment in generation and transmission
- **Reliability:** Physical constraints may force us to dispatch "uneconomical" units for stability

### Try It Yourself

Reduce Line 1-3 capacity to 150 MVA, notice how costs spike and Bus 3's LMP surges. 
This is the congestion cost you'd see in real electricity markets!
""")

st.info(
    f"**Summary:** Transmission constraints force a dispatch change that increases system cost "
    f"by approximately €{cost_increase:,.0f}/h ({cost_pct_increase:.1f}%). In operational planning, "
    f"this congestion cost must be weighed against the investment cost of grid expansion."
)