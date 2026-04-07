import streamlit as st

st.set_page_config(
    page_title="Energy System Modeling",
    page_icon="⚡",
    initial_sidebar_state="expanded",
    layout="wide"
    )

bidding_zone_page = st.Page("views/bidding_zone.py", title="Electricity Bidding Zones")
economic_dispatch_page = st.Page("views/economic_dispatch.py", title="Economic Dispatch")

pg = st.navigation(
    [bidding_zone_page, economic_dispatch_page]
)   

pg.run()



