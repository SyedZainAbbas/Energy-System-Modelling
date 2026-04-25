import streamlit as st
import pandas as pd
from src.negative_prices import negative_prices_dispatch

# ============================================================================
# PAGE HEADER
# ============================================================================


st.title("📉 Negative Electricity Prices")


def generate_summary(n):
    summary = pd.DataFrame(
        {
            "Load (MW)": n.loads_t.p_set["load"].values,
            "Base Gen (MW)": n.generators_t.p["base"].values,
            "Peak Gen (MW)": n.generators_t.p["peak"].values,
            "Base Status": n.generators_t.status["base"].values,
            "Peak Status": n.generators_t.status["peak"].values,
            "Price (€/MWh)": n.buses_t.marginal_price["bus"].values,
        }
    )
    summary.index.name = "Time Period"
    return summary


# ============================================================================
# SECTION 1: INTRODUCTION
# ============================================================================
st.markdown("""
### Understanding Negative Electricity Prices

Negative electricity prices occur when generators are willing to pay to remain online rather than shut down and restart later. 
This behavior is primarily driven by conventional baseload power plants, which face significant startup, shutdown, and minimum load constraints. 
Temporarily accepting negative prices can be economically preferable to cycling operations.

**Why do negative prices emerge?**

The phenomenon stems from two key factors:

1. **Growing renewable penetration**: Wind and solar generators have near-zero marginal costs and are often incentivized to produce whenever available, 
   leading to periods of excess supply.

2. **Limited system flexibility**: Conventional generators with high startup/shutdown costs and minimum output constraints cannot quickly adjust to 
   changing demand.

Negative prices typically occur during:
- High renewable generation (strong wind or solar output)
- Low electricity demand (nights, weekends, holidays)
- Limited ramping flexibility in the system
""")

# ============================================================================
# SECTION 2: MODEL SETUP
# ============================================================================
st.markdown("---")
st.markdown("## Case Study: Simple Two-Generator System")

st.markdown("""
To illustrate how negative prices emerge, we model a simplified power system with two generators facing the load profile below. 
The difference between **linearized** and **binary** unit commitment formulations reveals how market prices are interpreted.
""")
if "n_linearized" not in st.session_state:
    st.session_state.n_linearized = negative_prices_dispatch(luc=True)
if "n_binary" not in st.session_state:
    st.session_state.n_binary = negative_prices_dispatch(luc=False)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Generator Characteristics**")
    generator_data = st.session_state.n_linearized.generators[["marginal_cost",
                                                               "p_nom", "p_min_pu", "start_up_cost", "shut_down_cost"]]
    st.dataframe(generator_data, width="stretch")
with col2:
    st.markdown("**Demand Profile**")
    load_data = st.session_state.n_linearized.loads_t.p_set.T
    st.dataframe(load_data, width="stretch")

st.info(
    "**Setup Note:** The base generator has high startup/shutdown costs and minimum output constraints (40% of capacity). "
    "The peak generator is more flexible but expensive (€70/MWh). Watch how these constraints interact during low-demand periods."
)

# ============================================================================
# SECTION 3: UNIT COMMITMENT FORMULATIONS
# ============================================================================
st.markdown("---")
st.markdown("## Comparing Formulations: Linearized vs Binary")

st.markdown("""
PyPSA offers two unit commitment approaches with different economic interpretations:

- **Binary UC (MILP)**: Generators are strictly ON or OFF. This creates a non-convex problem where marginal prices are not economically meaningful.
- **Linearized UC (Relaxed LP)**: Generator commitment levels are continuous (0–1), creating a convex problem. Marginal prices become interpretable and 
  may appear negative during periods where partial shutdown is economically preferable to full cycling.
""")
linearized_mode = st.toggle("Show Linearized Unit Commitment", value=True)
if linearized_mode:
    st.markdown("### Linearized Unit Commitment (Relaxed LP)")
    summary_linearized = generate_summary(st.session_state.n_linearized)
    st.dataframe(summary_linearized, width="stretch")
    st.markdown("""
    **Key Observation:** In the linearized formulation, generators can take fractional ON/OFF levels (0 < status < 1). This relaxation smooths 
    start-ups, shut-downs, and ramping. **Negative marginal prices appear during low-demand periods** because the model can partially represent 
    the cost of avoiding a full cycling event. Notice how the base generator fractionally operates near minimum load to avoid costly restart.
    """)
else:
    st.markdown("### Binary Unit Commitment (MILP)")
    summary_binary = generate_summary(st.session_state.n_binary)
    st.dataframe(summary_binary, width="stretch")
    st.markdown("""
    **Key Observation:** In the binary formulation, generators are strictly ON or OFF (status ∈ {0, 1}). Start-ups, shut-downs, and minimum 
    output constraints are enforced exactly. The problem is non-convex, so **marginal prices reported by the solver are not directly interpretable** 
    as economic locational marginal prices.
    """)

# ============================================================================
# SECTION 4: KEY TAKEAWAYS
# ============================================================================
st.markdown("---")
st.markdown("## Key Takeaways")

st.markdown("""
1. **Negative prices emerge from flexibility constraints**: When generators have high startup/shutdown costs and must operate above minimum levels, 
   they are willing to accept negative prices rather than cycle repeatedly.

2. **Formulation matters for price interpretation**: Linearized unit commitment produces economically interpretable prices, while binary formulation 
   does not.

3. **Renewable integration drives the phenomenon**: Growing wind and solar capacity creates periods of supply surplus. Without adequate flexibility 
   from conventional plants or demand-side response, negative prices incentivize demand response or renewable curtailment.

4. **System flexibility is the solution**: Faster ramping capabilities, battery storage, flexible demand, or interconnections to neighboring regions 
   can reduce negative price events by allowing the system to balance supply and demand more efficiently.

5. **Economic signals matter**: Negative prices send a valuable market signal: the system has too much generation at this moment. Real-world market 
   designs should preserve these signals to encourage flexibility investment and usage.
""")
