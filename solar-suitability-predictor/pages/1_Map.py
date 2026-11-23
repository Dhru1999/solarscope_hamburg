import os

import pandas as pd
import streamlit as st

# WHY this page?: show where Hamburg's solar potential is - the guide calls this
# the "map" page. A map is the fastest way to explain the whole project to anyone.

# NEED: build file paths relative to THIS file, so the app works no matter from
# which folder it is started. __file__ is .../pages/1_Map.py, so ".." is the app root.
HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "..", "assets")

st.title("🗺️ Solar potential by district")

# USE: read the small Gold-table export (103 rows). Why a small CSV and not a
# live Databricks connection? The guide says the app must run from small exported
# files (assets/), so the same code later works on Streamlit Community Cloud too.
districts = pd.read_csv(os.path.join(ASSETS, "solar_districts.csv"))

# --- three headline numbers, one per metric card -----------------------------
total_power = districts["total_power_mwp"].sum()          # everything, all roofs
suitable_power = districts["suitable_power_mwp"].sum()   # only classes 1-3
roof_count = int(districts["roofs"].sum())

col1, col2, col3 = st.columns(3)
col1.metric("Total potential", f"{total_power:,.0f} MWp")
col2.metric("Suitable potential (Eignung 1-3)", f"{suitable_power:,.0f} MWp")
col3.metric("Roof faces analysed", f"{roof_count:,}")

st.divider()

# --- the map -----------------------------------------------------------------
# USE: st.map is Streamlit's built-in map - no API key, no extra library needed.
# Each bubble sits on the district's centre point; the bubble SIZE shows the
# potential peak power (MWp). Bigger bubble = more solar potential.
st.subheader("Potential by district (bubble size = potential peak power)")
st.map(districts, latitude="lat", longitude="lon", size="total_power_mwp")
st.caption(
    "Each bubble marks the centre of a district. In the laptop/Community Cloud "
    "version this can be upgraded to a filled choropleth map using districts.geojson."
)

st.divider()

# --- ranking table -----------------------------------------------------------
# USE: a sorted table so numbers can be checked exactly (a map shows trends, a
# table shows facts). Sorted by total power - the guide's "ranking" view.
st.subheader("District ranking")
ranking = districts[[
    "stadtteil", "roofs", "total_power_mwp", "suitable_power_mwp", "suitable_roofs", "total_pv_area_m2"
]].rename(columns={
    "stadtteil": "District", "roofs": "Roof faces",
    "total_power_mwp": "Total power (MWp)", "suitable_power_mwp": "Suitable power (MWp)",
    "suitable_roofs": "Suitable roofs", "total_pv_area_m2": "PV area (m²)",
})
st.dataframe(ranking, use_container_width=True, hide_index=True)
