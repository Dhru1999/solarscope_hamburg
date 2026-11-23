import streamlit as st

# WHY this file?: Streamlit "multipage apps" need one entry file (Home.py).
# Every file inside the pages/ folder then automatically becomes a page in the
# sidebar - no routing code needed.
# NEED: set_page_config must be the FIRST st command - it sets the browser tab title.
st.set_page_config(page_title="SolarScope Hamburg", page_icon="☀️", layout="wide")

st.title("☀️ SolarScope Hamburg")
st.caption("Which roofs in Hamburg should get solar panels first?")

st.markdown(
    """
This app answers three questions:

1. **🗺️ Map** - where in Hamburg is the solar potential? (district map + ranking)
2. **🏠 My roof** - is *my* roof suitable, and what would it produce?
   (a small calculator using the ML model)
3. **📊 Insights** - which districts stand out, and what does the data say?

The app is the last step of the SolarScope Hamburg pipeline:
"""
)

st.subheader("How the data got here (the medallion architecture)")
st.markdown(
    """
| Layer | Table | What it contains |
| --- | --- | --- |
| 🥉 Bronze | `solar_raw_csv` | the raw CSV upload, exactly as delivered |
| 🥈 Silver | `solar_roofs_with_district` | cleaned roof faces + their Hamburg district |
| 🥇 Gold | `solar_gold` | one summary row per district (power, area, counts) |
| 📦 Assets | `assets/solar_districts.csv` | a *small* export of the Gold table for this app |

**Why layers?** If a cleaning mistake is found later, only the affected layer
is rebuilt - the raw data is never lost.
"""
)

st.subheader("The ML model behind \"My roof\"")
st.markdown(
    """
- A **Random Forest classifier** trained on **864,358** Hamburg roof faces.
- Predicts the suitability class (Eignung 1 / 2 / 3 / 6) from features a roof
  owner knows beforehand: **size, direction, tilt, shading, roof type and district**.
- **Deliberately NOT used:** radiation columns - they are computed *from* the
  same analysis that assigns the class, so using them would leak the answer
  (like revising with the answer sheet on the desk).
- Tested on **21 districts the model never saw**: 88% accuracy, 0.86 macro F1.
- Tracked with **MLflow** and registered in **Unity Catalog** as
  `workspace.default.solar_suitability_model` version 2.
"""
)

st.info("Start with the **Map** page in the sidebar to explore the city, then try **My roof**.")
