import os

import mlflow
import pandas as pd
import streamlit as st

# WHY this page?: the guide's "My roof" calculator - a homeowner enters what
# they know about their roof, the ML model predicts the suitability class, and
# simple rules of thumb turn that into yearly kWh, savings and CO2 avoided.

HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "..", "assets")

# WHY version 2?: v2 was trained WITHOUT the radiation columns (they leaked the
# answer - see Home.py) and tested on districts the model had never seen.
MODEL_URI = "models:/workspace.default.solar_suitability_model/2"


# NEED: loading the model takes a few seconds. @st.cache_resource keeps it in
# memory, so it is loaded once - not again on every button click.
@st.cache_resource(show_spinner="Loading the model from Unity Catalog ...")
def load_model():
    # NEED: tell MLflow to use the UNITY CATALOG registry ("databricks-uc").
    # Without this line MLflow searches the old workspace registry, where our
    # model does not exist - and reports "Registered Model ... not found"
    # even though the model is safely registered in Unity Catalog.
    mlflow.set_registry_uri("databricks-uc")
    return mlflow.pyfunc.load_model(MODEL_URI)


# readable labels for the predicted class number (same wording as the source data)
CLASS_LABELS = {
    1: "Eignung 1 - very suitable (very high irradiation)",
    2: "Eignung 2 - highly suitable (high irradiation)",
    3: "Eignung 3 - suitable (medium irradiation)",
    6: "Eignung 6 - marginal (low irradiation / needs on-site check)",
}

st.title("🏠 My roof - is it worth it?")
st.write(
    "Enter what you know about your roof. The model predicts the official "
    "suitability class; the calculator gives a rough estimate of the yearly benefit."
)

# district names come from the same small asset file as the map page
# (one source of truth - no second list to keep up to date)
district_names = sorted(pd.read_csv(os.path.join(ASSETS, "solar_districts.csv"))["stadtteil"])

# --- step 1: the inputs (only what a roof owner knows beforehand) -------------
left, right = st.columns(2)
with left:
    area = st.number_input("Usable roof area (m²)", 1.0, 5000.0, 100.0, 1.0)
    aspect = st.slider("Direction the roof faces (°) - 0 = N, 90 = E, 180 = S, 270 = W", 0.0, 360.0, 180.0, 1.0)
    slope = st.slider("Roof tilt (°) - 0 = flat", 0.0, 90.0, 35.0, 0.5)
with right:
    schatten = st.slider("Shading - trees, chimneys, other buildings (%)", 0.0, 100.0, 0.0, 1.0)
    aufstd = st.selectbox(
        "Roof type",
        [0, 1],
        format_func=lambda v: "pitched roof (panels lie on the tiles)" if v == 0
        else "flat roof (panels on racks / Aufständerung)",
    )
    stadtteil = st.selectbox("District (Stadtteil)", district_names)

# --- step 2: predict the suitability class ------------------------------------
# WHY session_state?: Streamlit reruns this whole script on EVERY input change.
# Storing the result means the prediction survives moving the price slider below
# (it used to vanish until "Check my roof" was clicked again).
if st.button("Check my roof", type="primary", use_container_width=True):
    # the model expects a DataFrame with EXACTLY the training columns
    input_df = pd.DataFrame(
        [{"area": area, "aspect": aspect, "aufstd": aufstd,
          "slope": slope, "schatten": schatten, "stadtteil": stadtteil}]
    )
    try:
        prediction = int(load_model().predict(input_df)[0])
    except Exception as e:  # e.g. Databricks access problem - show a clear message, not a crash
        st.error(f"Could not load or run the model: {e}")
        st.stop()
    # remember the prediction AND the roof inputs it belongs to
    st.session_state["prediction"] = prediction
    st.session_state["roof"] = dict(
        area=area, aspect=aspect, aufstd=aufstd,
        slope=slope, schatten=schatten, stadtteil=stadtteil,
    )

# WHY outside the button block?: this reruns on every slider move, so the
# savings update live when the electricity price changes - without losing the
# prediction.
if "prediction" in st.session_state:
    prediction = st.session_state["prediction"]
    roof = st.session_state["roof"]

    st.success(f"Predicted suitability: **{CLASS_LABELS.get(prediction, prediction)}**")

    # --- step 3: the rule-of-thumb calculator ----------------------------------
    # WHY rules of thumb?: a real yield calculation needs an engineer and shading
    # measurements. These three constants give a good, honest rough estimate.
    # WHY roof[...]?: the estimate must stay tied to the roof the prediction was
    # made for, even if an input field is changed afterwards.
    M2_PER_KWP = 6.0     # about 6 m² of roof per installed kWp (typical module + spacing)
    KWH_PER_KWP = 950.0  # a kWp of panels in Hamburg produces roughly 950 kWh per year
    CO2_KG_PER_KWH = 0.4  # German electricity mix: ~0.4 kg CO2 per kWh produced

    kwp = roof["area"] / M2_PER_KWP            # possible peak power on this roof
    kwh_per_year = kwp * KWH_PER_KWP           # rough yearly production
    price = st.slider("Your electricity price (€ per kWh)", 0.10, 0.60, 0.35, 0.01)
    savings = kwh_per_year * price             # money not paid to the utility
    co2_tons = kwh_per_year * CO2_KG_PER_KWH / 1000  # CO2 avoided vs. grid power

    c1, c2, c3 = st.columns(3)
    c1.metric("Possible peak power", f"{kwp:.1f} kWp")
    c2.metric("Yearly production (est.)", f"{kwh_per_year:,.0f} kWh")
    c3.metric("CO2 avoided per year (est.)", f"{co2_tons:.1f} t")
    st.metric("Yearly savings (est.)", f"€ {savings:,.0f}")

    st.caption(
        "Rough estimates only - a real offer needs an on-site inspection. "
        "The prediction uses only size, direction, tilt, shading and roof type, "
        "and reflects the values entered when you clicked \"Check my roof\"."
    )
