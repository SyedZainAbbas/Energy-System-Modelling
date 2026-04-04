import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from electricity_markets import (
    simulate_single_zone,
    simulate_multizone,
    simulate_multizone_with_transmission,
    simulate_multizone_with_transmission_and_generation,
    TRANSMISSION_CAPACITY,
    GENERATION_CAPACITY,
    DEMAND,
)

# Page configuration
st.set_page_config(page_title="Bidding Zone Market Analysis", layout="wide")

# No custom styling needed - using native Streamlit components for theme compatibility

# Initialize session state
if "single_zone_network" not in st.session_state:
    st.session_state.single_zone_network = None
if "multizone_network" not in st.session_state:
    st.session_state.multizone_network = None
if "transmission_sliders_done" not in st.session_state:
    st.session_state.transmission_sliders_done = False


# ============================================================================
# SECTION 1: INTRODUCTION
# ============================================================================
st.title("🔌 Electricity Bidding Zones & Market Prices")

st.markdown("""
### Understanding Zonal vs Nodal Markets

In electricity markets, **bidding zones** represent geographical areas where a single market-clearing price applies. 
This approach simplifies market operations but can mask underlying network constraints.

**Key concepts:**
- **Zonal Model**: Assumes electricity can flow freely within a zone (no internal congestion). 
  Only cross-border constraints matter.
- **Price Formation**: Prices are determined by the marginal generator needed to meet demand in each zone.
- **Congestion Effects**: When transmission capacity is limited, zones may need to rely on expensive local generation,
  leading to price divergence.

This simulation shows how **transmission and generation capacity affects prices and dispatch** across three Southern African countries.
""")

# ============================================================================
# SECTION 2: INITIAL OPTIMIZATION (with status message)
# ============================================================================
st.markdown("---")
st.markdown("## Loading Scenarios...")

with st.spinner("Running initial market simulations..."):
    status_placeholder = st.empty()
    
    status_placeholder.info(
        "⏳ **Running optimizations...** This may take a moment as we're solving three electricity market scenarios. "
        "In each scenario, the system finds the lowest-cost dispatch that meets all demand while respecting transmission constraints."
    )
    
    # Run optimizations in sequence
    if st.session_state.single_zone_network is None:
        st.session_state.single_zone_network = simulate_single_zone()
    if st.session_state.multizone_network is None:
        st.session_state.multizone_network = simulate_multizone()
    
    status_placeholder.success("✅ Scenarios loaded successfully!")

# ============================================================================
# SECTION 3: SCENARIO COMPARISON
# ============================================================================
st.markdown("---")
st.markdown("## Part 1: Single Zone vs Multi-Zone Comparison")

comparison_type = st.radio(
    "Select scenario to analyze:",
    ["Single Zone (Isolated South Africa)", "Multi-Zone (Connected System)"],
    horizontal=True
)

n = (
    st.session_state.single_zone_network
    if comparison_type == "Single Zone (Isolated South Africa)"
    else st.session_state.multizone_network
)

# Display key metrics
col1, col2= st.columns(2)

# Calculate total system cost
total_cost = (n.generators.marginal_cost * n.generators_t.p.sum()).sum()

with col1:
    st.metric("Total System Cost", f"€{total_cost:,.0f}", help="Total generation cost to serve demand")
with col2:
    st.metric("Total Demand Met", f"{n.loads.p_set.sum():,.0f} MW", help="Total electricity demand across zones")

# Generation dispatch
st.markdown("### Generation Dispatch")
gen_data = []
for country in n.buses.index:
    for gen in n.generators[n.generators.bus == country].index:
        tech = gen.split("-")[-1]
        capacity = n.generators.loc[gen, "p_nom"]
        dispatch = n.generators_t.p[gen].iloc[0]
        utilization = (dispatch / capacity * 100) if capacity > 0 else 0
        marginal_cost = n.generators.loc[gen, "marginal_cost"]
        
        gen_data.append({
            "Country": country,
            "Technology": tech,
            "Capacity (MW)": capacity,
            "Dispatch (MW)": dispatch,
            "Utilization (%)": utilization,
            "Cost (€/MWh)": marginal_cost,
        })

gen_df = pd.DataFrame(gen_data)

