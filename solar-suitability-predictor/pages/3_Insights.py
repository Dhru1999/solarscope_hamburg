import os

import pandas as pd
import streamlit as st

# WHY this page?: the guide's "Insights" page - quick answers to the questions
# people actually ask: which districts lead, and how much of the potential is
# already "suitable"?

HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "..", "assets")

st.title("📊 Insights from the Gold table")

# USE: same small export of the Gold table as the other pages (one source of truth)
districts = pd.read_csv(os.path.join(ASSETS, "solar_districts.csv"))

# --- insight 1: how much of the total potential is in the top districts? -------
total = districts["total_power_mwp"].sum()
suitable = districts["suitable_power_mwp"].sum()
top10_share = districts.nlargest(10, "total_power_mwp")["total_power_mwp"].sum() / total

col1, col2, col3 = st.columns(3)
col1.metric("Suitable share of potential", f"{suitable / total:.0%}")
col2.metric("Suitable roof faces", f"{districts['suitable_roofs'].sum():,}")
col3.metric("Share in top 10 districts", f"{top10_share:.0%}")

st.divider()

# --- insight 2: the ranking as a chart ----------------------------------------
# USE: st.bar_chart is Streamlit's built-in chart - no plotting library needed.
# The index becomes the x-axis labels, the chosen column the bar heights.
st.subheader("Top 15 districts by potential peak power (MWp)")
top15 = districts.nlargest(15, "total_power_mwp").set_index("stadtteil")
st.bar_chart(top15["total_power_mwp"], horizontal=True)

st.divider()

# --- insight 3: suitable vs total - is the potential already tapped? -------------
# WHY compare these?: "total" is everything physics allows; "suitable" (classes 1-3)
# is what makes economic sense. The gap shows where planning effort would pay off.
st.subheader("Suitable vs total potential (top 10 districts)")
compare = (
    districts.nlargest(10, "total_power_mwp")
    .set_index("stadtteil")[["total_power_mwp", "suitable_power_mwp"]]
)
st.bar_chart(compare, horizontal=True)
st.caption("Suitable = suitability classes 1-3 only (Eignung 1, 2 and 3).")

st.divider()

# --- insight 4: which districts have the highest share of suitable roofs? -------
# WHY a *share* and not a count?: big districts naturally have many roofs; the
# share answers "where is it worth starting?".
st.subheader("Districts with the highest share of suitable roofs")
districts["suitable_share"] = districts["suitable_roofs"] / districts["roofs"]
best = (
    districts.nlargest(10, "suitable_share")
    [["stadtteil", "suitable_share", "suitable_roofs"]]
    .set_index("stadtteil")
)
st.bar_chart(best["suitable_share"])
st.caption("Share of roof faces with suitability class 1-3.")

st.divider()

st.subheader("The full numbers")
st.dataframe(districts.drop(columns=["lat", "lon", "suitable_share"]),
              use_container_width=True, hide_index=True)
