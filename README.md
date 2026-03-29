# Electricity Bidding Zones & Market Prices Simulation

An interactive Streamlit application that demonstrates how transmission infrastructure and bidding zone configuration influence electricity market prices and dispatch across interconnected electricity systems.

## Overview

This simulation explores the relationship between **transmission capacity**, **bidding zones**, and **market-clearing prices** using a simplified Southern African electricity network (South Africa, Mozambique, and Eswatini) built with [PyPSA](https://pypsa.org/).

## Key Concepts

### Zonal vs Nodal Market Representation

#### **Zonal Market Model**
In a zonal market, the transmission grid within a bidding zone is assumed to be **unconstrained**. This is often called the **"copper plate" assumption**, meaning electricity can flow freely within the zone without internal bottlenecks.

**Characteristics:**
- Only cross-border transmission constraints are explicitly modeled
- Internal congestion is not represented
- Simpler market design and operation
- Single market-clearing price per zone

#### **Nodal Market Model**
A nodal (or locational) market represents the grid at **much higher spatial resolution**. Each node reflects a physical location, and transmission constraints **within** the zone are explicitly modeled.

**Characteristics:**
- Locational Marginal Prices (LMPs) vary across nodes
- Reflects actual grid topology and congestion
- More complex but more physically accurate
- Prices vary based on network conditions

**EU Regulatory Framework:** According to EU guidelines, bidding zones should be defined to ensure efficient congestion management and overall market efficiency, ideally reflecting underlying structural congestion patterns.

### Bidding Zone Configuration: The Germany Debate

There is an ongoing policy debate about whether Germany should be split into multiple bidding zones.

#### **Potential Benefits of Multi-Zone Split:**
- **Reduced redispatch costs:** Congestion would be handled through market price signals rather than costly post-market interventions
- **Better incentives for grid investment:** Price signals reflect actual constraints
- **Improved efficiency:** More accurate reflection of physical network limitations

#### **Challenges:**
- Determining optimal zone boundaries is complex
- Price divergence across regions may introduce market uncertainty
- Investment signals may shift across regions unpredictably
- Ongoing grid expansion can change congestion patterns over time
- Political resistance from regions expecting lower prices

**Key Insight:** While technically a multi-zone system can improve efficiency, the decision is strongly influenced by **political and regulatory considerations** beyond pure economic optimization.

## Simulation Model

### How It Works

This simulation demonstrates how bidding zones influence electricity market outcomes using a simplified three-zone system:

1. **Single Zone (Baseline):** South Africa operates independently
2. **Multi-Zone (Connected):** Three countries interact through transmission links
3. **Sensitivity Analysis:** Explore how transmission capacity changes market outcomes

### Key Components

- **Bidding Zones:** South Africa, Mozambique, Eswatini (each with single market-clearing price)
- **Generation Portfolio:**
  - South Africa: Coal (€30/MWh), Gas (€60/MWh), Oil (€80/MWh), Wind (€0/MWh)
  - Mozambique: Hydro (€0/MWh)
  - Eswatini: Hydro (€0/MWh)
- **Transmission Links:** Cross-border interconnections with adjustable capacity
- **Optimization:** Least-cost dispatch using linear programming

### Electricity Dispatch Merit Order

The system follows the **merit order principle**: demand is met using the **lowest-cost generation first**, subject to network constraints.

## Simulation Insights

### Scenario 1: Congested System (Limited Transmission)

When transmission capacity is limited:

- **Price divergence:** Each zone has a different market-clearing price
- **Local dispatch drives prices:** Each zone relies on its own generation mix
- **Example outcomes:**
  - South Africa: High price (€60/MWh) due to expensive gas generation
  - Mozambique & Eswatini: Low price (€0/MWh) due to abundant cheap hydro
- **Limited power flows:** Congestion prevents cheaper electricity from being exported to high-cost regions

**Key insight:** Limited transmission creates isolated markets with different prices, reducing overall system efficiency.

### Scenario 2: Increasing Transmission Capacity

As interconnection capacity increases:

- **More power flows between zones:** Cheaper generation (hydro) can be exported
- **Price convergence:** Prices begin to align across zones
- **Behavior shift:** System becomes increasingly integrated
- **Dispatch optimization:** Cheap hydro is dispatched first, replacing expensive thermal generation

#### **Two possible outcomes:**

1. **Full capacity relief:** Transmission removes the marginal constraint
   - Prices converge to marginal cost of cheapest available generation (€0/MWh from hydro)
   - Complete system integration

2. **Partial congestion:** Transmission still constrains some flows
   - Price gaps narrow but remain positive
   - Partial integration benefits

**Critical finding:** Price convergence depends entirely on whether transmission capacity is sufficient to remove the binding constraint in each zone.

## Welfare Effects & Policy Implications

### Overall Impact: Lower Costs, Uneven Benefits

Increasing transmission capacity generally leads to:

✅ **System-level benefits:**
- Lower total system costs (more efficient dispatch)
- Higher overall social welfare
- Reduced reliance on expensive generation

⚖️ **Distributional effects (winners and losers):**
- **Consumers in importing regions:** Benefit from lower electricity prices
- **Producers in exporting regions:** Benefit from increased demand for their generation
- **Producers in importing regions:** Face lower prices, reducing revenue
- **Capital investments:** Required for grid expansion

### Policy Trade-offs

While grid expansion and market integration improve **overall efficiency**, they create **distributional effects** that are often **central to policy debates**:

- **Equity concerns:** Not all regions benefit equally
- **Regional balance:** Exporting regions gain power export revenue
- **Investment climate:** Affects incentives for local generation investments
- **Cost allocation:** Who pays for grid infrastructure?

**Important consideration:** Grid expansion costs must be compared against efficiency gains in a full cost-benefit analysis.

## How to Use This App

1. **Part 1: Scenario Comparison**
   - Compare single-zone vs multi-zone systems
   - Observe price differences and generation dispatch
   - See power flows and congestion indicators

2. **Part 2: Transmission Sensitivity**
   - Adjust transmission capacity using sliders
   - Watch prices and flows update in real-time
   - Understand how infrastructure investment affects market outcomes

## Installation & Setup

### Prerequisites
- Python 3.9+
- `uv` package manager

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd DS_ESM

# Install dependencies
uv sync

# Run the app
streamlit run app.py
```

## Technology Stack

- **[Streamlit](https://streamlit.io/)** - Interactive web app framework
- **[PyPSA](https://pypsa.org/)** - Power System Analysis (optimization & modeling)
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation
- **[Plotly](https://plotly.com/)** - Interactive visualizations
- **[uv](https://astral.sh/blog/uv/)** - Fast Python package manager

## Project Structure

```
DS_ESM/
├── app.py                    # Main Streamlit application
├── electricity_markets.py    # PyPSA network simulations
├── pyproject.toml           # Project dependencies (uv)
├── uv.lock                  # Dependency lock file
└── README.md                # This file
```

## References & Further Reading

### Bidding Zones & Market Design
- [ENTSOE Bidding Zone Review (BZR)](https://www.entsoe.eu/network_codes/bzr/#what-is-bidding-zone-review-bzr)
- [Internal Electricity Market Glossary - Bidding Zone](https://emissions-euets.com/internal-electricity-market-glossary/375-bidding-zone)

### German Bidding Zone Debate
- [Regional Electricity Bidding Zones in Germany: Grid Relief or Price Trap?](https://www.erneuerbare-energien-hamburg.de/en/news/details/regional-electricity-bidding-zones-in-germany-grid-relief-or-price-trap.html)

### Technical Documentation
- [PyPSA Documentation](https://docs.pypsa.org/latest/)

## Disclaimer

This is a **simplified toy model** for educational purposes. Real electricity markets are far more complex and include:
- Multiple time periods and contingency analysis
- Reserve margins and frequency stability requirements
- Reactive power and voltage constraints
- Detailed transmission network topology
- Ancillary services and balancing markets
- Ramping constraints and unit commitment
- Regulatory and political considerations

Use this simulation to understand **fundamental concepts** about zonal markets and transmission constraints, not for policy recommendations.

## Author

Created for educational demonstration of electricity market economics and grid optimization.

---

**Questions or feedback?** Feel free to open an issue.