# Visualization of generation mix
fig = px.bar(
    gen_df,
    x="Country",
    y="Dispatch (MW)",
    color="Technology",
    barmode="stack",
    title="Generation Dispatch by Country",
    hover_data=["Capacity (MW)", "Utilization (%)", "Cost (€/MWh)"],
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# Generation table
st.dataframe(
    gen_df.set_index(["Country", "Technology"]).sort_index(),
    use_container_width=True,
    height=300,
)

# Prices by zone
st.markdown("### Electricity Prices by Zone")
prices_data = []
for country in n.buses.index:
    price = n.buses_t.marginal_price[country].iloc[0] if not n.buses_t.marginal_price.empty else 0
    demand = n.loads[n.loads.bus == country].p_set.sum()
    prices_data.append({"Country": country, "Price (€/MWh)": price, "Demand (MW)": demand})

prices_df = pd.DataFrame(prices_data)
fig_prices = px.bar(
    prices_df,
    x="Country",
    y="Price (€/MWh)",
    color="Country",
    title="Market-Clearing Prices",
    text="Price (€/MWh)",
    hover_data=["Demand (MW)"],
)
fig_prices.update_traces(textposition="auto")
fig_prices.update_layout(height=400, showlegend=False)
st.plotly_chart(fig_prices, use_container_width=True)

# Power flows (only for multi-zone)
if comparison_type == "Multi-Zone (Connected System)" and not n.links.empty:
    st.markdown("### Power Flows & Congestion")
    
    flow_data = []
    for link in n.links.index:
        flow = n.links_t.p0[link].iloc[0]
        capacity = n.links.p_nom[link]
        utilization = abs(flow) / capacity * 100 if capacity > 0 else 0
        direction = "→" if flow >= 0 else "←"
        
        flow_data.append({
            "Corridor": link.replace(" link", ""),
            "Power Flow (MW)": flow,
            "Capacity (MW)": capacity,
            "Utilization (%)": utilization,
            "Direction": direction,
        })
    
    flow_df = pd.DataFrame(flow_data)
    
    fig_flow = px.bar(
        flow_df,
        x="Corridor",
        y="Power Flow (MW)",
        color="Utilization (%)",
        title="Transmission Line Flows",
        text="Power Flow (MW)",
        color_continuous_scale="YlOrRd",
        hover_data=["Capacity (MW)", "Utilization (%)", "Direction"],
    )
    fig_flow.update_traces(textposition="auto")
    fig_flow.update_layout(height=400)
    st.plotly_chart(fig_flow, use_container_width=True)
    
    st.dataframe(flow_df.set_index("Corridor"), use_container_width=True)
    
    # Insights
    max_util = flow_df["Utilization (%)"].max()
    if max_util > 80:
        st.warning("⚠️ **Congestion Alert:** All the links are fully utilized. This is a potential bottleneck limiting power flows.")

# Insights for Part 1
st.markdown("### 💡 Insights from Comparison")
if comparison_type == "Single Zone (Isolated South Africa)":
    st.info(
        "**Single Zone Analysis:**\n\n"
        "- South Africa operates in isolation with its own generation mix\n\n"
        "- Prices are determined solely by South Africa's generation costs\n\n"
        "- Price = Cost of the marginal generator needed to meet demand\n\n"
        "- In this case: Gas (€60/MWh)"
    )
else:
    st.info(
        "**Multi-Zone Analysis:**\n\n"
        "- Three countries with different generation mixes are now connected\n\n"
        "- **Price divergence**: Each zone has a different price based on local marginal costs\n\n"
        "- Mozambique & Eswatini (hydro-rich): Lower prices (€0/MWh)\n\n"
        "- South Africa (thermal-dependent): Higher prices (€60/MWh)\n\n"
        "- **Limited transmission**: Congestion prevents full price convergence\n\n"
        "- Power flows from cheap zones (hydro) to expensive zones (thermal)"
    )
# ============================================================================
# SECTION 4: TRANSMISSION SENSITIVITY ANALYSIS
# ============================================================================
st.markdown("---")
st.markdown("## Part 2: How Transmission Capacity Affects Markets")

st.markdown("""
**Explore the impact of increasing transmission capacity on:**
- Electricity prices across zones
- Power flows between countries
- Overall system efficiency

Use the sliders below to adjust transmission capacity on each corridor. 
The system will recalculate prices and flows based on your input.
""")

col1, col2, col3 = st.columns(3)

with col1:
    sa_moz = st.slider(
        "SA-Mozambique (MW)",
        min_value=0,
        max_value=1250,
        value=750,
        step=50,
        key="sa_moz_slider",
    )

with col2:
    sa_esw = st.slider(
        "SA-Eswatini (MW)",
        min_value=0,
        max_value=1000,
        value=500,
        step=50,
        key="sa_esw_slider",
    )

with col3:
    moz_esw = st.slider(
        "Mozambique-Eswatini (MW)",
        min_value=0,
        max_value=500,
        value=200,
        step=25,
        key="moz_esw_slider",
    )

# Run optimization with new transmission capacities
with st.spinner("Recalculating market with new transmission capacities..."):
    transmission_dict = {
        "South Africa-Mozambique link": sa_moz,
        "South Africa-Eswatini link": sa_esw,
        "Mozambique-Eswatini link": moz_esw,
    }
    n_sensitivity = simulate_multizone_with_transmission(transmission_dict)
# Comparison table
st.markdown("### Transmission Capacity Comparison")
comparison_data = []
base_n = st.session_state.multizone_network

for link in ["South Africa-Mozambique link", "South Africa-Eswatini link", "Mozambique-Eswatini link"]:
    base_capacity = base_n.links.loc[link, "p_nom"]
    new_capacity = n_sensitivity.links.loc[link, "p_nom"]
    base_flow = base_n.links_t.p0[link].iloc[0]
    new_flow = n_sensitivity.links_t.p0[link].iloc[0]
    
    comparison_data.append({
        "Corridor": link.replace(" link", ""),
        "Base Capacity (MW)": base_capacity,
        "New Capacity (MW)": new_capacity,
        "Base Flow (MW)": base_flow,
        "New Flow (MW)": new_flow,
        "Flow Change (MW)": new_flow - base_flow,
    })

comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df.set_index("Corridor"), use_container_width=True)

# Prices comparison
st.markdown("### Price Evolution with Transmission Capacity")
base_prices = {}
new_prices = {}

for country in base_n.buses.index:
    base_prices[country] = base_n.buses_t.marginal_price[country].iloc[0] if not base_n.buses_t.marginal_price.empty else 0
    new_prices[country] = n_sensitivity.buses_t.marginal_price[country].iloc[0] if not n_sensitivity.buses_t.marginal_price.empty else 0

price_comparison = pd.DataFrame({
    "Country": list(base_prices.keys()),
    "Base Price (€/MWh)": list(base_prices.values()),
    "New Price (€/MWh)": list(new_prices.values()),
})
price_comparison["Price Change (€/MWh)"] = price_comparison["New Price (€/MWh)"] - price_comparison["Base Price (€/MWh)"]

# Visualization
fig_price_comp = go.Figure()
fig_price_comp.add_trace(
    go.Bar(x=price_comparison["Country"], y=price_comparison["Base Price (€/MWh)"],
           name="Base Scenario", marker_color="lightblue")
)
fig_price_comp.add_trace(
    go.Bar(x=price_comparison["Country"], y=price_comparison["New Price (€/MWh)"],
           name="New Scenario", marker_color="darkblue")
)
fig_price_comp.update_layout(
    title="Price Comparison: Base vs New Transmission Capacity",
    barmode="group",
    xaxis_title="Country",
    yaxis_title="Price (€/MWh)",
    height=400,
)
st.plotly_chart(fig_price_comp, use_container_width=True)

st.dataframe(price_comparison.set_index("Country"), use_container_width=True)

# System cost comparison
base_cost = (base_n.generators.marginal_cost * base_n.generators_t.p.sum()).sum()
new_cost = (n_sensitivity.generators.marginal_cost * n_sensitivity.generators_t.p.sum()).sum()
cost_saving = base_cost - new_cost

st.info(
    f"**System Efficiency Impact:**\n\n"
    f"- Base system cost: €{base_cost:,.0f}\n\n"
    f"- New system cost: €{new_cost:,.0f}\n\n"
    f"- **Cost saving: €{cost_saving:,.0f} ({cost_saving/base_cost*100:.1f}% improvement)**\n\n"
    f"Higher transmission capacity enables:\n"
    f"1. More efficient dispatch from low-cost zones (hydro)\n"
    f"2. Price convergence across regions\n"
    f"3. Lower overall system costs\n\n"
    f"**Note:** This does not account for the capital cost of building new transmission infrastructure, which would need to be considered in a full cost-benefit analysis."
)


# ============================================================================
# SECTION 5: TRANSMISSION AND GENERATION CAPACITY IMPACT
# ============================================================================
st.markdown("---")
st.markdown("## Part 3: Transmission & Generation Capacity Impact")

st.markdown("""
We've seen how transmission capacity drives price convergence. Now explore how increasing 
hydro generation in Mozambique and Eswatini further reduces prices across the system.

Adjust the sliders to see combined effects of transmission expansion and generation growth.
""")
col1, col2, col3 = st.columns(3)

with col1:
    sa_moz_gen = st.slider(
        "SA-Mozambique (MW)",
        min_value=0,
        max_value=5000,
        value=3500,
        step=50,
        key="sa_moz_slider_gen",
    )

with col2:
    sa_esw_gen = st.slider(
        "SA-Eswatini (MW)",
        min_value=0,
        max_value=2000,
        value=1000,
        step=50,
        key="sa_esw_slider_gen",
    )

with col3:
    moz_esw_gen = st.slider(
        "Mozambique-Eswatini (MW)",
        min_value=0,
        max_value=2000,
        value=1350,
        step=50,
        key="moz_esw_slider_gen",
    )

col1, col2 = st.columns(2)

with col1:
    moz_hydro = st.slider(
        "Mozambique Hydro (MW)",
        min_value=1200,
        max_value=5000,
        value=4000,
        step=50,
        key="moz_hydro_slider",
    )

with col2:
    esw_hydro = st.slider(
        "Eswatini Hydro (MW)",
        min_value=600,
        max_value=1500,
        value=900,
        step=50,
        key="esw_hydro_slider",
    )

# Run optimization with new transmission capacities
with st.spinner("Recalculating market with new generation and transmission capacities..."):
    transmission_dict_gen = {
        "South Africa-Mozambique link": sa_moz_gen,
        "South Africa-Eswatini link": sa_esw_gen,
        "Mozambique-Eswatini link": moz_esw_gen,
    }
    generation_dict_gen = {
        "Mozambique": {"Hydro": moz_hydro},
        "Eswatini": {"Hydro": esw_hydro},
    }
    n_sensitivity_gen = simulate_multizone_with_transmission_and_generation(transmission_dict_gen, generation_dict_gen)

# Comparison table
st.markdown("### Transmission and Generation Capacity Comparison")
flow_data_gen = []

for link in ["South Africa-Mozambique link", "South Africa-Eswatini link", "Mozambique-Eswatini link"]:
    capacity_gen = n_sensitivity_gen.links.loc[link, "p_nom"]
    flow_gen = n_sensitivity_gen.links_t.p0[link].iloc[0]
    
    flow_data_gen.append({
        "Corridor": link.replace(" link", ""),
        "New Capacity (MW)": capacity_gen,
        "New Flow (MW)": flow_gen,
        "Utilization (%)": round(abs(flow_gen) / capacity_gen * 100) if capacity_gen > 0 else "NA",
    })

flow_df_gen = pd.DataFrame(flow_data_gen)
st.dataframe(flow_df_gen.set_index("Corridor"), use_container_width=True)

# Prices comparison
st.markdown("### Price Evolution with new Transmission and Generation Capacity")
base_prices_gen = {}
new_prices_gen = {}

for country in base_n.buses.index:
    base_prices_gen[country] = base_n.buses_t.marginal_price[country].iloc[0] if not base_n.buses_t.marginal_price.empty else 0
    new_prices_gen[country] = n_sensitivity_gen.buses_t.marginal_price[country].iloc[0] if not n_sensitivity_gen.buses_t.marginal_price.empty else 0

price_comparison_gen = pd.DataFrame({
    "Country": list(base_prices_gen.keys()),
    "Base Price (€/MWh)": list(base_prices_gen.values()),
    "New Price (€/MWh)": list(new_prices_gen.values()),
})
price_comparison_gen["Price Change (€/MWh)"] = price_comparison_gen["New Price (€/MWh)"] - price_comparison_gen["Base Price (€/MWh)"]

gen_df = n_sensitivity_gen.generators["p_nom"].to_frame("p_nom")
gen_df = gen_df.merge(n_sensitivity_gen.generators_t.p.T, left_index=True, right_index=True)
gen_df["Utilization (%)"] = gen_df.apply(lambda row: (row[1] / row["p_nom"] * 100) if row["p_nom"] > 0 else 0, axis=1)
gen_df["Type"] = gen_df.index.map(lambda x: x.split("-")[-1])
gen_df.index = gen_df.index.map(lambda x: x.split("-")[0])
gen_df.columns = ["Capacity (MW)", "Dispatch (MW)", "Utilization (%)", "Type"]
gen_df = gen_df[["Type", "Capacity (MW)", "Dispatch (MW)", "Utilization (%)"]]
st.write(gen_df)

# Visualization
fig_price_comp_gen = go.Figure()
fig_price_comp_gen.add_trace(
    go.Bar(x=price_comparison_gen["Country"], y=price_comparison_gen["Base Price (€/MWh)"],
           name="Base Scenario", marker_color="lightblue")
)
fig_price_comp_gen.add_trace(
    go.Bar(x=price_comparison_gen["Country"], y=price_comparison_gen["New Price (€/MWh)"],
           name="New Scenario", marker_color="darkblue")
)
fig_price_comp_gen.update_layout(
    title="Price Comparison: Base vs New Transmission & Generation Capacity",
    barmode="group",
    xaxis_title="Country",
    yaxis_title="Price (€/MWh)",
    height=400,
)
st.plotly_chart(fig_price_comp_gen, use_container_width=True)

st.dataframe(price_comparison_gen.set_index("Country"), use_container_width=True)

# System cost comparison
base_cost_gen = (base_n.generators.marginal_cost * base_n.generators_t.p.sum()).sum()
new_cost_gen = (n_sensitivity_gen.generators.marginal_cost * n_sensitivity_gen.generators_t.p.sum()).sum()
cost_saving_gen = base_cost_gen - new_cost_gen

st.info(
    f"**System Efficiency Impact:**\n\n"
    f"- Base system cost: €{base_cost_gen:,.0f}\n\n"
    f"- New system cost: €{new_cost_gen:,.0f}\n\n"
    f"- **Cost saving: €{cost_saving_gen:,.0f} ({cost_saving_gen/base_cost_gen*100:.1f}% improvement)**\n\n"
    f"Higher transmission and generation capacity enables:\n"
    f"1. More efficient dispatch from expanded hydro capacity\n"
    f"2. Further price convergence across regions\n"
    f"3. Reduced reliance on expensive thermal generation"
)

# ============================================================================
# SECTION 6: KEY INSIGHTS & POLICY IMPLICATIONS
# ============================================================================
st.markdown("---")
st.markdown("## 📊 Key Insights & Policy Implications")

insight_cols = st.columns(2)

with insight_cols[0]:
    st.markdown("""
    ### ✅ Benefits of Grid Integration
    
    **Price Convergence:**
    - As transmission capacity increases, prices across zones converge
    - This reflects the law of one price in more integrated markets
    - Consumers benefit from access to cheaper generation
    
    **Efficiency Gains:**
    - Dispatch becomes more economically efficient
    - Least-cost generation is used first, reducing total costs
    - System operates closer to theoretical optimum
    """)

with insight_cols[1]:
    st.markdown("""
    ### ⚖️ Challenges & Trade-offs
    
    **Distributional Effects:**
    - Exporting regions: Benefit from higher demand for their generation
    - Importing regions: Benefit from lower electricity prices
    - Local producers in importing regions: May face lower prices
    
    **Infrastructure Needs:**
    - Grid expansion requires capital investment
    - Optimal zone boundaries depend on physical constraints
    - Policy decisions must balance efficiency with regional interests
    """)

st.markdown("""
### 🎯 Key Takeaways

1. **Zonal Markets Simplify Operations**: They reduce complexity but can mask network constraints
2. **Transmission is a Critical Resource**: Limited capacity creates price divergence and congestion
3. **Price Signals Matter**: Market-clearing prices reflect local scarcity and guide dispatch
4. **Investment Impacts Market Dynamics**: Grid expansion fundamentally changes price formation and flows
5. **Policy Trade-offs**: Regulators must balance efficiency gains with equity considerations

---
*This simulation demonstrates how transmission infrastructure shapes electricity market outcomes.*
*In real systems, decisions about bidding zone configuration have profound impacts on prices, investment, and welfare distribution.*
""")
